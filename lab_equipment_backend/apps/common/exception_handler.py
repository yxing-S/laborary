

"""
所有异常统一输出：{"code": ..., "msg": ..., "data": null}
"""
import logging

from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response as DRFResponse
from rest_framework.views import exception_handler as drf_default_handler

from apps.common.exceptions import BizException
from apps.common.response import Result

logger = logging.getLogger("django")


def custom_exception_handler(exc, context):
    """DRF 异常 -> 统一 {code, msg, data} 结构"""
    # ---- 自定义业务异常 ----
    if isinstance(exc, BizException):
        return DRFResponse(
            Result.error(exc.code, exc.msg, exc.data),
            status=exc.code if exc.code in (400, 401, 403, 404) else 400,
        )

    # ---- DRF 已知异常 ----
    response = drf_default_handler(exc, context)

    # ---- DRF 认出的已知异常 ----
    if response is not None:
        data = response.data
        # ValidationError 的 data 可能是 dict（字段错误）或 list
        if isinstance(data, dict):
            if "detail" in data:
                msg = str(data["detail"])
            elif "non_field_errors" in data:
                msg = str(data["non_field_errors"][0])
            else:
                # 取第一个字段的第一个错误
                first_key = next(iter(data))
                first_val = data[first_key]
                if isinstance(first_val, list) and first_val:
                    field_label = first_key
                    msg = f"{field_label}: {first_val[0]}" if field_label != "non_field_errors" else str(first_val[0])
                else:
                    msg = str(first_val)
        elif isinstance(data, list) and data:
            msg = str(data[0])
        else:
            msg = str(data)

        # 映射 HTTP 状态码 -> 业务码（接口文档第 8 节）
        status = response.status_code
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            code = 401
            msg = "未登录或登录已过期，请重新登录"
        elif isinstance(exc, PermissionDenied):
            code = 403
            msg = msg or "权限不足，无该操作访问权限"
        elif isinstance(exc, NotFound):
            code = 404
        elif isinstance(exc, ValidationError):
            code = 400
        elif isinstance(exc, MethodNotAllowed):
            code = 400
        else:
            code = 400 if status < 500 else 500

        response.data = Result.error(code, msg)
        return response

    # ---- 非 DRF 管辖的异常（兜底 500）----
    logger.exception("服务器内部异常: %s", exc)
    return DRFResponse(
        Result.error(500, "服务器内部异常"),
        status=500,
    )
