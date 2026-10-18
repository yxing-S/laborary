"""公共 Abstract Model（G2）"""
from django.db import models


class TimestampMixin(models.Model):
    """create_time / update_time，数据库自动维护"""

    create_time = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    update_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        abstract = True
