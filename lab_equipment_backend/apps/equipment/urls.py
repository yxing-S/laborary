"""设备模块路由（对齐《后端API接口文档》四、五章）

同一路径注册多个方法视图时，通过 method_dispatch 按 HTTP 方法分派
（Django URL resolver 只命中第一个匹配的 pattern，需在内部按方法二次分派）。
"""
from django.http import HttpResponseNotAllowed
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from apps.equipment import views


def method_dispatch(**method_views):
    """按 HTTP 方法分派到不同视图函数（DRF 视图自身已处理认证/权限）"""

    @csrf_exempt
    def dispatch(request, *args, **kwargs):
        view = method_views.get(request.method.lower())
        if view is None:
            return HttpResponseNotAllowed([m.upper() for m in method_views])
        return view(request, *args, **kwargs)

    return dispatch


urlpatterns = [
    # ---- 设备浏览（登录用户）----
    path("equipment", views.equipment_browse_list),                     # 5.1 GET
    path("equipment/<int:pk>", views.equipment_browse_detail),          # 5.2 GET

    # ---- 管理员设备管理 ----
    path("admin/equipment", method_dispatch(
        get=views.admin_equipment_list, post=views.equipment_add)),     # 4.4 / 4.1
    path("admin/equipment/import", views.equipment_import),             # 4.6 POST
    path("admin/equipment/export", views.export_equipment),             # 4.7 GET
    path("admin/equipment/<int:pk>", method_dispatch(
        get=views.admin_equipment_detail,
        put=views.equipment_update,
        delete=views.equipment_delete)),                                # 4.5 / 4.2 / 4.3

    # ---- 图片上传 ----
    path("upload/image", views.upload_image),                           # 4.8 POST
]
