"""借用模块 Serializer（对齐《后端API接口文档》六、七章）

请求 Serializer 用 camelCase + source 映射，响应 Serializer 显式声明字段。
"""
from rest_framework import serializers

from apps.borrow.models import BorrowRecord
from apps.common.constants import AuditAction, ReturnType


# ===================== 请求 Serializer =====================

class BorrowApplySerializer(serializers.Serializer):
    """6.1 提交借用申请"""

    equipmentId = serializers.IntegerField(min_value=1)
    borrowPurpose = serializers.CharField(min_length=2, max_length=100)
    planBorrowStart = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M:%S"])
    planReturnTime = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M:%S"])
    remark = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        from django.utils import timezone

        now = timezone.now()
        if attrs["planBorrowStart"] < now:
            raise serializers.ValidationError("借用开始时间不能早于当前时间")
        if attrs["planReturnTime"] <= attrs["planBorrowStart"]:
            raise serializers.ValidationError("计划归还时间必须晚于借用开始时间")
        return attrs


class BorrowApprovalSerializer(serializers.Serializer):
    """6.5 审批借用申请"""

    action = serializers.ChoiceField(choices=[AuditAction.APPROVE, AuditAction.REJECT])
    comment = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["action"] == AuditAction.REJECT and not attrs.get("comment", "").strip():
            raise serializers.ValidationError("驳回时必须填写审批意见")
        return attrs


class ReturnApplySerializer(serializers.Serializer):
    """7.1 发起归还申请"""

    borrowRecordId = serializers.IntegerField(min_value=1)


class ReturnConfirmSerializer(serializers.Serializer):
    """7.3 确认归还"""

    returnType = serializers.ChoiceField(
        choices=[ReturnType.NORMAL, ReturnType.DAMAGED, ReturnType.LOST]
    )
    damageDesc = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["returnType"] in (ReturnType.DAMAGED, ReturnType.LOST) and not attrs.get("damageDesc", "").strip():
            raise serializers.ValidationError("损坏/丢失时必须填写说明")
        return attrs


# ===================== 响应 Serializer =====================

class BorrowRecordOutSerializer(serializers.ModelSerializer):
    """借用记录输出（我的申请/待审批/总览通用）"""

    id = serializers.IntegerField(read_only=True)
    applicationNo = serializers.SerializerMethodField()
    equipmentId = serializers.IntegerField(source="equipment_id")
    equipmentName = serializers.CharField(source="equipment.name", default="")
    equipmentNo = serializers.CharField(source="equipment.equipment_no", default="")
    userId = serializers.IntegerField(source="user_id")
    userName = serializers.CharField(source="user.name", default="")
    userNo = serializers.CharField(source="user.user_no", default="")
    borrowPurpose = serializers.CharField(source="borrow_purpose")
    planBorrowStart = serializers.DateTimeField(source="plan_borrow_start", format="%Y-%m-%d %H:%M:%S")
    planReturnTime = serializers.DateTimeField(source="plan_return_time", format="%Y-%m-%d %H:%M:%S")
    actualReturnTime = serializers.DateTimeField(
        source="actual_return_time", format="%Y-%m-%d %H:%M:%S", allow_null=True, required=False
    )
    approvalStatus = serializers.CharField(source="approval_status")
    approvalComment = serializers.CharField(source="approval_comment", default="")
    overdueStatus = serializers.CharField(source="overdue_status")
    applyTime = serializers.DateTimeField(source="create_time", format="%Y-%m-%d %H:%M:%S")
    remark = serializers.CharField(source="remark", default="")

    def get_applicationNo(self, obj):
        return f"APP{obj.id:06d}"

    class Meta:
        model = BorrowRecord
        fields = [
            "id", "applicationNo", "equipmentId", "equipmentName", "equipmentNo",
            "userId", "userName", "userNo", "borrowPurpose",
            "planBorrowStart", "planReturnTime", "actualReturnTime",
            "approvalStatus", "approvalComment", "overdueStatus", "applyTime", "remark",
        ]


class ReturnApplicationOutSerializer(serializers.ModelSerializer):
    """7.2 待归还列表输出（applyTime = 归还申请时间）"""

    id = serializers.IntegerField(read_only=True)
    borrowRecordId = serializers.IntegerField(source="id")
    applicationNo = serializers.SerializerMethodField()
    equipmentId = serializers.IntegerField(source="equipment_id")
    equipmentName = serializers.CharField(source="equipment.name", default="")
    equipmentNo = serializers.CharField(source="equipment.equipment_no", default="")
    userId = serializers.IntegerField(source="user_id")
    userName = serializers.CharField(source="user.name", default="")
    userNo = serializers.CharField(source="user.user_no", default="")
    planReturnTime = serializers.DateTimeField(source="plan_return_time", format="%Y-%m-%d %H:%M:%S")
    overdueStatus = serializers.CharField(source="overdue_status")
    applyTime = serializers.DateTimeField(
        source="return_apply_time", format="%Y-%m-%d %H:%M:%S", allow_null=True, required=False
    )

    def get_applicationNo(self, obj):
        return f"APP{obj.id:06d}"

    class Meta:
        model = BorrowRecord
        fields = [
            "id", "borrowRecordId", "applicationNo", "equipmentId", "equipmentName",
            "equipmentNo", "userId", "userName", "userNo",
            "planReturnTime", "overdueStatus", "applyTime",
        ]
