# borrow_records 表 — 数据库变更记录

## 变更 1

- 类型：表删除（重命名）
- 修改日期：2026-10-19 19:07:36
- 修改人：767seven
- 说明：借用记录表由单数 `borrow_record` 重命名为复数 `borrow_records`，对齐 Navicat SQL 文档

```sql
RENAME TABLE `borrow_record` TO `borrow_records`;
```

## 变更 2

- 类型：字段修改
- 修改日期：2026-10-19 19:07:36
- 修改人：767seven
- 说明：`approval_status` 审批状态值由中文改为英文（pending/approved/rejected/returned/cancelled），与 API 文档枚举定义 10.4 一致

```sql
ALTER TABLE `borrow_records`
    MODIFY `approval_status` VARCHAR(20) NOT NULL DEFAULT 'pending'
    COMMENT '审批状态：pending/approved/rejected/returned/cancelled';

-- 存量数据迁移
UPDATE `borrow_records` SET `approval_status` = 'pending'   WHERE `approval_status` = '待审批';
UPDATE `borrow_records` SET `approval_status` = 'approved'  WHERE `approval_status` = '已通过';
UPDATE `borrow_records` SET `approval_status` = 'rejected'  WHERE `approval_status` = '已驳回';
UPDATE `borrow_records` SET `approval_status` = 'returned'  WHERE `approval_status` = '已归还';
UPDATE `borrow_records` SET `approval_status` = 'cancelled' WHERE `approval_status` = '已取消';
```

## 变更 3

- 类型：字段修改
- 修改日期：2026-10-19 19:07:36
- 修改人：767seven
- 说明：`overdue_status` 逾期状态值由中文改为英文（normal/overdue/overdue_returned），与 API 文档枚举定义 10.5 一致

```sql
ALTER TABLE `borrow_records`
    MODIFY `overdue_status` VARCHAR(20) NOT NULL DEFAULT 'normal'
    COMMENT '逾期状态：normal/overdue/overdue_returned';

-- 存量数据迁移
UPDATE `borrow_records` SET `overdue_status` = 'normal'           WHERE `overdue_status` = '正常';
UPDATE `borrow_records` SET `overdue_status` = 'overdue'          WHERE `overdue_status` = '已逾期';
UPDATE `borrow_records` SET `overdue_status` = 'overdue_returned' WHERE `overdue_status` = '逾期已归还';
```

## 变更 4

- 类型：字段修改
- 修改日期：2026-10-19 19:07:36
- 修改人：767seven
- 说明：`return_type` 归还类型值域由 `normal/damage/lose` 改为 `normal/damaged/lost`，与 API 文档枚举定义 10.6 一致

```sql
ALTER TABLE `borrow_records`
    MODIFY `return_type` VARCHAR(20) DEFAULT NULL
    COMMENT '归还类型：normal/damaged/lost';

-- 存量数据迁移
UPDATE `borrow_records` SET `return_type` = 'damaged' WHERE `return_type` = 'damage';
UPDATE `borrow_records` SET `return_type` = 'lost'    WHERE `return_type` = 'lose';
```
