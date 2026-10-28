"""设备管理/浏览模块视图（对齐《后端API接口文档》四、五章，责任人 A）

接口清单：
4.1 POST   /admin/equipment          管理员-新增设备
4.2 PUT    /admin/equipment/{id}     管理员-编辑设备
4.3 DELETE /admin/equipment/{id}     管理员-逻辑删除设备
4.4 GET    /admin/equipment          管理员-设备列表
4.5 GET    /admin/equipment/{id}     管理员-设备详情
4.6 POST   /admin/equipment/import   管理员-批量导入设备
4.7 GET    /admin/equipment/export   管理员-导出设备台账
4.8 POST   /upload/image             设备图片上传
5.1 GET    /equipment                设备列表（公开浏览）
5.2 GET    /equipment/{id}           设备详情（公开）
"""
import uuid
from pathlib import Path

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.common.constants import BizErrorCode, EquipmentStatus, OperationModule
from apps.common.exceptions import BizException, NotFoundError
from apps.common.pagination import paginate
from apps.common.permissions import IsAdmin
from apps.common.response import Result
from apps.common.utils import read_excel_sheet, write_excel_sheet
from apps.equipment.models import Equipment
from apps.equipment.serializers import (
    EquipmentAddSerializer,
    EquipmentAdminDetailSerializer,
    EquipmentAdminSerializer,
    EquipmentBrowseDetailSerializer,
    EquipmentBrowseSerializer,
    EquipmentUpdateSerializer,
)
from apps.log.decorators import log_operation


def _get_equipment_or_404(pk) -> Equipment:
    equipment = Equipment.objects.filter(pk=pk).first()
    if equipment is None:
        raise NotFoundError("设备不存在")
    return equipment


def _truthy(value: str) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes")


def _admin_filtered_qs(request):
    """4.4 管理端列表/导出共用筛选：keyword(名称/编号)、status、location、showDeleted"""
    keyword = (request.query_params.get("keyword") or "").strip()
    status = (request.query_params.get("status") or "").strip()
    location = (request.query_params.get("location") or "").strip()
    show_deleted = _truthy(request.query_params.get("showDeleted"))

    qs = Equipment.objects.all().order_by("-id")
    if not show_deleted:
        qs = qs.filter(is_deleted=False)
    if keyword:
        qs = qs.filter(Q(name__icontains=keyword) | Q(equipment_no__icontains=keyword))
    if status:
        qs = qs.filter(status=status)
    if location:
        qs = qs.filter(location__icontains=location)
    return qs


# ================= 5.1 设备列表（公开浏览） =================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def equipment_browse_list(request):
    """5.1 登录用户浏览设备；不展示已逻辑删除的设备"""
    keyword = (request.query_params.get("keyword") or "").strip()
    status = (request.query_params.get("status") or "").strip()
    location = (request.query_params.get("location") or "").strip()
    only_available = _truthy(request.query_params.get("onlyAvailable"))

    qs = Equipment.objects.filter(is_deleted=False).order_by("-id")
    if keyword:
        qs = qs.filter(name__icontains=keyword)
    if status:
        qs = qs.filter(status=status)
    if location:
        qs = qs.filter(location__icontains=location)
    if only_available:
        qs = qs.filter(status=EquipmentStatus.IDLE)

    return paginate(request, qs, EquipmentBrowseSerializer)


# ================= 5.2 设备详情（公开） =================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def equipment_browse_detail(request, pk):
    """5.2 完整参数 + 历史借用记录；已逻辑删除的设备对浏览端不可见"""
    equipment = Equipment.objects.filter(pk=pk).first()
    if equipment is None or equipment.is_deleted:
        raise NotFoundError("设备不存在")
    return Result.to_response(
        Result.success(EquipmentBrowseDetailSerializer(equipment).data)
    )


# ================= 4.4 管理员设备列表 =================

@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_equipment_list(request):
    """4.4 管理员查询全部设备，showDeleted=true 时含已逻辑删除"""
    return paginate(request, _admin_filtered_qs(request), EquipmentAdminSerializer)


# ================= 4.5 管理员设备详情 =================

@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_equipment_detail(request, pk):
    """4.5 管理员查看设备详情（含已逻辑删除），附历史借用记录"""
    equipment = _get_equipment_or_404(pk)
    return Result.to_response(
        Result.success(EquipmentAdminDetailSerializer(equipment).data)
    )


# ================= 4.1 管理员新增设备 =================

