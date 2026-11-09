# 彩画作平台：Neo4j知识存储版

正式知识现在从Neo4j读取和修改，SQLite保留业务历史和旧知识迁移备份，不作为另一份可编辑知识主库。无Neo4j连接时启动明确失败，不悄悄使用旧SQLite数据。

## 启动
本机先启动Neo4j，然后双击start.command，访问http://127.0.0.1:18765/。Python 3.10+，无第三方Python依赖。

复制到其他电脑时，另行安装/启动Neo4j，并复制.env.example为.env修改连接设置。没有Neo4j知识数据时执行python3 scripts/migrate_to_neo4j.py；只有企业版支持脚本的--create-database选项，社区版请使用专用默认库neo4j。首次迁移要求目标库为空，成功后禁止重复运行。

当前仅允许caihuaplatform/caihuafull/neo4j，不要写入其他已有库。原SQLite数据始终保留，数据库备份在项目根backups目录。

## 数据职责
- Neo4j：实体及属性、关系、来源、本次知识修改的前后版本与变更编号。
- SQLite：历史记录、修改任务及执行状态。迁移前records表仅保留用于追溯。
- resources/files：文献图片。当前仅建立目录约定，未提取。

当前已有实体/关系编辑会直接写Neo4j；Neo4j事务成功后写SQLite执行记录。发生错误的任务标记needs_reconciliation，避免无提示回退到旧数据。完整专家审批、agent、影响预览和自动恢复仍待开发。

## 导入与验证
python3 scripts/migrate_to_neo4j.py --create-database
导入后逐字段比对所有实体和关系，报告位于data/reports/neo4j_migration.json。原始快照不修改；候选与待确认状态照原样保留，不代表专家终审。

## 旧同步脚本
Neo4j主库存储模式下scripts/neo4j_sync.py明确拒绝运行，防止旧快照覆盖新知识。

## 测试
CAIHUA_KNOWLEDGE_STORE=sqlite python3 -m unittest discover -s tests -v
此命令用临时SQLite验证原有语义与接口；Neo4j集成验证单独记录，不将SQLite测试冒充Neo4j测试。

## 备份与执行状态恢复
python3 scripts/backup.py 同时备份SQLite及Neo4j知识逻辑快照；图片文件另行复制。
若Neo4j写入已成功但SQLite记录中断，执行python3 scripts/reconcile_knowledge_jobs.py核对变更编号补记。未提交的变更不会自动重放。

## Docker迁移到其他电脑
首次：docker compose up -d neo4j；docker compose run --rm caihua python scripts/migrate_to_neo4j.py；docker compose up -d caihua。后续仅docker compose up -d。不要与本机同端口Neo4j实例同时运行。仅本机端口开放；如部署到远程环境，应配置身份认证。Docker方案尚未在本次环境运行验证。

## GitHub
本地Git已保存迁移前基线与后续变更。GitHub远程仓库尚未创建或推送；建立私有远程后再绑定。
