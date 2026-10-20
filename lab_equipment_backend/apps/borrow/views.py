"""借用模块视图（对齐《后端API接口文档》六、七、八章）

接口清单（仅现有接口，缺失接口不实现）：
6.1 POST /borrow-applications                       提交借用申请
6.2 GET  /borrow-applications/my                    我的申请列表
6.3 PUT  /borrow-applications/{id}/cancel           取消申请
6.4 GET  /admin/borrow-applications/pending         待审批列表
6.5 PUT  /admin/borrow-applications/{id}/approval   审批操作
6.6 GET  /admin/borrow-records                      借用记录总览
7.1 POST /return-applications                       发起归还申请
7.2 GET  /admin/return-applications/pending         待归还列表
7.3 PUT  /admin/return-applications/{id}/confirm    确认归还
8.1 GET  /admin/statistics/equipment-usage          设备使用统计
8.2 GET  /admin/statistics/user-borrow              用户借用统计
8.4 GET  /admin/borrow-records/export               导出借用记录
"""
from datetime import datetime, time as _time

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.borrow.models import BorrowRecord
from apps.borrow.serializers import (
    BorrowApplySerializer,
    BorrowApprovalSerializer,
    BorrowRecordOutSerializer,
    ReturnApplicationOutSerializer,
    ReturnApplySerializer,
    ReturnConfirmSerializer,
)
from apps.borrow.services import compute_return_overdue_status, refresh_overdue_status
from apps.common.constants import (
    ApprovalStatus,
    AuditAction,
    BizErrorCode,
    EquipmentStatus,
    OperationModule,
    OverdueStatus,
    ReturnType,
    Role,
    UserStatus,
)
from apps.common.exceptions import BadRequestError, BizException, ForbiddenError, NotFoundError
from apps.common.pagination import paginate
from apps.common.permissions import IsAdmin
from apps.common.response import Result
from apps.common.utils import write_excel_sheet
from apps.equipment.models import Equipment
from apps.log.decorators import log_operation
from apps.user.models import User

# 确认归还类型 -> 设备状态 映射
_RETURN_TYPE_EQUIPMENT_STATUS = {
    ReturnType.NORMAL: EquipmentStatus.IDLE,
    ReturnType.DAMAGED: EquipmentStatus.REPAIRING,
    ReturnType.LOST: EquipmentStatus.SCRAPPED,
}


