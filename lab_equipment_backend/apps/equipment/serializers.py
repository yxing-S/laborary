"""设备模块 Serializer（对齐《后端API接口文档》四、五章，责任人 A）

出入参统一 camelCase，通过 source= 映射蛇形列名（数据库结构不变）。
"""
from datetime import date

from rest_framework import serializers

from apps.common.constants import EquipmentStatus
from apps.equipment.models import Equipment


# ================= 请求 Serializer =================

class EquipmentAddSerializer(serializers.ModelSerializer):
    """4.1 管理员新增设备"""

    equipmentNo = serializers.CharField(source="equipment_no", min_length=3, max_length=30)
    name = serializers.CharField(min_length=2, max_length=50)
    model = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    spec = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    buyDate = serializers.DateField(source="buy_date", required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0,
                                     required=False, allow_null=True)
    location = serializers.CharField(min_length=2, max_length=50)
    status = serializers.ChoiceField(choices=EquipmentStatus.ALL, default=EquipmentStatus.IDLE)
    imgUrl = serializers.CharField(source="img_url", max_length=255, required=False,
                                   allow_blank=True, default="")
    remark = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    class Meta:
        model = Equipment
        fields = ["equipmentNo", "name", "model", "spec", "buyDate",
                  "price", "location", "status", "imgUrl", "remark"]

    def validate_buyDate(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("购置日期不能是未来")
        return value

    def validate_status(self, value):
        # “借出中”只能由借还流转（B 域）变更，新增设备不允许直接置为 borrowed
        if value == EquipmentStatus.BORROWED:
            raise serializers.ValidationError("新增设备不允许置为借出中")
        return value


class EquipmentUpdateSerializer(serializers.ModelSerializer):
    """4.2 管理员编辑设备（equipmentNo 不可修改）"""

    name = serializers.CharField(min_length=2, max_length=50, required=False)
    model = serializers.CharField(max_length=50, required=False, allow_blank=True)
    spec = serializers.CharField(max_length=200, required=False, allow_blank=True)
    buyDate = serializers.DateField(source="buy_date", required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0,
                                     required=False, allow_null=True)
    location = serializers.CharField(min_length=2, max_length=50, required=False)
    status = serializers.ChoiceField(choices=EquipmentStatus.ALL, required=False)
    imgUrl = serializers.CharField(source="img_url", max_length=255, required=False,
                                   allow_blank=True)
    remark = serializers.CharField(max_length=500, required=False, allow_blank=True)

    class Meta:
        model = Equipment
        fields = ["name", "model", "spec", "buyDate", "price",
                  "location", "status", "imgUrl", "remark"]

    def validate_buyDate(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("购置日期不能是未来")
        return value


# ================= 响应 Serializer =================

class BorrowHistorySerializer(serializers.Serializer):
    """4.5 / 5.2 历史借用记录单项（跨域只读 B 的 borrow_records，related_name=borrow_records）"""

    id = serializers.IntegerField()
    userName = serializers.CharField(source="user.name", default="")
    userNo = serializers.CharField(source="user.user_no", default="")
    planBorrowStart = serializers.DateTimeField(
        source="plan_borrow_start", format="%Y-%m-%d %H:%M:%S"
    )
    planReturnTime = serializers.DateTimeField(
        source="plan_return_time", format="%Y-%m-%d %H:%M:%S"
    )
    actualReturnTime = serializers.DateTimeField(
        source="actual_return_time", format="%Y-%m-%d %H:%M:%S",
        allow_null=True, required=False,
    )
    approvalStatus = serializers.CharField(source="approval_status")
    overdueStatus = serializers.CharField(source="overdue_status")


def _get_borrow_history(obj):
    """设备历史借用记录（跨域只读 B 的表，最多返回最近 50 条）"""
    records = obj.borrow_records.select_related("user").order_by("-id")[:50]
    return BorrowHistorySerializer(records, many=True).data


class EquipmentAdminSerializer(serializers.ModelSerializer):
    """4.4 管理员设备列表单项"""

    equipmentNo = serializers.CharField(source="equipment_no")
    buyDate = serializers.DateField(source="buy_date")
    imgUrl = serializers.CharField(source="img_url")
    isDeleted = serializers.BooleanField(source="is_deleted")
    createTime = serializers.DateTimeField(source="create_time", format="%Y-%m-%d %H:%M:%S")
    updateTime = serializers.DateTimeField(source="update_time", format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Equipment
        fields = ["id", "equipmentNo", "name", "model", "spec", "buyDate", "price",
                  "location", "status", "imgUrl", "remark", "isDeleted",
                  "createTime", "updateTime"]


class EquipmentAdminDetailSerializer(EquipmentAdminSerializer):
    """4.5 管理员设备详情：基础字段 + 历史借用记录"""

    borrowHistory = serializers.SerializerMethodField()

    class Meta(EquipmentAdminSerializer.Meta):
        fields = EquipmentAdminSerializer.Meta.fields + ["borrowHistory"]

    def get_borrowHistory(self, obj):
        return _get_borrow_history(obj)


class EquipmentBrowseSerializer(serializers.ModelSerializer):
    """5.1 设备列表单项（公开浏览）"""

    equipmentNo = serializers.CharField(source="equipment_no")
    imgUrl = serializers.CharField(source="img_url")
    canBorrow = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = ["id", "equipmentNo", "name", "model", "location",
                  "status", "imgUrl", "canBorrow"]

    def get_canBorrow(self, obj):
        return obj.status == EquipmentStatus.IDLE and not obj.is_deleted


class EquipmentBrowseDetailSerializer(serializers.ModelSerializer):
    """5.2 设备详情（公开）：完整参数 + canBorrow + borrowHistory"""

    equipmentNo = serializers.CharField(source="equipment_no")
    buyDate = serializers.DateField(source="buy_date")
    imgUrl = serializers.CharField(source="img_url")
    canBorrow = serializers.SerializerMethodField()
    borrowHistory = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = ["id", "equipmentNo", "name", "model", "spec", "buyDate", "price",
                  "location", "status", "imgUrl", "remark", "canBorrow", "borrowHistory"]

    def get_canBorrow(self, obj):
        return obj.status == EquipmentStatus.IDLE and not obj.is_deleted

    def get_borrowHistory(self, obj):
        return _get_borrow_history(obj)
