


class Role:
    ADMIN = "admin"
    USER = "user"


class UserStatus:
    NORMAL = "正常"
    DISABLED = "禁用"


class EquipmentStatus:
    """设备状态（7.1 字典）：闲置 / 借出中 / 维修中 / 已报废"""

    IDLE = "闲置"
    BORROWED = "借出中"
    REPAIRING = "维修中"
    SCRAPPED = "已报废"

    ALL = ["闲置", "借出中", "维修中", "已报废"]


class ApprovalStatus:
    """借用审批状态（7.2 字典）"""

    PENDING = "待审批"
    PASSED = "已通过"
    REJECTED = "已驳回"
    CANCELED = "已取消"
    RETURNED = "已归还"

    ALL = ["待审批", "已通过", "已驳回", "已取消", "已归还"]


class OverdueStatus:
    """逾期状态（G12 归 B：定时任务/查询时实时计算，A 只读）"""

    NORMAL = "正常"
    OVERDUE = "已逾期"
    OVERDUE_RETURNED = "逾期已归还"


class ReturnType:
    """确认归还类型（4.3）"""

    NORMAL = "normal"
    DAMAGE = "damage"
    LOSE = "lose"


class AuditResult:
    """审批结果（3.5）"""

    PASS = "pass"
    REJECT = "reject"


class LogModule:
    """操作日志模块（6.1，G9 归 B）"""

    USER = "用户管理"
    EQUIPMENT = "设备管理"
    BORROW = "借用审批"
    RETURN = "归还管理"
    LOGIN = "登录认证"


class LogResult:
    """操作日志结果（G9 归 B）"""

    SUCCESS = "成功"
    FAIL = "失败"
