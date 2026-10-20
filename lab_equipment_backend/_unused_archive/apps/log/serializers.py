"""操作日志 Serializer（6.1，责任人 B）"""
from rest_framework import serializers

from apps.log.models import OperationLog


class OperationLogOutSerializer(serializers.ModelSerializer):
    logId = serializers.IntegerField(source="id")
    operatorId = serializers.IntegerField(source="operator_id", allow_null=True)
    operatorName = serializers.CharField(source="operator_name")
    requestMethod = serializers.CharField(source="request_method")
    requestUrl = serializers.CharField(source="request_url")
    requestParams = serializers.CharField(source="request_params")
    createTime = serializers.DateTimeField(source="create_time", format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = OperationLog
        fields = [
            "logId", "operatorId", "operatorName", "module", "action",
            "requestMethod", "requestUrl", "requestParams", "ip",
            "result", "detail", "createTime",
        ]
