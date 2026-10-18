"""业务异常定义（G4 全局异常处理的一部分）

用法：在 service / view 中直接 raise：
    raise BizException("设备编号已存在", code=400)
    raise NotFoundError("设备不存在")
    raise ForbiddenError()
"""


class BizException(Exception):
    """业务异常：code 对应接口文档第 8 节业务码"""

    def __init__(self, msg: str = "业务处理失败", code: int = 400, data=None):
        self.code = code
        self.msg = msg
        self.data = data
        super().__init__(msg)


class BadRequestError(BizException):
    def __init__(self, msg: str = "参数错误", data=None):
        super().__init__(msg=msg, code=400, data=data)


class UnauthorizedError(BizException):
    def __init__(self, msg: str = "未登录或登录已过期，请重新登录", data=None):
        super().__init__(msg=msg, code=401, data=data)


class ForbiddenError(BizException):
    def __init__(self, msg: str = "权限不足，无该操作访问权限", data=None):
        super().__init__(msg=msg, code=403, data=data)


class NotFoundError(BizException):
    def __init__(self, msg: str = "资源不存在", data=None):
        super().__init__(msg=msg, code=404, data=data)
