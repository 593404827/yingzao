# 彩画作数字互动平台 · 可迁移初版

这就是当前知识图谱页面的完整项目。前端、后端、数据库、原始快照、修订记录和启动脚本都在这个文件夹中。无需访问原电脑的 Desktop 路径，也不要求安装 Neo4j。

## 1. 启动

先安装 Python 3.10 或以上版本（建议 3.12）。本项目不需要 pip/npm 安装任何第三方包。

- macOS：双击 `start.command`，如执行权限丢失，终端运行 `bash start.command`。
- Windows：双击 `start.bat`。需要 Python 已加入 PATH，或可使用 `py -3`。
- Linux：`bash start.sh`。
- 通用：在项目根目录运行 `python3 run.py`；Windows 可用 `py -3 run.py`。

然后访问 **http://127.0.0.1:18765/**。保持终端窗口打开，按 Ctrl+C 停止。若端口被占用：`python3 run.py --port 18766`，随后访问 18766。

### Docker（可选）

安装 Docker 后，在项目目录执行 `docker compose up --build -d`，仍访问 18765。数据映射在本地 `data/`，停止容器不会丢失数据。Docker 方案需要首次下载基础镜像；普通 Python 启动不需要联网。不要同时启动两个占用同一端口的实例。

## 2. 迁移到其他电脑

1. 在旧电脑执行 `python3 scripts/backup.py`，得到一致性的数据库备份。
2. 停止服务后复制整个 `caihua-platform` 文件夹；或将备份文件在新电脑恢复为 `data/platform.sqlite3`（先停新电脑服务）。
3. 新电脑装 Python 3.10+，使用相应启动脚本即可。
4. `data/platform.sqlite3` 是编辑后的数据；`data/raw/` 是原始快照。两者都要保留。不要只复制 frontend。

数据库不存在时，会从随项目携带的原始快照自动初始化，并应用本轮可追踪修订。已有数据库不会在启动时被原始数据覆盖。

## 3. 文件结构与修改位置

```text
frontend/index.html          页面布局
frontend/style.css           配色、字体、排版
frontend/app.js              图谱绘制、检索交互、实体编辑
frontend/review.html          老师意见与历史问题回查
backend/server.py            HTTP API 与静态文件服务
backend/storage.py           SQLite 数据读写与修订历史
backend/query.py             问题检索、限定语境的路径查询
backend/corrections.py       初始修订规则；原始记录保留
run.py                       跨平台启动入口
scripts/                     备份、HTML 导出、审阅报告、Neo4j 同步
 data/platform.sqlite3       当前数据与历史
 data/raw/                   原始快照（只读来源）
 data/reports/               审阅报告、测试与导出
 tests/                      自动验证
```

页面右侧的“修订此实体”可修改名称、分类和子类，需要填写理由；每次保存保留前后版本。在“复核记录”页面可查看历史。关系可通过 PATCH API 修改或撤回；复杂的属性修订目前需要在数据维护代码/API 扩展中处理，没有伪装成已经具备的属性编辑界面。

修改前端文件后刷新网页；修改 Python 后端后重启服务。新增知识需要导入数据库，不能只改 HTML 里的文字。

## 4. API

| 方法 | 地址 | 用途 |
|---|---|---|
| GET | `/api/status` | 服务/存储状态 |
| GET | `/api/graph` | 有效实体、关系、属性和出处 |
| GET | `/api/search?q=赭笔` | 术语搜索；赭笔作为旧词检索笔与赭 |
| GET | `/api/questions` | 十个预设问题 |
| POST | `/api/query` | `{ "preset": 0, "level": "all" }`；或 `{ "text": "五彩遍装用什么颜色" }` |
| PATCH | `/api/records/node/{id}` | `{ "changes": {"name":"…"}, "reason":"…" }` |
| PATCH | `/api/records/edge/{id}` | 修订关系名称、状态、限定条件或 active |
| GET | `/api/reviews` | 截图关注点及六条类别越界复核与229项历史回查索引 |
| GET | `/api/history` | 修订前后历史 |
| GET | `/api/export` | 包含撤回记录的完整导出 |

