"""借用模块视图（接口 3.1 - 5.4，责任人 B）

接口清单：
3.1 POST /api/borrow/apply                     提交借用申请
3.2 GET  /api/borrow/my/list                   我的申请列表
3.3 PUT  /api/borrow/cancel/{recordId}         取消待审批申请
3.4 GET  /api/admin/borrow/pendingList         待审批列表
3.5 PUT  /api/admin/borrow/audit/{recordId}    审批（事务）
3.6 GET  /api/admin/borrow/allList             全部借用记录总览
4.1 PUT  /api/borrow/returnApply/{recordId}    发起归还
4.2 GET  /api/admin/borrow/waitReturnList      待归还列表
4.3 PUT  /api/admin/borrow/confirmReturn/{recordId}  确认归还（事务）
5.1 GET  /api/admin/statistics/equipment       设备借用统计
5.2 GET  /api/admin/statistics/user            用户借用统计
5.4 GET  /api/admin/export/borrowRecord        导出借用记录 Excel
"""
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.borrow.models import BorrowRecord
from apps.borrow.serializers import (
    BorrowApplySerializer,
    BorrowAuditSerializer,
    BorrowRecordOutSerializer,
    ReturnConfirmSerializer,
)
from apps.borrow.services import compute_return_overdue_status, refresh_overdue_status
from apps.common.constants import (
    ApprovalStatus,
    AuditResult,
    EquipmentStatus,
    LogModule,
    OverdueStatus,
    ReturnType,
    UserStatus,
)
from apps.common.exceptions import BadRequestError, NotFoundError
from apps.common.pagination import PageNumberPagination
from apps.common.permissions import IsAdmin
from apps.common.response import Result
from apps.common.utils import write_excel_sheet
from apps.equipment.models import Equipment
from apps.log.decorators import log_operation
from apps.user.models import User

