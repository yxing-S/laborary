"""用户/认证模块路由（对齐《后端API接口文档》二、三章）

同一路径注册多个方法视图时，通过 method_dispatch 按 HTTP 方法分派
（Django URL resolver 只命中第一个匹配的 pattern，需在内部按方法二次分派）。
"""
from django.http import HttpResponseNotAllowed
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from apps.user import views


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
    # ---- 认证模块 ----
    path("auth/register", views.register),                        # 2.1
    path("auth/login", views.login),                              # 2.2
    path("auth/logout", views.logout),                            # 2.3
    path("auth/reset-password", views.reset_password),            # 2.4
    path("auth/password", views.change_password),                 # 2.5

    # ---- 当前用户 ----
    path("users/me", method_dispatch(
        get=views.user_me, put=views.user_me_update)),            # 3.1 / 3.2

    # ---- 管理员用户管理 ----
    path("admin/users", method_dispatch(
        get=views.admin_user_list, post=views.admin_user_add)),   # 3.3 / 3.4
    path("admin/users/import", views.admin_user_import),          # 3.9
    path("admin/users/export", views.admin_user_export),          # 3.10
    path("admin/users/<int:pk>", method_dispatch(
        put=views.admin_user_update, delete=views.admin_user_delete)),  # 3.5 / 3.8
    path("admin/users/<int:pk>/status", views.admin_user_status),            # 3.6
    path("admin/users/<int:pk>/reset-password", views.admin_reset_password),  # 3.7
]
