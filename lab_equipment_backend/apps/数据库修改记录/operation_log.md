# operation_log 表 — 数据库变更记录

## 变更 1

- 类型：表删除（重建）
- 修改日期：2026-11-02 20:11:29
- 修改人：767seven
- 说明：按 `sql/schema.sql` 重建本地 `lab_equipment` 库，删除并重建 `operation_log` 表。原 97 条操作日志清空，重建前已备份至 `C:\Users\Chen\Desktop\lab_equipment_backup_20261102_200747.sql`

```sql
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `operation_log`;
-- 随后执行 sql/schema.sql 中的 CREATE TABLE `operation_log` ...（结构见该文件）

SET FOREIGN_KEY_CHECKS = 1;
```
