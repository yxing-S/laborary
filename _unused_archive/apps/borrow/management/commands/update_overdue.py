"""每日扫描逾期记录（G12，责任人 B）

用法：python manage.py update_overdue
建议配合系统定时任务（cron）每日执行，作为查询时实时计算之外的兜底。
"""
from django.core.management.base import BaseCommand

from apps.borrow.services import refresh_overdue_status


class Command(BaseCommand):
    help = "扫描借用记录，将已通过且已超过计划归还时间仍未归还的记录置为已逾期"

    def handle(self, *args, **options):
        count = refresh_overdue_status()
        self.stdout.write(self.style.SUCCESS(f"逾期状态更新完成，本次更新 {count} 条记录"))
