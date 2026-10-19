# users 表 — 数据库变更记录

## 变更 1

- 类型：表删除（重命名）
- 修改日期：2026-10-19 19:07:36
- 修改人：767seven
- 说明：为对齐《实验室设备借用管理系统_后端API接口文档》与 Navicat SQL 文档，用户表由单数 `user` 重命名为复数 `users`

```sql
RENAME TABLE `user` TO `users`;
```

## 变更 2

- 类型：字段修改
- 修改日期：2026-10-19 19:07:36
- 修改人：767seven
- 说明：`status` 账号状态值由中文改为英文（normal/disabled），与 API 文档枚举定义 10.2 一致

```sql
ALTER TABLE `users`
    MODIFY `status` VARCHAR(10) NOT NULL DEFAULT 'normal'
    COMMENT '账号状态：normal/disabled';

-- 存量数据迁移
UPDATE `users` SET `status` = 'normal'   WHERE `status` = '正常';
UPDATE `users` SET `status` = 'disabled' WHERE `status` = '禁用';
```

## 变更 3

- 类型：字段修改
- 修改日期：2026-10-19 19:07:36
- 修改人：767seven
- 说明：初始化管理员种子数据 `status` 由中文 `正常` 改为英文 `normal`

```sql
UPDATE `users`
SET `status` = 'normal'
WHERE `user_no` = 'admin' AND `status` = '正常';
```
