"""借用模块路由（对齐《后端API接口文档》六、七、八章）

仅登记现有接口，缺失接口（6.7 逾期校验、8.3 逾期统计）不实现。
根路径前缀 /api/ 由 lab_equipment/urls.py 统一挂载，此处不处理。
"""
from django.urls import path

from apps.borrow import views

urlpatterns = [
    # ---- 借用申请 ----
    path("borrow-applications", views.borrow_apply),                     # 6.1 POST
    path("borrow-applications/my", views.borrow_my_list),                # 6.2 GET
    path("borrow-applications/<int:pk>/cancel", views.borrow_cancel),    # 6.3 PUT
    path("admin/borrow-applications/pending", views.borrow_pending_list),  # 6.4 GET
    path("admin/borrow-applications/<int:pk>/approval", views.borrow_audit),  # 6.5 PUT

    # ---- 借用记录 ----
    path("admin/borrow-records", views.borrow_all_list),                 # 6.6 GET
    path("admin/borrow-records/export", views.export_borrow_record),     # 8.4 GET

    # ---- 归还 ----
    path("return-applications", views.borrow_return_apply),              # 7.1 POST
    path("admin/return-applications/pending", views.borrow_wait_return_list),  # 7.2 GET
    path("admin/return-applications/<int:pk>/confirm", views.borrow_confirm_return),  # 7.3 PUT

    # ---- 统计 ----
    path("admin/statistics/equipment-usage", views.equipment_statistics),  # 8.1 GET
    path("admin/statistics/user-borrow", views.user_statistics),         # 8.2 GET
]
