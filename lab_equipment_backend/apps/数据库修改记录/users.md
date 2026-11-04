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

## 变更 4

- 类型：表删除（重建）
- 修改日期：2026-11-02 20:11:29
- 修改人：767seven
- 说明：按 `sql/schema.sql` 重建本地 `lab_equipment` 库，删除并重建 `users` 表。原 3 条测试用户数据清空，重建前已备份至 `C:\Users\Chen\Desktop\lab_equipment_backup_20261102_200747.sql`

```sql
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `users`;
-- 随后执行 sql/schema.sql 中的 CREATE TABLE `users` ...（结构见该文件）

SET FOREIGN_KEY_CHECKS = 1;
```

## 变更 5

- 类型：字段添加
- 修改日期：2026-11-02 20:11:29
- 修改人：767seven
- 说明：`schema.sql` 的 `users` 表缺少 Django 5.1 `AbstractBaseUser` / `PermissionsMixin` 必需列，导致应用查询报 `Unknown column 'users.last_login'`，补齐以下 4 列

```sql
ALTER TABLE `users`
    ADD COLUMN `last_login`   datetime(6) DEFAULT NULL AFTER `id`,
    ADD COLUMN `is_superuser` tinyint(1) NOT NULL DEFAULT 0 AFTER `last_login`,
    ADD COLUMN `is_active`    tinyint(1) NOT NULL DEFAULT 1,
    ADD COLUMN `is_staff`     tinyint(1) NOT NULL DEFAULT 0;
```

## 变更 6

- 类型：字段修改
- 修改日期：2026-11-02 20:11:29
- 修改人：767seven
- 说明：`schema.sql` 种子密码为裸 bcrypt 格式 `$2b$12$...`，Django 5.1 仅识别带 `bcrypt$` 前缀的格式，导致 `admin123` 校验失败。通过 Django ORM `set_password('admin123')` 重新生成哈希，并将管理员 `is_superuser` / `is_staff` 置为 1

```sql
-- 实际通过 manage.py shell 执行，等价 SQL 形式如下（哈希由 Django 生成）
UPDATE `users`
SET `password`     = 'bcrypt$<django 生成的 bcrypt 哈希>',
    `is_superuser` = 1,
    `is_staff`     = 1
WHERE `user_no` = 'admin';
```
