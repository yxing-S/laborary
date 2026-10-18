"""通用字典接口

7.1 GET /api/dict/equipmentStatus  -> ["闲置","借出中","维修中","已报废"]
7.2 GET /api/dict/borrowStatus    -> ["待审批","已通过","已驳回","已取消","已归还"]
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.common.constants import ApprovalStatus, EquipmentStatus
from apps.common.response import Result


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def equipment_status_dict(request):
    return Result.to_response(Result.success(EquipmentStatus.ALL))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def borrow_status_dict(request):
    return Result.to_response(Result.success(ApprovalStatus.ALL))