后端采用实体名与限定关系路径检索，不是接入大模型的任意语义问答。预设问题依据数据库内容回答，不使用虚构结果。

## 5. 数据审核与本轮修正

原始全文可审阅数据保留1284次实体提及、835条属性、1153条原关系及上轮2条补齐关系。初始化之后再应用本轮修订，当前有效实体/关系数以 `/api/graph` 的 meta 为准，不能拿快照数量当修订后数量。

- “赭笔”不再作为有效工具实体。CH-009、CH-031、CH-045 三处分别表达使用工具“笔”和使用色彩“赭”。原文仍可出现“赭笔”，历史中也保留撤回记录；这不等于错误实体仍有效。未据此推定特定矿物颜料。
- CH-028 保留诸华（纹样）与五彩设色（设色方法），截图里的“诸华间杂”不作为独立技法；对晕技法已存在，本轮再补空缘与外缘道的直接对晕关系。
- 相对尺寸中记录“减”和“三分之一”，但原文/题解的最终比例冲突仍保留待确认，不自行计算出最终比例。
- 两条缘道宽度规定的约束对象落到缘道，构件范围分别保留梁栿/枓栱；撤回把被测缘道误作相对参照对象的关系。
- “已核验”不等于老师终审；未明确确认的候选继续标记候选。65条挂起断言继续保留审阅记录。

另对全文关系做类别一致性回查，6条越界候选标为待确认，详见 `data/reports/关系类别越界_待复核.json`。

详见 `data/reports/老师意见回查.md`。本轮具体审阅赭笔和三张截图的关注点；229项提供可追踪回查索引，**没有声称229项已全部重新完成专家语义核验**。

## 6. Neo4j（可选联动，避免成为迁移前提）

SQLite 是本项目可编辑的数据源；Neo4j 可作为图查询投影，不再要求每台电脑都有原来的 Neo4j 安装目录。原 caihuatest 不变。

- 仅导出投影：`python3 scripts/neo4j_sync.py`
- 同步到已有本机 caihuafull：`python3 scripts/neo4j_sync.py --apply`
- 连接参数从环境变量读取：`NEO4J_HTTP`、`NEO4J_USER`、`NEO4J_PASSWORD`。不在项目写入密码。
- 目标库须提前创建（社区版可按自己的单数据库情况调整并审查脚本）；当前脚本只允许彩画专用的 caihuafull/caihuaplatform，防止误写其他库。
- 同步不删除历史；撤回记录 `active=false`。Neo4j 查询有效知识时加 `active=true` 条件，不要把历史实体当现行知识。

```cypher
MATCH (n:CaihuaEntity)-[r]->(m:CaihuaEntity)
WHERE n.active=true AND m.active=true AND r.active=true
RETURN n,r,m;
```

网页修订后如仍需 Neo4j 演示，重新运行同步脚本。当前不是两库双向自动同步，避免互相覆盖。

## 7. 测试、备份与离线 HTML

```bash
python3 -m unittest discover -s tests -v
python3 scripts/backup.py
python3 scripts/export_html.py
python3 scripts/audit_teacher.py
```

HTML 导出位于 `data/reports/知识图谱_离线修订版.html`，用于演示/分享快照；修订仍应在服务版中保存。复核报告中的当前计数是生成时快照，数据修订后可重新运行 audit_teacher.py。

已在当前 macOS/Python 3.14 环境完成13项自动测试和浏览器操作验证；Windows/Linux 启动脚本和 Docker 配置已提供，尚未在这些系统实际运行，不承诺未经测试的环境零差异。

## 8. 能否继续作为毕设平台？

可以。本版是知识检索和数据维护基础，后续可在不重做数据层的前提下逐步增加纹样拆解、设色层次、图版/实验资源联动、专业与大众两种阅读方式，以及内容核验和使用评价。当前页面是研究原型，不把知识图谱展示本身当成已完成的全部数字互动设计。