# 确认归还类型 -> 设备状态 映射
_RETURN_TYPE_EQUIPMENT_STATUS = {
    ReturnType.NORMAL: EquipmentStatus.IDLE,
    ReturnType.DAMAGE: EquipmentStatus.REPAIRING,
    ReturnType.LOSE: EquipmentStatus.SCRAPPED,
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


def _paginate(request, queryset, serializer_cls):
    """统一分页，返回 {total, pages, current, records} 结构"""
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(serializer_cls(page, many=True).data)


def _get_borrow_record_or_404(pk, user=None):
    """按主键取借用记录；传 user 时同时校验归属（避免泄露他人记录是否存在）"""
    qs = BorrowRecord.objects.filter(pk=pk)
    if user is not None:
        qs = qs.filter(user=user)
    record = qs.first()
    if record is None:
        raise NotFoundError("借用记录不存在")
    return record


# ===================== 3.1 提交借用申请 =====================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_operation(module=LogModule.BORROW, action="提交借用申请")
def borrow_apply(request):
    ser = BorrowApplySerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    # ① 申请人状态校验
    if request.user.status == UserStatus.DISABLED:
        raise BadRequestError("账号已被禁用，无法提交借用申请")

    # ② 设备存在且闲置
    equipment = Equipment.objects.filter(pk=data["equipmentId"], is_deleted=False).first()
    if equipment is None:
        raise BadRequestError("设备不存在")
    if equipment.status != EquipmentStatus.IDLE:
        raise BadRequestError("该设备当前不是闲置状态，无法借用")

    # ④ 当前用户存在逾期未归还记录则拒绝
    now = timezone.now()
    if BorrowRecord.objects.filter(
        user=request.user,
        approval_status=ApprovalStatus.PASSED,
        actual_return_time__isnull=True,
        plan_return_time__lt=now,
    ).exists():
        raise BadRequestError("存在逾期未还记录，禁止再次申请")

    # ⑤ 同一设备在目标时间段内已通过借出则冲突
    if BorrowRecord.objects.filter(
        equipment=equipment,
        approval_status=ApprovalStatus.PASSED,
        actual_return_time__isnull=True,
        plan_borrow_start__lt=data["planReturnTime"],
        plan_return_time__gt=data["planBorrowStart"],
    ).exists():
        raise BadRequestError("该设备在所选时间段已被借出，请调整借用时间")

    record = BorrowRecord.objects.create(
        user=request.user,
        equipment=equipment,
        plan_borrow_start=data["planBorrowStart"],
        plan_return_time=data["planReturnTime"],
        borrow_purpose=data.get("borrowPurpose", ""),
        remark=data.get("remark", ""),
    )
    return Result.to_response(Result.success({"recordId": record.id}, "借用申请提交成功"))


# ===================== 3.2 我的申请列表 =====================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def borrow_my_list(request):
    approval_status = (request.query_params.get("approvalStatus") or "").strip()
    qs = BorrowRecord.objects.filter(user=request.user)
    if approval_status:
        qs = qs.filter(approval_status=approval_status)
    qs = qs.order_by("-id")
    return _paginate(request, qs, BorrowRecordOutSerializer)


# ===================== 3.3 取消待审批申请 =====================

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@log_operation(module=LogModule.BORROW, action="取消借用申请")
def borrow_cancel(request, recordId):
    record = _get_borrow_record_or_404(recordId, user=request.user)
    if record.approval_status != ApprovalStatus.PENDING:
        raise BadRequestError("仅待审批的申请可取消")
    record.approval_status = ApprovalStatus.CANCELED
    record.cancel_time = timezone.now()
    record.save(update_fields=["approval_status", "cancel_time", "update_time"])
    return Result.to_response(Result.success(msg="借用申请已取消"))


# ===================== 3.4 待审批列表 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def borrow_pending_list(request):
    qs = BorrowRecord.objects.filter(approval_status=ApprovalStatus.PENDING).order_by("id")
    return _paginate(request, qs, BorrowRecordOutSerializer)


# ===================== 3.5 审批（事务） =====================

@api_view(["PUT"])
@permission_classes([IsAdmin])
@log_operation(module=LogModule.BORROW, action="审批借用申请")
def borrow_audit(request, recordId):
    ser = BorrowAuditSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    record = _get_borrow_record_or_404(recordId)
    if record.approval_status != ApprovalStatus.PENDING:
        raise BadRequestError("该申请已审批，禁止重复审批")

    with transaction.atomic():
        record.approval_comment = data.get("approvalComment", "")
        record.auditor = request.user
        record.audit_time = timezone.now()
        if data["auditResult"] == AuditResult.PASS:
            record.approval_status = ApprovalStatus.PASSED
            record.save()
            # 事务内同步设备状态为借出中
            Equipment.objects.filter(pk=record.equipment_id).update(status=EquipmentStatus.BORROWED)
        else:
            record.approval_status = ApprovalStatus.REJECTED
            record.save()

    return Result.to_response(
        Result.success({"recordId": record.id, "approvalStatus": record.approval_status}, "审批完成")
    )


# ===================== 3.6 全部借用记录总览 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def borrow_all_list(request):
    refresh_overdue_status()  # G12 查询时实时计算兜底

    user_id = _parse_int_param(request, "userId")
    equipment_id = _parse_int_param(request, "equipmentId")
    overdue_status = (request.query_params.get("overdueStatus") or "").strip()
    start_time = _parse_datetime_param(request, "startTime")
    end_time = _parse_datetime_param(request, "endTime")

    qs = BorrowRecord.objects.all()
    if user_id is not None:
        qs = qs.filter(user_id=user_id)
    if equipment_id is not None:
        qs = qs.filter(equipment_id=equipment_id)
    if overdue_status:
        qs = qs.filter(overdue_status=overdue_status)
    if start_time:
        qs = qs.filter(create_time__gte=start_time)
    if end_time:
        qs = qs.filter(create_time__lte=end_time)
    qs = qs.order_by("-id")
    return _paginate(request, qs, BorrowRecordOutSerializer)


# ===================== 4.1 发起归还 =====================

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@log_operation(module=LogModule.RETURN, action="发起归还申请")
def borrow_return_apply(request, recordId):
    record = _get_borrow_record_or_404(recordId, user=request.user)
    if record.approval_status != ApprovalStatus.PASSED:
        raise BadRequestError("仅已通过（借出中）的记录可发起归还")
    if record.return_apply_time is not None:
        raise BadRequestError("已发起归还申请，不可重复提交")
    record.return_apply_time = timezone.now()
    record.save(update_fields=["return_apply_time", "update_time"])
    return Result.to_response(Result.success(msg="归还申请已提交"))


# ===================== 4.2 待归还列表 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def borrow_wait_return_list(request):
    refresh_overdue_status()  # G12 查询时实时计算兜底
    qs = BorrowRecord.objects.filter(
        approval_status=ApprovalStatus.PASSED,
        return_apply_time__isnull=False,
        actual_return_time__isnull=True,
    ).order_by("return_apply_time")
    return _paginate(request, qs, BorrowRecordOutSerializer)


# ===================== 4.3 确认归还（事务） =====================

@api_view(["PUT"])
@permission_classes([IsAdmin])
@log_operation(module=LogModule.RETURN, action="确认归还")
def borrow_confirm_return(request, recordId):
    ser = ReturnConfirmSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    record = _get_borrow_record_or_404(recordId)
    if record.approval_status != ApprovalStatus.PASSED:
        raise BadRequestError("该记录未处于借出中状态，无法确认归还")
    if record.actual_return_time is not None:
        raise BadRequestError("该记录已确认归还，禁止重复操作")

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
        Result.success({"recordId": record.id, "overdueStatus": record.overdue_status}, "归还确认完成")
    )