@api_view(["POST"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.EQUIPMENT_MANAGEMENT, action="新增设备")
def equipment_add(request):
    """4.1 equipmentNo 全局唯一，重复返回 2004"""
    ser = EquipmentAddSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    if Equipment.objects.filter(equipment_no=ser.validated_data["equipment_no"]).exists():
        raise BizException("设备编号已存在", code=BizErrorCode.EQUIPMENT_NO_EXISTS)

    equipment = Equipment.objects.create(**ser.validated_data)
    return Result.to_response(Result.success(EquipmentAdminSerializer(equipment).data))


# ================= 4.2 管理员编辑设备 =================

@api_view(["PUT"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.EQUIPMENT_MANAGEMENT, action="编辑设备")
def equipment_update(request, pk):
    """4.2 借出中设备禁止手动改状态（2011）；禁止手动置为借出中（该状态仅由借还流转变更）"""
    equipment = _get_equipment_or_404(pk)
    ser = EquipmentUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    new_status = data.get("status")
    if new_status and new_status != equipment.status:
        if equipment.status == EquipmentStatus.BORROWED:
            raise BizException(
                "设备处于借出中，不可手动修改状态，请通过审批/归还流程变更",
                code=BizErrorCode.EQUIPMENT_BORROWED,
            )
        if new_status == EquipmentStatus.BORROWED:
            raise BizException(
                "设备处于借出中，不可手动修改状态",
                code=BizErrorCode.EQUIPMENT_BORROWED,
            )

    for field, val in data.items():
        setattr(equipment, field, val)
    equipment.save()
    return Result.to_response(Result.success(EquipmentAdminSerializer(equipment).data))


# ================= 4.3 逻辑删除设备 =================

@api_view(["DELETE"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.EQUIPMENT_MANAGEMENT, action="删除设备")
def equipment_delete(request, pk):
    """4.3 逻辑删除（is_deleted=true），历史借用记录保留；借出中不可删除"""
    equipment = _get_equipment_or_404(pk)
    if equipment.status == EquipmentStatus.BORROWED:
        raise BizException("设备处于借出中，不可删除", code=BizErrorCode.EQUIPMENT_BORROWED)
    equipment.is_deleted = True
    equipment.save(update_fields=["is_deleted", "update_time"])
    return Result.to_response(Result.success(message="设备已删除"))


# ================= 4.6 批量导入设备 =================

@api_view(["POST"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.EQUIPMENT_MANAGEMENT, action="导入设备")
def equipment_import(request):
    """4.6 form-data 上传 Excel；返回成功/失败明细（结构同 3.9）"""
    file = request.FILES.get("file")
    if not file:
        raise BizException("请上传 Excel 文件", code=BizErrorCode.EXCEL_FORMAT_ERROR)
    if not file.name.endswith((".xlsx", ".xls")):
        raise BizException("仅支持 .xlsx/.xls 格式", code=BizErrorCode.EXCEL_FORMAT_ERROR)

    try:
        headers, rows = read_excel_sheet(file.read())
    except ValueError as exc:
        raise BizException(str(exc), code=BizErrorCode.EXCEL_FORMAT_ERROR)

    success_count = 0
    fail_list = []
    for row in rows:
        eq_no = str(row.get("设备编号", "") or row.get("equipmentNo", "") or "").strip()
        name = str(row.get("设备名称", "") or row.get("name", "") or "").strip()

        if not eq_no:
            fail_list.append({"row": row.get("__row__"), "reason": "设备编号不能为空"})
            continue
        if not name:
            fail_list.append({"row": row.get("__row__"), "equipmentNo": eq_no,
                              "reason": "设备名称不能为空"})
            continue
        if Equipment.objects.filter(equipment_no=eq_no).exists():
            fail_list.append({"row": row.get("__row__"), "equipmentNo": eq_no, "name": name,
                              "reason": "设备编号已存在"})
            continue

        try:
            Equipment.objects.create(
                equipment_no=eq_no,
                name=name,
                model=str(row.get("型号", "") or row.get("model", "") or "").strip(),
                spec=str(row.get("规格", "") or row.get("spec", "") or "").strip(),
                location=str(row.get("存放位置", "") or row.get("location", "") or "").strip(),
                remark=str(row.get("备注", "") or row.get("remark", "") or "").strip(),
                status=EquipmentStatus.IDLE,
            )
            success_count += 1
        except Exception as exc:
            fail_list.append({"row": row.get("__row__"), "equipmentNo": eq_no, "name": name,
                              "reason": str(exc)})

    return Result.to_response(Result.success({
        "total": len(rows),
        "successCount": success_count,
        "failCount": len(fail_list),
        "failList": fail_list,
    }))


# ================= 4.7 导出设备台账 =================

@api_view(["GET"])
@permission_classes([IsAdmin])
def export_equipment(request):
    """4.7 导出设备台账 Excel；查询参数同 4.4；限制最大导出条数"""
    max_rows = getattr(settings, "EXPORT_MAX_ROWS", 10000)
    qs = _admin_filtered_qs(request)[:max_rows]

    headers = ["设备编号", "设备名称", "型号", "规格", "购置日期",
               "单价", "存放位置", "状态", "备注", "是否删除"]
    rows = []
    for eq in qs:
        rows.append([
            eq.equipment_no, eq.name, eq.model, eq.spec,
            str(eq.buy_date) if eq.buy_date else "",
            float(eq.price) if eq.price is not None else "",
            eq.location, eq.status, eq.remark,
            "是" if eq.is_deleted else "否",
        ])

    content = write_excel_sheet("设备台账", headers, rows)
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="equipment.xlsx"'
    return response


# ================= 4.8 设备图片上传 =================

_ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png"}
_MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_image(request):
    """4.8 通用图片上传：jpg/png ≤5MB，返回可访问 URL"""
    file = request.FILES.get("file")
    if not file:
        raise BizException("请选择要上传的图片", code=BizErrorCode.UPLOAD_FAILED)

    ext = Path(file.name).suffix.lower()
    if ext not in _ALLOWED_IMAGE_EXT:
        raise BizException("仅支持 jpg/png 格式图片", code=BizErrorCode.UPLOAD_FAILED)
    if file.size > _MAX_IMAGE_SIZE:
        raise BizException("图片大小不能超过 5MB", code=BizErrorCode.UPLOAD_FAILED)

    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = Path(settings.MEDIA_ROOT) / filename
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
    except OSError as exc:
        raise BizException(f"文件上传失败：{exc}", code=BizErrorCode.UPLOAD_FAILED)

    url = request.build_absolute_uri(f"{settings.MEDIA_URL}{filename}")
    return Result.to_response(Result.success({
        "url": url,
        "filename": filename,
        "size": file.size,
    }))
