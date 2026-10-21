"""操作日志路由（对齐《后端API接口文档》9.1，责任人 B）"""
from django.urls import path

from apps.log import views

urlpatterns = [
    path("admin/operation-logs", views.log_list),  # 9.1 操作日志列表
]
