"""
URL 路由总装配（G1）

开发者 A 负责的模块：
- /api/user/**          用户模块 1.1-1.12
- /api/equipment/**     设备管理 2.1-2.6（普通用户/管理员可见）
- /api/admin/user/**    管理员用户管理 1.7-1.12
- /api/admin/equipment/** 设备管理 2.3-2.6
- /api/admin/export/equipment  5.3 设备台账导出
- /api/dict/**          7.1/7.2 通用字典
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.user.urls")),
    path("api/", include("apps.equipment.urls")),
    path("api/", include("apps.common.urls")),
    path("api/", include("apps.borrow.urls")),
    path("api/", include("apps.log.urls")),
]
