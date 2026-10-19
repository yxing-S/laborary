"""借用域公共服务（G12 逾期状态，责任人 B）

被 3.6 / 4.2 / 5.1 / 5.2 查询时实时计算兜底，以及每日 management command 复用。
"""
from django.utils import timezone

from apps.borrow.models import BorrowRecord
from apps.common.constants import ApprovalStatus, OverdueStatus


def compute_return_overdue_status(plan_return_time, actual_return_time):
    """确认归还后，按实际归还时间与计划归还时间计算逾期状态。

    超时 -> 逾期已归还；未超时 -> 正常。
    """
    if actual_return_time is None:
        return OverdueStatus.NORMAL
    return (
        OverdueStatus.OVERDUE_RETURNED
        if actual_return_time > plan_return_time
        else OverdueStatus.NORMAL
    )


def refresh_overdue_status():
    """把「已通过且未归还且已超计划归还时间」的记录置为「已逾期」。

    返回本次更新的记录数（0 表示无变化）。
    """
    now = timezone.now()
    return BorrowRecord.objects.filter(
        approval_status=ApprovalStatus.PASSED,
        actual_return_time__isnull=True,
        overdue_status=OverdueStatus.NORMAL,
        plan_return_time__lt=now,
    ).update(overdue_status=OverdueStatus.OVERDUE)
