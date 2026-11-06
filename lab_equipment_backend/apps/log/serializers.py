"""操作日志 Serializer（对齐《后端API接口文档》9.1，责任人 B）

响应 data.list 单项字段：
id / operatorId / operatorName / module / action / content / ipAddress / operateTime
"""
from rest_framework import serializers

from apps.log.models import OperationLog


class OperationLogOutSerializer(serializers.ModelSerializer):
    operatorId = serializers.IntegerField(source="operator_id", allow_null=True)
    operatorName = serializers.CharField(source="operator_name", default="")
    content = serializers.SerializerMethodField()
    ipAddress = serializers.CharField(source="ip", default="")
    operateTime = serializers.DateTimeField(source="create_time", format="%Y-%m-%d %H:%M:%S")

    # 登录接口的 action 为前端筛选码 login，展示时转中文
    _ACTION_TEXT = {"login": "用户登录"}

    def get_content(self, obj):
        """操作内容取行为名；失败时附带原因，便于前端日志页展示"""
        action_text = self._ACTION_TEXT.get(obj.action, obj.action)
        if obj.detail and obj.result != "成功":
            return f"{action_text}（{obj.detail}）"
        return action_text

    class Meta:
        model = OperationLog
        fields = [
            "id", "operatorId", "operatorName", "module", "action",
            "content", "ipAddress", "operateTime",
        ]
