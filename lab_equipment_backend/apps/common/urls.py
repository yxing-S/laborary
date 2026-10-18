"""通用字典路由（7.1 / 7.2）"""
from django.urls import path

from apps.common.views import borrow_status_dict, equipment_status_dict

urlpatterns = [
    path("dict/equipmentStatus", equipment_status_dict),
    path("dict/borrowStatus", borrow_status_dict),
]
