"""操作日志 Serializer（对齐《后端API接口文档》9.1，责任人 B）

响应 data.list 单项字段：
id / operatorId / operatorName / module / action / content / ipAddress / operateTime
"""
from rest_framework import serializers

from apps.log.models import OperationLog


class OperationLogOutSerializer(serializers.ModelSerializer):
    operatorId = serializers.IntegerField(source="operator_id", allow_null=True)
    operatorName = serializers.CharField(source="operator_name", default="")
    content = serializers.CharField(source="detail", default="")
    ipAddress = serializers.CharField(source="ip", default="")
    operateTime = serializers.DateTimeField(source="create_time", format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = OperationLog
        fields = [
            "id", "operatorId", "operatorName", "module", "action",
            "content", "ipAddress", "operateTime",
        ]
