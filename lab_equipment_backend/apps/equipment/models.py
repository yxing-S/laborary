
from decimal import Decimal

from django.db import models

from apps.common.constants import EquipmentStatus
from apps.common.models import TimestampMixin


class Equipment(TimestampMixin):
    """设备表（对应 SQL: equipment）"""

    equipment_no = models.CharField("设备编号", max_length=50, unique=True, db_index=True)
    name = models.CharField("设备名称", max_length=100, db_index=True)
    model = models.CharField("型号", max_length=100, blank=True, default="")
    spec = models.CharField("规格", max_length=200, blank=True, default="")
    buy_date = models.DateField("购置日期", null=True, blank=True)
    price = models.DecimalField(
        "单价", max_digits=10, decimal_places=2, null=True, blank=True
    )
    location = models.CharField("存放位置", max_length=200, blank=True, default="", db_index=True)
    status = models.CharField(
        "设备状态", max_length=20, default=EquipmentStatus.IDLE, db_index=True
    )
    img_url = models.CharField("设备图片", max_length=255, blank=True, default="")
    remark = models.CharField("备注", max_length=500, blank=True, default="")
    is_deleted = models.BooleanField("逻辑删除", default=False)

    class Meta:
        db_table = "equipment"
        verbose_name = "设备"
        verbose_name_plural = verbose_name
        ordering = ["-id"]

    def __str__(self):
        return f"{self.equipment_no} - {self.name}"