def _parse_int_param(request, name):
    raw = (request.query_params.get(name) or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise BadRequestError(f"参数 {name} 必须为整数")


def _parse_datetime_param(request, name):
    raw = (request.query_params.get(name) or "").strip()
    if not raw:
        return None
    parsed = parse_datetime(raw)
    if parsed is None:
        raise BadRequestError(f"参数 {name} 时间格式应为 yyyy-MM-dd HH:mm:ss")
    return parsed


def _parse_date_param(request, name):
    raw = (request.query_params.get(name) or "").strip()
    if not raw:
        return None
    parsed = parse_date(raw)
    if parsed is None:
        raise BadRequestError(f"参数 {name} 时间格式应为 yyyy-MM-dd")
    return parsed


def _get_borrow_record_or_404(pk, user=None):
    """按主键取借用记录；传 user 时校验归属（他人记录返回 403）"""
    record = BorrowRecord.objects.filter(pk=pk).first()
    if record is None:
        raise NotFoundError("借用记录不存在")
    if user is not None and record.user_id != user.id:
        raise ForbiddenError("无权操作他人借用记录")
    return record


def _build_records_qs(request):
    """6.6 / 8.4 共用的借用记录筛选"""
    keyword = (request.query_params.get("keyword") or "").strip()
    equipment_id = _parse_int_param(request, "equipmentId")
    approval_status = (request.query_params.get("approvalStatus") or "").strip()
    start_time = _parse_datetime_param(request, "startTime")
    end_time = _parse_datetime_param(request, "endTime")

    qs = BorrowRecord.objects.all()
    if keyword:
        qs = qs.filter(Q(user__name__icontains=keyword) | Q(user__user_no__icontains=keyword))
    if equipment_id is not None:
        qs = qs.filter(equipment_id=equipment_id)
    if approval_status:
        qs = qs.filter(approval_status=approval_status)
    if start_time:
        qs = qs.filter(create_time__gte=start_time)
    if end_time:
        qs = qs.filter(create_time__lte=end_time)
    return qs


def _buy_date_as_dt(eq):
    """设备购置日期转 datetime（无购置日期时退回创建时间）"""
    if eq.buy_date:
        return datetime.combine(eq.buy_date, _time.min)
    return eq.create_time


# ===================== 6.1 提交借用申请 =====================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_operation(module=OperationModule.BORROW_APPLICATION, action="提交借用申请")
def borrow_apply(request):
    ser = BorrowApplySerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    # ① 申请人状态校验
    if request.user.status == UserStatus.DISABLED:
        raise BizException("账号已被禁用，无法提交借用申请", code=BizErrorCode.ACCOUNT_DISABLED)

    # ② 设备存在且闲置
    equipment = Equipment.objects.filter(pk=data["equipmentId"], is_deleted=False).first()
    if equipment is None:
        raise NotFoundError("设备不存在")
    if equipment.status != EquipmentStatus.IDLE:
        raise BizException("该设备当前不可借用", code=BizErrorCode.EQUIPMENT_NOT_AVAILABLE)

    # ③ 当前用户存在逾期未归还记录则拒绝
    now = timezone.now()
    if BorrowRecord.objects.filter(
        user=request.user,
        approval_status=ApprovalStatus.APPROVED,
        actual_return_time__isnull=True,
        plan_return_time__lt=now,
    ).exists():
        raise BizException("存在逾期未归还记录，禁止新申请", code=BizErrorCode.HAS_OVERDUE)

    # ④ 同一设备在目标时间段内已通过借出则冲突
    if BorrowRecord.objects.filter(
        equipment=equipment,
        approval_status=ApprovalStatus.APPROVED,
        actual_return_time__isnull=True,
        plan_borrow_start__lt=data["planReturnTime"],
        plan_return_time__gt=data["planBorrowStart"],
    ).exists():
        raise BizException("该设备在所选时间段已被借出，请调整借用时间", code=409)

    record = BorrowRecord.objects.create(
        user=request.user,
        equipment=equipment,
        plan_borrow_start=data["planBorrowStart"],
        plan_return_time=data["planReturnTime"],
        borrow_purpose=data.get("borrowPurpose", ""),
        remark=data.get("remark", ""),
    )
    return Result.to_response(Result.success({
        "id": record.id,
        "applicationNo": f"APP{record.id:06d}",
        "approvalStatus": record.approval_status,
        "applyTime": record.create_time.strftime("%Y-%m-%d %H:%M:%S"),
    }, "借用申请提交成功"))


# ===================== 6.2 我的申请列表 =====================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def borrow_my_list(request):
    approval_status = (request.query_params.get("approvalStatus") or "").strip()
    qs = BorrowRecord.objects.filter(user=request.user)
    if approval_status:
        qs = qs.filter(approval_status=approval_status)
    qs = qs.order_by("-id")
    return paginate(request, qs, BorrowRecordOutSerializer)


# ===================== 6.3 取消待审批申请 =====================

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@log_operation(module=OperationModule.BORROW_APPLICATION, action="取消借用申请")
def borrow_cancel(request, pk):
    record = _get_borrow_record_or_404(pk, user=request.user)
    if record.approval_status != ApprovalStatus.PENDING:
        raise BizException("申请状态不允许取消", code=BizErrorCode.CANNOT_CANCEL)
    record.approval_status = ApprovalStatus.CANCELLED
    record.cancel_time = timezone.now()
    record.save(update_fields=["approval_status", "cancel_time", "update_time"])
    return Result.to_response(Result.success(message="借用申请已取消"))


# ===================== 6.4 待审批列表 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def borrow_pending_list(request):
    qs = BorrowRecord.objects.filter(approval_status=ApprovalStatus.PENDING).order_by("id")
    return paginate(request, qs, BorrowRecordOutSerializer)


# ===================== 6.5 审批（事务） =====================

@api_view(["PUT"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.BORROW_APPROVAL, action="审批借用申请")
def borrow_audit(request, pk):
    ser = BorrowApprovalSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    record = _get_borrow_record_or_404(pk)
    if record.approval_status != ApprovalStatus.PENDING:
        raise BizException("审批已通过，不可撤回", code=BizErrorCode.ALREADY_APPROVED)

    with transaction.atomic():
        record.approval_comment = data.get("comment", "")
        record.auditor = request.user
        record.audit_time = timezone.now()
        if data["action"] == AuditAction.APPROVE:
            record.approval_status = ApprovalStatus.APPROVED
            record.save()
            Equipment.objects.filter(pk=record.equipment_id).update(status=EquipmentStatus.BORROWED)
        else:
            record.approval_status = ApprovalStatus.REJECTED
            record.save()

    return Result.to_response(
        Result.success({"id": record.id, "approvalStatus": record.approval_status}, "审批完成")
    )


# ===================== 6.6 借用记录总览 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def borrow_all_list(request):
    refresh_overdue_status()
    qs = _build_records_qs(request)
    return paginate(request, qs, BorrowRecordOutSerializer)


# ===================== 7.1 发起归还 =====================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_operation(module=OperationModule.RETURN_CONFIRM, action="发起归还申请")
def borrow_return_apply(request):
    ser = ReturnApplySerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    record_id = ser.validated_data["borrowRecordId"]

    record = _get_borrow_record_or_404(record_id, user=request.user)
    if record.approval_status != ApprovalStatus.APPROVED:
        raise BizException("借用状态不允许发起归还", code=BizErrorCode.CANNOT_RETURN)
    if record.return_apply_time is not None:
        raise BizException("归还申请已提交，请勿重复提交", code=BizErrorCode.RETURN_ALREADY_SUBMITTED)
    record.return_apply_time = timezone.now()
    record.save(update_fields=["return_apply_time", "update_time"])
    return Result.to_response(Result.success(message="归还申请已提交"))


# ===================== 7.2 待归还列表 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def borrow_wait_return_list(request):
    refresh_overdue_status()
    qs = BorrowRecord.objects.filter(
        approval_status=ApprovalStatus.APPROVED,
        return_apply_time__isnull=False,
        actual_return_time__isnull=True,
    ).order_by("return_apply_time")
    return paginate(request, qs, ReturnApplicationOutSerializer)


# ===================== 7.3 确认归还（事务） =====================

@api_view(["PUT"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.RETURN_CONFIRM, action="确认归还")
def borrow_confirm_return(request, pk):
    ser = ReturnConfirmSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    record = _get_borrow_record_or_404(pk)
    if record.approval_status != ApprovalStatus.APPROVED:
        raise BizException("该记录未处于借出中状态，无法确认归还", code=BizErrorCode.CANNOT_RETURN)
    if record.actual_return_time is not None:
        raise BizException("该记录已确认归还，禁止重复操作", code=409)

    now = timezone.now()
    overdue_status = compute_return_overdue_status(record.plan_return_time, now)
    target_status = _RETURN_TYPE_EQUIPMENT_STATUS[data["returnType"]]

    with transaction.atomic():
        record.actual_return_time = now
        record.return_type = data["returnType"]
        record.damage_desc = data.get("damageDesc", "")
        record.approval_status = ApprovalStatus.RETURNED
        record.overdue_status = overdue_status
        record.save(
            update_fields=[
                "actual_return_time", "return_type", "damage_desc",
                "approval_status", "overdue_status", "update_time",
            ]
        )
        Equipment.objects.filter(pk=record.equipment_id).update(status=target_status)

    return Result.to_response(
        Result.success({"id": record.id, "overdueStatus": record.overdue_status}, "归还确认完成")
    )


# ===================== 8.1 设备使用统计 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def equipment_statistics(request):
    refresh_overdue_status()
    now = timezone.now()

    start_time = _parse_date_param(request, "startTime")
    end_time = _parse_date_param(request, "endTime")

    qs = BorrowRecord.objects.filter(
        approval_status__in=[ApprovalStatus.APPROVED, ApprovalStatus.RETURNED],
    )
    if start_time:
        qs = qs.filter(create_time__date__gte=start_time)
    if end_time:
        qs = qs.filter(create_time__date__lte=end_time)

    stats = {}
    for r in qs.values("equipment_id", "plan_borrow_start", "actual_return_time"):
        item = stats.setdefault(r["equipment_id"], {"count": 0, "seconds": 0.0})
        end = r["actual_return_time"] or now
        item["count"] += 1
        item["seconds"] += max(0.0, (end - r["plan_borrow_start"]).total_seconds())

    result = []
    for eq in Equipment.objects.all():
        item = stats.get(eq.id, {"count": 0, "seconds": 0.0})
        elapsed_seconds = max(0.0, (now - _buy_date_as_dt(eq)).total_seconds())
        borrow_hours = round(item["seconds"] / 3600, 2)
        idle_hours = round(max(0.0, elapsed_seconds - item["seconds"]) / 3600, 2)
        utilization = round(borrow_hours / (elapsed_seconds / 3600) * 100, 2) if elapsed_seconds > 0 else 0.0
        result.append({
            "equipmentId": eq.id,
            "equipmentNo": eq.equipment_no,
            "equipmentName": eq.name,
            "totalBorrowCount": item["count"],
            "totalBorrowDuration": borrow_hours,
            "idleDuration": idle_hours,
            "utilizationRate": utilization,
        })
    result.sort(key=lambda x: x["totalBorrowCount"], reverse=True)
    return Result.to_response(Result.success(result))


# ===================== 8.2 用户借用统计 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def user_statistics(request):
    refresh_overdue_status()

    start_time = _parse_date_param(request, "startTime")
    end_time = _parse_date_param(request, "endTime")
    department = (request.query_params.get("department") or "").strip()

    users_qs = User.objects.filter(role=Role.USER)
    if department:
        users_qs = users_qs.filter(department__icontains=department)
    user_ids = list(users_qs.values_list("id", flat=True))

    qs = BorrowRecord.objects.filter(user_id__in=user_ids)
    if start_time:
        qs = qs.filter(create_time__date__gte=start_time)
    if end_time:
        qs = qs.filter(create_time__date__lte=end_time)

    rows = (
        qs.values("user_id")
        .annotate(
            totalApplyCount=Count("id"),
            approvedCount=Count("id", filter=Q(approval_status=ApprovalStatus.APPROVED)),
            rejectedCount=Count("id", filter=Q(approval_status=ApprovalStatus.REJECTED)),
            returnedCount=Count("id", filter=Q(approval_status=ApprovalStatus.RETURNED)),
            overdueCount=Count(
                "id",
                filter=Q(overdue_status__in=[OverdueStatus.OVERDUE, OverdueStatus.OVERDUE_RETURNED]),
            ),
        )
        .order_by("-totalApplyCount")
    )

    users = {u.id: u for u in users_qs}
    result = []
    for r in rows:
        u = users.get(r["user_id"])
        if u is None:
            continue
        result.append({
            "userId": r["user_id"],
            "userNo": u.user_no,
            "userName": u.name,
            "department": u.department,
            "totalApplyCount": r["totalApplyCount"],
            "approvedCount": r["approvedCount"],
            "rejectedCount": r["rejectedCount"],
            "returnedCount": r["returnedCount"],
            "overdueCount": r["overdueCount"],
        })
    return Result.to_response(Result.success(result))


# ===================== 8.4 导出借用记录 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def export_borrow_record(request):
    qs = _build_records_qs(request).order_by("id")

    max_rows = getattr(settings, "EXPORT_MAX_ROWS", 10000)
    if qs.count() > max_rows:
        raise BadRequestError(f"导出条数超过上限 {max_rows} 条，请缩小时间范围")

    records = qs[:max_rows]
    headers = [
        "记录ID", "申请单号", "用户", "设备编号", "设备名称", "计划借用开始", "计划归还",
        "借用用途", "审批状态", "逾期状态", "实际归还时间", "归还类型", "申请时间",
    ]
    rows = []
    for r in records:
        rows.append([
            r.id,
            f"APP{r.id:06d}",
            r.user.name if r.user_id else "",
            r.equipment.equipment_no if r.equipment_id else "",
            r.equipment.name if r.equipment_id else "",
            r.plan_borrow_start.strftime("%Y-%m-%d %H:%M:%S"),
            r.plan_return_time.strftime("%Y-%m-%d %H:%M:%S"),
            r.borrow_purpose,
            r.approval_status,
            r.overdue_status,
            r.actual_return_time.strftime("%Y-%m-%d %H:%M:%S") if r.actual_return_time else "",
            r.return_type or "",
            r.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    content = write_excel_sheet("借用记录", headers, rows)
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="borrowRecords.xlsx"'
    return response
