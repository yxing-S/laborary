"""设备模块路由（2.1 - 2.6 / 5.3）"""
from django.urls import path

from apps.equipment import views

urlpatterns = [
    # ---- 设备通用接口（admin/user 均可）----
    path("equipment/list", views.equipment_list),           # 2.1
    path("equipment/<int:pk>", views.equipment_detail),     # 2.2

    # ---- 管理员设备管理接口 ----
    path("admin/equipment/add", views.equipment_add),                      # 2.3
    path("admin/equipment/update/<int:pk>", views.equipment_update),      # 2.4
    path("admin/equipment/delete/<int:pk>", views.equipment_delete),     # 2.5
    path("admin/equipment/import", views.equipment_import),               # 2.6

    # ---- 导出 ----
    path("admin/export/equipment", views.export_equipment),               # 5.3
]
