"""统一返回格式 Result（G3）

{
  "code": 200,       # 200成功 / 400参数或业务错误 / 401未登录 / 403权限不足 / 404不存在 / 500异常
  "msg": "操作提示信息",
  "data": {}         # 失败时可为 null
}
"""
from django.http import JsonResponse
from rest_framework.response import Response


class Result:
    """工具类：构造统一返回结构"""

    @staticmethod
    def success(data=None, msg: str = "操作成功") -> dict:
        return {"code": 200, "msg": msg, "data": data}

    @staticmethod
    def error(code: int = 400, msg: str = "操作失败", data=None) -> dict:
        return {"code": code, "msg": msg, "data": data}

    @staticmethod
    def to_response(data: dict, status: int = 200) -> Response:
        """DRF View 返回用"""
        return Response(data, status=status)

    @staticmethod
    def to_json_response(data: dict, status: int = 200) -> JsonResponse:
        """普通 Django View 返回用（如文件下载场景）"""
        return JsonResponse(data, status=status, json_dumps_params={"ensure_ascii": False})
