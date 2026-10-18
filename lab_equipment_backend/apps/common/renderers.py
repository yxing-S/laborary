"""自定义 JSON Renderer（G3）：保证 DRF 所有响应都包裹在统一结构中

成功（HTTP 2xx）：{"code": 200, "msg": "操作成功", "data": <原始数据>}
失败（异常已被 exception_handler 转成 dict）：直接透传
"""
from rest_framework.renderers import JSONRenderer


class JSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # 异常场景已被 custom_exception_handler 包裹成 {code, msg, data} 结构
        # 成功场景：data 可能是分页 dict / 单个对象 / 列表 / None
        if isinstance(data, dict) and "code" in data and "msg" in data:
            return super().render(data, accepted_media_type, renderer_context)

        # 正常成功响应，包裹统一格式
        wrapped = {"code": 200, "msg": "操作成功", "data": data}
        return super().render(wrapped, accepted_media_type, renderer_context)
