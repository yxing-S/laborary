"""用户/认证模块路由（对齐《后端API接口文档》二、三章）"""
from django.urls import path

from apps.user import views

urlpatterns = [
    # ---- 认证模块 ----
    path("auth/register", views.register),                        # 2.1
    path("auth/login", views.login),                              # 2.2
    path("auth/logout", views.logout),                            # 2.3
    path("auth/reset-password", views.reset_password),            # 2.4
    path("auth/password", views.change_password),                 # 2.5

    # ---- 当前用户 ----
    path("users/me", views.user_me),                              # 3.1 GET
    path("users/me", views.user_me_update),                       # 3.2 PUT

    # ---- 管理员用户管理 ----
    path("admin/users", views.admin_user_list),                   # 3.3 GET
    path("admin/users", views.admin_user_add),                    # 3.4 POST
    path("admin/users/import", views.admin_user_import),          # 3.9
    path("admin/users/export", views.admin_user_export),          # 3.10
    path("admin/users/<int:pk>", views.admin_user_update),        # 3.5 PUT
    path("admin/users/<int:pk>", views.admin_user_delete),        # 3.8 DELETE
    path("admin/users/<int:pk>/status", views.admin_user_status),            # 3.6
    path("admin/users/<int:pk>/reset-password", views.admin_reset_password),  # 3.7
]
