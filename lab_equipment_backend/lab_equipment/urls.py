"""
URL 路由总装配（G1）

开发者 A 负责的模块：
- /api/user/**          用户模块 1.1-1.12
- /api/equipment/**     设备管理 2.1-2.6（普通用户/管理员可见）
- /api/admin/user/**    管理员用户管理 1.7-1.12
- /api/admin/equipment/** 设备管理 2.3-2.6
- /api/admin/export/equipment  5.3 设备台账导出
- /api/dict/**          7.1/7.2 通用字典

开发者 B 负责的模块：
- /api/borrow/**                 借用申请/我的申请/取消/归还 3.1-3.3、4.1
- /api/admin/borrow/**           审批/待审批/总览/待归还/确认归还 3.4-3.6、4.2-4.3
- /api/admin/statistics/**       设备/用户借用统计 5.1-5.2
- /api/admin/export/borrowRecord 借用记录导出 5.4
- /api/admin/log/list            操作日志查询 6.1
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
