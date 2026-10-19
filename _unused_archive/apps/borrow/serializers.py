"""借用模块 Serializer（接口 3.1 - 5.4，责任人 B）

统一沿用现有风格：请求 Serializer 用 camelCase + source 映射，
响应 Serializer 显式声明字段 + 统一时间格式。
"""
from rest_framework import serializers

from apps.borrow.models import BorrowRecord
from apps.common.constants import AuditResult, ReturnType


# ===================== 请求 Serializer =====================

class BorrowApplySerializer(serializers.Serializer):
    """3.1 提交借用申请"""

    equipmentId = serializers.IntegerField(min_value=1)
    planBorrowStart = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M:%S"])
    planReturnTime = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M:%S"])
    borrowPurpose = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    remark = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        from django.utils import timezone

        now = timezone.now()
        if attrs["planBorrowStart"] < now:
            raise serializers.ValidationError("借用开始时间不能早于当前时间")
        if attrs["planReturnTime"] <= attrs["planBorrowStart"]:
            raise serializers.ValidationError("计划归还时间必须晚于借用开始时间")
        return attrs


class BorrowAuditSerializer(serializers.Serializer):
    """3.5 审批借用申请"""

    auditResult = serializers.ChoiceField(choices=[AuditResult.PASS, AuditResult.REJECT])
    approvalComment = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["auditResult"] == AuditResult.REJECT and not attrs.get("approvalComment", "").strip():
            raise serializers.ValidationError("驳回时必须填写审批意见")
        return attrs


class ReturnConfirmSerializer(serializers.Serializer):
    """4.3 确认归还"""

    returnType = serializers.ChoiceField(
        choices=[ReturnType.NORMAL, ReturnType.DAMAGE, ReturnType.LOSE]
    )
    damageDesc = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


# ===================== 响应 Serializer =====================

class BorrowRecordOutSerializer(serializers.ModelSerializer):
    """借用记录输出（列表 / 详情通用）"""

    recordId = serializers.IntegerField(source="id")
    userId = serializers.IntegerField(source="user_id")
    userName = serializers.CharField(source="user.name", default="")
    userNo = serializers.CharField(source="user.user_no", default="")
    equipmentId = serializers.IntegerField(source="equipment_id")
    equipmentNo = serializers.CharField(source="equipment.equipment_no", default="")
    equipmentName = serializers.CharField(source="equipment.name", default="")
    planBorrowStart = serializers.DateTimeField(source="plan_borrow_start", format="%Y-%m-%d %H:%M:%S")
    planReturnTime = serializers.DateTimeField(source="plan_return_time", format="%Y-%m-%d %H:%M:%S")
    borrowPurpose = serializers.CharField(source="borrow_purpose")
    remark = serializers.CharField()
    approvalStatus = serializers.CharField(source="approval_status")
    approvalComment = serializers.CharField(source="approval_comment")
    auditorName = serializers.CharField(source="auditor.name", default="")
    auditTime = serializers.DateTimeField(source="audit_time", format="%Y-%m-%d %H:%M:%S")
    cancelTime = serializers.DateTimeField(source="cancel_time", format="%Y-%m-%d %H:%M:%S")
    returnApplyTime = serializers.DateTimeField(source="return_apply_time", format="%Y-%m-%d %H:%M:%S")
    actualReturnTime = serializers.DateTimeField(source="actual_return_time", format="%Y-%m-%d %H:%M:%S")
    returnType = serializers.CharField(source="return_type")
    damageDesc = serializers.CharField(source="damage_desc")
    overdueStatus = serializers.CharField(source="overdue_status")
    createTime = serializers.DateTimeField(source="create_time", format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = BorrowRecord
        fields = [
            "recordId", "userId", "userName", "userNo",
            "equipmentId", "equipmentNo", "equipmentName",
            "planBorrowStart", "planReturnTime", "borrowPurpose", "remark",
            "approvalStatus", "approvalComment", "auditorName", "auditTime",
            "cancelTime", "returnApplyTime", "actualReturnTime",
            "returnType", "damageDesc", "overdueStatus", "createTime",
        ]
