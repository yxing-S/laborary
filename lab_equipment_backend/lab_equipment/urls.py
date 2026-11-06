"""
URL 路由总装配（G1）

开发者 A 负责的模块（《后端API接口文档》）：
- /api/auth/**            认证模块 2.1-2.5
- /api/users/**           用户模块 3.1-3.2
- /api/admin/users/**     管理员用户管理 3.3-3.10
- /api/equipment/**       设备浏览 5.1-5.2
- /api/admin/equipment/** 设备管理 4.1-4.7
- /api/upload/image       图片上传 4.8
- /api/dict/**            通用字典

开发者 B 负责的模块：
- /api/borrow-applications/** 等 借用流转（六、七、八章）
- /api/admin/operation-logs    操作日志（九章）
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # 前端 baseURL 为 /real-api/api/v1，Nginx 去掉 /real-api 前缀后即 /api/v1/...
    path("api/v1/", include("apps.user.urls")),
    path("api/v1/", include("apps.equipment.urls")),
    path("api/v1/", include("apps.common.urls")),
    # B 的模块：借用流转（六/七/八章）+ 操作日志（九章）
    path("api/v1/", include("apps.borrow.urls")),
    path("api/v1/", include("apps.log.urls")),
]

# 图片上传（4.8）的媒体文件访问；仅 DEBUG 生效，生产环境由 Web 服务器托管
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
