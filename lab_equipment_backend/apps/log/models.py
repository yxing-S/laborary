"""操作日志模型（G9 切面 + 6.1 查询，责任人 B；表结构 G2 冻结）


"""
from django.db import models

from apps.common.models import TimestampMixin


class OperationLog(TimestampMixin):
    """系统操作日志表（对应 SQL: operation_log）"""

    operator = models.ForeignKey(
        "user.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="operation_logs", verbose_name="操作人",
    )
    operator_name = models.CharField("操作人姓名", max_length=50, blank=True, default="")
    module = models.CharField("功能模块", max_length=50, blank=True, default="", db_index=True)
    action = models.CharField("操作行为", max_length=100, blank=True, default="")
    request_method = models.CharField("HTTP方法", max_length=10, blank=True, default="")
    request_url = models.CharField("请求路径", max_length=255, blank=True, default="")
    request_params = models.TextField("请求参数", blank=True, default="")
    ip = models.CharField("操作IP", max_length=50, blank=True, default="")
    result = models.CharField("操作结果", max_length=20, default="成功")
    detail = models.TextField("异常信息/备注", blank=True, default="")

    class Meta:
        db_table = "operation_log"
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name
        ordering = ["-id"]
