"""操作日志路由（6.1，责任人 B）"""
from django.urls import path

from apps.log import views

urlpatterns = [
    path("admin/log/list", views.log_list),  # 6.1 操作日志查询
]
