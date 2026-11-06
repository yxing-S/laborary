"""借用模块 Serializer（对齐《后端API接口文档》六、七章）

请求 Serializer 用 camelCase + source 映射，响应 Serializer 显式声明字段。
"""
import math

from django.utils import timezone
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
        comment = attrs.get("comment", "").strip()
        if attrs["action"] == AuditAction.REJECT and len(comment) < 2:
            raise serializers.ValidationError("驳回时必须填写 2-200 字的审批意见")
        return attrs


class ReturnApplySerializer(serializers.Serializer):
    """7.1 发起归还申请"""

    borrowRecordId = serializers.IntegerField(min_value=1)


# 前端页面使用 damage/lose，接口文档定义为 damaged/lost，两者都接受
_RETURN_TYPE_ALIASES = {"damage": ReturnType.DAMAGED, "lose": ReturnType.LOST}


class ReturnConfirmSerializer(serializers.Serializer):
    """7.3 确认归还"""

    returnType = serializers.ChoiceField(
        choices=[
            ReturnType.NORMAL, ReturnType.DAMAGED, ReturnType.LOST,
            "damage", "lose",
        ]
    )
    damageDesc = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    def validate_returnType(self, value):
        return _RETURN_TYPE_ALIASES.get(value, value)

    def validate(self, attrs):
        desc = attrs.get("damageDesc", "").strip()
        if attrs["returnType"] in (ReturnType.DAMAGED, ReturnType.LOST) and len(desc) < 2:
            raise serializers.ValidationError("损坏/丢失时必须填写 2-500 字的说明")
        return attrs


# 这两个接口前端未做状态码转中文适配，直接返回中文展示值
_OVERDUE_TEXT = {
    "normal": "正常",
    "overdue": "已逾期",
    "overdue_returned": "逾期已归还",
}


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
    returnApplyTime = serializers.DateTimeField(
        source="return_apply_time", format="%Y-%m-%d %H:%M:%S", allow_null=True, required=False
    )
    returnType = serializers.CharField(source="return_type", default="")
    damageDesc = serializers.CharField(source="damage_desc", default="")
    department = serializers.CharField(source="user.department", default="")
    approvalStatus = serializers.CharField(source="approval_status")
    approvalComment = serializers.CharField(source="approval_comment", default="")
    overdueStatus = serializers.CharField(source="overdue_status")
    applyTime = serializers.DateTimeField(source="create_time", format="%Y-%m-%d %H:%M:%S")
    remark = serializers.CharField(default="")

    def get_applicationNo(self, obj):
        return f"APP{obj.id:06d}"

    class Meta:
        model = BorrowRecord
        fields = [
            "id", "applicationNo", "equipmentId", "equipmentName", "equipmentNo",
            "userId", "userName", "userNo", "department", "borrowPurpose",
            "planBorrowStart", "planReturnTime", "actualReturnTime", "returnApplyTime",
            "returnType", "damageDesc",
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
    department = serializers.CharField(source="user.department", default="")
    planBorrowStart = serializers.DateTimeField(
        source="plan_borrow_start", format="%Y-%m-%d %H:%M:%S"
    )
    planReturnTime = serializers.DateTimeField(source="plan_return_time", format="%Y-%m-%d %H:%M:%S")
    overdueStatus = serializers.SerializerMethodField()
    applyTime = serializers.DateTimeField(
        source="return_apply_time", format="%Y-%m-%d %H:%M:%S", allow_null=True, required=False
    )

    def get_overdueStatus(self, obj):
        return _OVERDUE_TEXT.get(obj.overdue_status, obj.overdue_status)

    def get_applicationNo(self, obj):
        return f"APP{obj.id:06d}"

    class Meta:
        model = BorrowRecord
        fields = [
            "id", "borrowRecordId", "applicationNo", "equipmentId", "equipmentName",
            "equipmentNo", "userId", "userName", "userNo", "department",
            "planBorrowStart", "planReturnTime", "overdueStatus", "applyTime",
        ]


class OverdueRecordOutSerializer(serializers.ModelSerializer):
    """8.3 逾期记录统计单项"""

    borrowRecordId = serializers.IntegerField(source="id")
    userId = serializers.IntegerField(source="user_id")
    userName = serializers.CharField(source="user.name", default="")
    userNo = serializers.CharField(source="user.user_no", default="")
    department = serializers.CharField(source="user.department", default="")
    equipmentName = serializers.CharField(source="equipment.name", default="")
    equipmentNo = serializers.CharField(source="equipment.equipment_no", default="")
    planBorrowStart = serializers.DateTimeField(
        source="plan_borrow_start", format="%Y-%m-%d %H:%M:%S"
    )
    planReturnTime = serializers.DateTimeField(source="plan_return_time", format="%Y-%m-%d %H:%M:%S")
    actualReturnTime = serializers.DateTimeField(
        source="actual_return_time", format="%Y-%m-%d %H:%M:%S", allow_null=True, required=False
    )
    returnType = serializers.CharField(source="return_type", default="")
    damageDesc = serializers.CharField(source="damage_desc", default="")
    overdueStatus = serializers.SerializerMethodField()
    overdueDays = serializers.SerializerMethodField()
    approvalStatus = serializers.CharField(source="approval_status")

    def get_overdueStatus(self, obj):
        return _OVERDUE_TEXT.get(obj.overdue_status, obj.overdue_status)

    def get_overdueDays(self, obj):
        """逾期天数：已归还按实际归还时间算，未归还按当前时间算"""
        end = obj.actual_return_time or timezone.now()
        return max(1, math.ceil((end - obj.plan_return_time).total_seconds() / 86400))

    class Meta:
        model = BorrowRecord
        fields = [
            "borrowRecordId", "userId", "userName", "userNo", "department",
            "equipmentName", "equipmentNo", "planBorrowStart", "planReturnTime",
            "actualReturnTime", "returnType", "damageDesc", "overdueStatus",
            "overdueDays", "approvalStatus",
        ]
