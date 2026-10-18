
from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.common.constants import EquipmentStatus, Role
from apps.common.exceptions import BadRequestError, NotFoundError
from apps.common.permissions import IsAdminOrReadOnly, IsAdmin
from apps.common.response import Result
from apps.common.utils import read_excel_sheet, write_excel_sheet
from apps.equipment.models import Equipment
from apps.equipment.serializers import (
    EquipmentAddSerializer,
    EquipmentDetailSerializer,
    EquipmentOutSerializer,
    EquipmentUpdateSerializer,
)


# ================= 2.1 设备列表 =================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def equipment_list(request):
    """2.1 user 自动过滤 is_deleted=true，admin 看全部"""
    page = int(request.query_params.get("page", 1))
    size = int(request.query_params.get("size", 10))
    name = request.query_params.get("name", "")
    equipment_no = request.query_params.get("equipmentNo", "")
    status = request.query_params.get("status", "")
    location = request.query_params.get("location", "")

    is_admin = request.user.role == Role.ADMIN
    qs = Equipment.objects.all().order_by("-id")
    if not is_admin:
        qs = qs.filter(is_deleted=False)
    if name:
        qs = qs.filter(name__icontains=name)
    if equipment_no:
        qs = qs.filter(equipment_no__icontains=equipment_no)
    if status:
        qs = qs.filter(status=status)
    if location:
        qs = qs.filter(location__icontains=location)

    total = qs.count()
    records = qs[(page - 1) * size: page * size]
    pages = (total + size - 1) // size if size > 0 else 0
    return Result.to_response(Result.success({
        "total": total,
        "pages": pages,
        "current": page,
        "records": EquipmentOutSerializer(records, many=True).data,
    }))


# ================= 2.2 设备详情 =================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def equipment_detail(request, pk):
    """2.2 完整设备信息 + 该设备历史借用记录列表（跨域只读 B 的表）"""
    equipment = _get_equipment_or_404(pk)
    # 普通用户看不到已逻辑删除的设备
    if equipment.is_deleted and request.user.role != Role.ADMIN:
        raise NotFoundError("设备不存在")
    return Result.to_response(
        Result.success(EquipmentDetailSerializer(equipment).data)
    )


# ================= 2.3 管理员新增设备 =================

@api_view(["POST"])
@permission_classes([IsAdmin])
def equipment_add(request):
    """2.3 equipmentNo 全局唯一"""
    ser = EquipmentAddSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    if Equipment.objects.filter(equipment_no=ser.validated_data["equipment_no"]).exists():
        raise BadRequestError("设备编号已存在")

    equipment = Equipment.objects.create(**ser.validated_data)
    return Result.to_response(Result.success(EquipmentOutSerializer(equipment).data))


# ================= 2.4 管理员编辑设备 =================

@api_view(["PUT"])
@permission_classes([IsAdmin])
def equipment_update(request, pk):
    """2.4 借出中设备拒绝手动改 status；禁止把设备改为借出中"""
    equipment = _get_equipment_or_404(pk)
    ser = EquipmentUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    # 业务约束：借出中的设备禁止修改 status
    new_status = data.get("status")
    if equipment.status == EquipmentStatus.BORROWED:
        if new_status and new_status != equipment.status:
            raise BadRequestError(
                '设备当前处于"借出中"，不能手动修改状态，请通过审批/归还流程变更'
            )
    # 禁止通过编辑接口把设备改为"借出中"（该状态只由借还业务 3.5/4.3 变更）
    if new_status == EquipmentStatus.BORROWED:
        raise BadRequestError('不能通过编辑接口将设备状态设为"借出中"')

    for field, val in data.items():
        setattr(equipment, field, val)
    equipment.save()
    return Result.to_response(Result.success(EquipmentOutSerializer(equipment).data))


# ================= 2.5 逻辑删除设备 =================

@api_view(["DELETE"])
@permission_classes([IsAdmin])
def equipment_delete(request, pk):
    """2.5 非物理删除，置 is_deleted=true，历史记录保留"""
    equipment = _get_equipment_or_404(pk)
    if equipment.status == EquipmentStatus.BORROWED:
        raise BadRequestError('设备处于"借出中"，不能删除')
    equipment.is_deleted = True
    equipment.save()
    return Result.to_response(Result.success(msg="设备已删除"))


# ================= 2.6 批量导入设备（第二阶段）=================

@api_view(["POST"])
@permission_classes([IsAdmin])
def equipment_import(request):
    """2.6 form-data 上传 Excel"""
    file = request.FILES.get("file")
    if not file:
        raise BadRequestError("请上传 Excel 文件")
    if not file.name.endswith(".xlsx"):
        raise BadRequestError("仅支持 .xlsx 格式")

    headers, rows = read_excel_sheet(file.read())
    success_count = 0
    fail_rows = []

    for row in rows:
        eq_no = str(row.get("设备编号", "") or row.get("equipmentNo", "") or "").strip()
        name = str(row.get("设备名称", "") or row.get("name", "") or "").strip()

        if not eq_no:
            fail_rows.append({"row": row.get("__row__"), "reason": "设备编号不能为空"})
            continue
        if not name:
            fail_rows.append({"row": row.get("__row__"), "equipmentNo": eq_no, "reason": "设备名称不能为空"})
            continue
        if Equipment.objects.filter(equipment_no=eq_no).exists():
            fail_rows.append({"row": row.get("__row__"), "equipmentNo": eq_no, "reason": "设备编号已存在"})
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
        except Exception as e:
            fail_rows.append({"row": row.get("__row__"), "equipmentNo": eq_no, "reason": str(e)})

    return Result.to_response(Result.success({
        "successCount": success_count,
        "failCount": len(fail_rows),
        "failRows": fail_rows,
    }))


# ================= 5.3 导出设备台账 Excel =================

@api_view(["GET"])
@permission_classes([IsAdmin])
def export_equipment(request):
    """5.3 响应头设置文件下载流；限制最大导出条数"""
    max_rows = getattr(settings, "EXPORT_MAX_ROWS", 10000)
    qs = Equipment.objects.all().order_by("id")[:max_rows]

    headers = ["设备编号", "设备名称", "型号", "规格", "购置日期",
               "单价", "存放位置", "状态", "备注", "是否删除"]
    rows = []
    for eq in qs:
        rows.append([
            eq.equipment_no, eq.name, eq.model, eq.spec,
            str(eq.buy_date) if eq.buy_date else "",
            float(eq.price) if eq.price else "",
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


# ================= 辅助函数 =================

def _get_equipment_or_404(pk: int) -> Equipment:
    equipment = Equipment.objects.filter(pk=pk).first()
    if equipment is None:
        raise NotFoundError("设备不存在")
    return equipment
