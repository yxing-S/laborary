
from django.db import models

from apps.common.constants import ApprovalStatus, OverdueStatus
from apps.common.models import TimestampMixin


class BorrowRecord(TimestampMixin):
    """借用记录表（对应 SQL: borrow_record）"""

    user = models.ForeignKey(
        "user.User", on_delete=models.PROTECT, related_name="borrow_records",
        verbose_name="申请人",
    )
    equipment = models.ForeignKey(
        "equipment.Equipment", on_delete=models.PROTECT,
        related_name="borrow_records", verbose_name="设备",
    )

    plan_borrow_start = models.DateTimeField("计划借用开始时间")
    plan_return_time = models.DateTimeField("计划归还时间", db_index=True)
    borrow_purpose = models.CharField("借用用途", max_length=255, blank=True, default="")
    remark = models.CharField("申请备注", max_length=500, blank=True, default="")

    approval_status = models.CharField(
        "审批状态", max_length=20, default=ApprovalStatus.PENDING, db_index=True
    )
    approval_comment = models.CharField("审批意见", max_length=500, blank=True, default="")
    auditor = models.ForeignKey(
        "user.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audited_records", verbose_name="审批人",
    )
    audit_time = models.DateTimeField("审批时间", null=True, blank=True)
    cancel_time = models.DateTimeField("取消时间", null=True, blank=True)

    return_apply_time = models.DateTimeField("发起归还申请时间", null=True, blank=True)
    actual_return_time = models.DateTimeField("实际归还时间", null=True, blank=True)
    return_type = models.CharField("归还类型", max_length=20, blank=True, default="")
    damage_desc = models.CharField("损坏/丢失说明", max_length=500, blank=True, default="")

    overdue_status = models.CharField(
        "逾期状态", max_length=20, default=OverdueStatus.NORMAL, db_index=True
    )

    class Meta:
        db_table = "borrow_records"
        verbose_name = "借用记录"
        verbose_name_plural = verbose_name
        ordering = ["-id"]

    def __str__(self):
        return f"借用记录 #{self.id} - 用户{self.user_id} 设备{self.equipment_id}"