# ===================== 5.1 设备借用统计 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def equipment_statistics(request):
    refresh_overdue_status()  # G12 查询时实时计算兜底
    now = timezone.now()

    stats = {}
    rows = BorrowRecord.objects.filter(
        approval_status__in=[ApprovalStatus.PASSED, ApprovalStatus.RETURNED],
    ).values("equipment_id", "plan_borrow_start", "actual_return_time")
    for r in rows:
        item = stats.setdefault(r["equipment_id"], {"count": 0, "seconds": 0.0, "first_start": None})
        start = r["plan_borrow_start"]
        end = r["actual_return_time"] or now
        item["count"] += 1
        item["seconds"] += max(0.0, (end - start).total_seconds())
        if item["first_start"] is None or start < item["first_start"]:
            item["first_start"] = start

    result = []
    for eq in Equipment.objects.all():
        item = stats.get(eq.id, {"count": 0, "seconds": 0.0, "first_start": None})
        window_start = item["first_start"] or eq.create_time
        idle_seconds = max(0.0, (now - window_start).total_seconds() - item["seconds"])
        result.append(
            {
                "equipmentId": eq.id,
                "name": eq.name,
                "equipmentNo": eq.equipment_no,
                "borrowCount": item["count"],
                "totalBorrowHours": round(item["seconds"] / 3600, 2),
                "idleHours": round(idle_seconds / 3600, 2),
            }
        )
    result.sort(key=lambda x: x["borrowCount"], reverse=True)
    return Result.to_response(Result.success(result))


# ===================== 5.2 用户借用统计 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def user_statistics(request):
    refresh_overdue_status()  # G12 查询时实时计算兜底

    rows = (
        BorrowRecord.objects.values("user_id")
        .annotate(
            borrowCount=Count(
                "id",
                filter=Q(approval_status__in=[ApprovalStatus.PASSED, ApprovalStatus.RETURNED]),
            ),
            overdueCount=Count(
                "id",
                filter=Q(overdue_status__in=[OverdueStatus.OVERDUE, OverdueStatus.OVERDUE_RETURNED]),
            ),
        )
        .order_by("-borrowCount")
    )

    users = {u.id: u for u in User.objects.filter(id__in=[r["user_id"] for r in rows])}
    result = []
    for r in rows:
        u = users.get(r["user_id"])
        result.append(
            {
                "userId": r["user_id"],
                "name": u.name if u else "",
                "department": u.department if u else "",
                "borrowCount": r["borrowCount"],
                "overdueCount": r["overdueCount"],
            }
        )
    return Result.to_response(Result.success(result))


# ===================== 5.4 导出借用记录 =====================

@api_view(["GET"])
@permission_classes([IsAdmin])
def export_borrow_record(request):
    start_time = _parse_datetime_param(request, "startTime")
    end_time = _parse_datetime_param(request, "endTime")

    qs = BorrowRecord.objects.all()
    if start_time:
        qs = qs.filter(create_time__gte=start_time)
    if end_time:
        qs = qs.filter(create_time__lte=end_time)
    qs = qs.order_by("id")

    max_rows = getattr(settings, "EXPORT_MAX_ROWS", 10000)
    if qs.count() > max_rows:
        raise BadRequestError(f"导出条数超过上限 {max_rows} 条，请缩小时间范围")

    records = qs[:max_rows]
    headers = [
        "记录ID", "用户", "设备编号", "设备名称", "计划借用开始", "计划归还",
        "借用用途", "审批状态", "逾期状态", "实际归还时间", "归还类型", "创建时间",
    ]
    rows = []
    for r in records:
        rows.append(
            [
                r.id,
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
            ]
        )

    content = write_excel_sheet("借用记录", headers, rows)
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="borrowRecord.xlsx"'
    return response
