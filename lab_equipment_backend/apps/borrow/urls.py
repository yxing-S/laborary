"""借用模块路由（3.1 - 3.6 / 4.1 - 4.3 / 5.1 / 5.2 / 5.4，责任人 B）"""
from django.urls import path

from apps.borrow import views

urlpatterns = [
    # 借用申请
    path("borrow/apply", views.borrow_apply),                              # 3.1
    path("borrow/my/list", views.borrow_my_list),                          # 3.2
    path("borrow/cancel/<int:recordId>", views.borrow_cancel),             # 3.3

    # 审批
    path("admin/borrow/pendingList", views.borrow_pending_list),           # 3.4
    path("admin/borrow/audit/<int:recordId>", views.borrow_audit),         # 3.5
    path("admin/borrow/allList", views.borrow_all_list),                   # 3.6

    # 归还
    path("borrow/returnApply/<int:recordId>", views.borrow_return_apply),  # 4.1
    path("admin/borrow/waitReturnList", views.borrow_wait_return_list),    # 4.2
    path("admin/borrow/confirmReturn/<int:recordId>", views.borrow_confirm_return),  # 4.3

    # 统计与导出
    path("admin/statistics/equipment", views.equipment_statistics),        # 5.1
    path("admin/statistics/user", views.user_statistics),                  # 5.2
    path("admin/export/borrowRecord", views.export_borrow_record),         # 5.4
]
