"""通用字典接口

7.1 GET /api/v1/dict/equipmentStatus  -> ["idle","borrowed","repairing","scrapped"]
7.2 GET /api/v1/dict/borrowStatus    -> ["pending","approved","rejected","returned","cancelled"]
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
