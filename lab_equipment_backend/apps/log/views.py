"""操作日志查询视图（对齐《后端API接口文档》9.1，责任人 B）

GET /admin/operation-logs
Query 筛选：operatorId / module / action / startTime / endTime
"""
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes

from apps.common.exceptions import BadRequestError
from apps.common.pagination import paginate
from apps.common.permissions import IsAdmin
from apps.log.models import OperationLog
from apps.log.serializers import OperationLogOutSerializer


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


@api_view(["GET"])
@permission_classes([IsAdmin])
def log_list(request):
    module = (request.query_params.get("module") or "").strip()
    action = (request.query_params.get("action") or "").strip()
    operator_id = _parse_int_param(request, "operatorId")
    start_time = _parse_datetime_param(request, "startTime")
    end_time = _parse_datetime_param(request, "endTime")

    qs = OperationLog.objects.all()
    if module:
        qs = qs.filter(module=module)
    if action:
        qs = qs.filter(action=action)
    if operator_id is not None:
        qs = qs.filter(operator_id=operator_id)
    if start_time:
        qs = qs.filter(create_time__gte=start_time)
    if end_time:
        qs = qs.filter(create_time__lte=end_time)
    qs = qs.order_by("-id")

    return paginate(request, qs, OperationLogOutSerializer)
