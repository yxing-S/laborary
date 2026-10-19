"""操作日志切面（G9，责任人 B）

用法（装饰在 DRF 视图函数上，置于 @permission_classes 之下）：
    @api_view(["POST"])
    @permission_classes([IsAuthenticated])
    @log_operation(module=LogModule.BORROW, action="提交借用申请")
    def borrow_apply(request):
        ...

说明：
- 视图正常返回或抛出异常均会落库 operation_log；
- 日志写入本身任何异常都会被吞掉，绝不阻断业务响应。
"""
import json
from functools import wraps

from apps.common.constants import LogResult
from apps.log.models import OperationLog

_SENSITIVE_KEYS = ("password", "passwd", "token", "secret", "authorization")
_PARAMS_MAX_LEN = 2000


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _mask_sensitive(data):
    """递归脱敏 password / token 等敏感字段"""
    if isinstance(data, dict):
        return {
            k: ("******" if isinstance(k, str) and any(h in k.lower() for h in _SENSITIVE_KEYS) else _mask_sensitive(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_mask_sensitive(item) for item in data]
    return data


def _extract_params(request):
    """提取并脱敏请求参数，超长截断"""
    try:
        if request.method == "GET":
            data = dict(request.query_params)
        else:
            data = dict(request.data) if getattr(request, "data", None) else {}
        return json.dumps(_mask_sensitive(data), ensure_ascii=False, default=str)[:_PARAMS_MAX_LEN]
    except Exception:
        return ""


def _record_operation(request, module, action, success, detail=""):
    """落库一条操作日志；任何异常均静默，不影响业务"""
    try:
        user = request.user if getattr(request.user, "is_authenticated", False) else None
        OperationLog.objects.create(
            operator=user,
            operator_name=getattr(user, "name", "") or "",
            module=module,
            action=action,
            request_method=request.method,
            request_url=request.path[:255],
            request_params=_extract_params(request),
            ip=_client_ip(request),
            result=LogResult.SUCCESS if success else LogResult.FAIL,
            detail=detail,
        )
    except Exception:
        pass


def log_operation(module, action):
    """记录视图操作日志的装饰器"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                response = view_func(request, *args, **kwargs)
                status_code = getattr(response, "status_code", 200)
                success = status_code < 400
                detail = "" if success else f"HTTP {status_code}"
                _record_operation(request, module, action, success, detail)
                return response
            except Exception as exc:
                _record_operation(request, module, action, False, str(exc))
                raise

        return wrapper

    return decorator
