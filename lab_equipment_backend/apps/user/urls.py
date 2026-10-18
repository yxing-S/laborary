"""用户模块路由（1.1 - 1.12）"""
from django.urls import path

from apps.user import views

urlpatterns = [
    # ---- 用户通用接口（admin/user 均可）----
    path("user/register", views.register),                # 1.1
    path("user/login", views.login),                      # 1.2
    path("user/info", views.user_info),                   # 1.3
    path("user/profile", views.update_profile),           # 1.4
    path("user/password", views.update_password),        # 1.5
    path("user/resetPwdBySelf", views.reset_pwd_by_self), # 1.6

    # ---- 管理员用户管理接口 ----
    path("admin/user/list", views.admin_user_list),       # 1.7
    path("admin/user/add", views.admin_user_add),         # 1.8
    path("admin/user/update/<int:pk>", views.admin_user_update),     # 1.9
    path("admin/user/status/<int:pk>", views.admin_user_status),    # 1.10
    path("admin/user/resetPwd/<int:pk>", views.admin_reset_pwd),  # 1.11
    path("admin/user/import", views.admin_user_import),  # 1.12
]
