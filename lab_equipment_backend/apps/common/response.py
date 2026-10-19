"""统一返回格式 Result（对齐《后端API接口文档》1.2 通用响应结构）

{
  "code": 200,            # 200成功 / 4xx HTTP错误 / 2xxx 业务错误码
  "message": "操作提示信息",
  "data": {},             # 失败时可为 null
  "timestamp": 1695504000000  # 服务器时间戳（毫秒）
}
"""
import time

from django.http import JsonResponse
from rest_framework.response import Response


def now_ms() -> int:
    """服务器当前时间戳（毫秒）"""
    return int(time.time() * 1000)


class Result:
    """工具类：构造统一返回结构"""

    @staticmethod
    def success(data=None, message: str = "操作成功") -> dict:
        return {"code": 200, "message": message, "data": data, "timestamp": now_ms()}

    @staticmethod
    def error(code: int = 400, message: str = "操作失败", data=None) -> dict:
        return {"code": code, "message": message, "data": data, "timestamp": now_ms()}

    @staticmethod
    def to_response(data: dict, status: int = 200) -> Response:
        """DRF View 返回用"""
        return Response(data, status=status)

    @staticmethod
    def to_json_response(data: dict, status: int = 200) -> JsonResponse:
        """普通 Django View 返回用（如文件下载场景）"""
        return JsonResponse(data, status=status, json_dumps_params={"ensure_ascii": False})
