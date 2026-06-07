# AstrBot Arknights Plugin 调试复盘

> 日期：2026-06-07
> 会话时长：~4 小时
> 根本问题：迁移代码存在大量系统性缺陷，调试过程犯了方法论错误

---

## 一、犯错的根本原因

### 1. 没有先读文档和代码就动手

插件项目有 `docs/SUMMARY.md` 和 `MIGRATION_LOG.md` 详细记录了迁移状态和已知局限，但调试初期完全没有查阅。导致重复发现已知问题、重复修复已修复的 bug。

**教训**：拿到任何项目，第一步永远是读 `docs/`、`README`、`MIGRATION_LOG`。理解「已知什么、缺什么」比「试什么」重要十倍。

### 2. 用"试探性修补"代替"系统性对比"

核心 Bug（`keywords=[]` falsy、`dispatch` 三元组、async generator await）都不是通过对比 AmiyaBot 源码发现的，而是通过日志打点+猜测+反复重启试出来的。整个过程类似随机搜索，浪费了大量 token 和时间。

**正确做法**：拿到报错 → 找到 AmiyaBot 原版对应代码 → 逐行对比 → 发现差异 → 精准修复。一次对比顶十次猜测。

### 3. 做出了不可分发的方案决策

`gamedataPath = 'file:///D:/Documents/projects/Amiya-Bot/'` — 把图片资源路径硬编码为开发机的绝对路径。这是一个完全不可分发的方案，任何其他用户安装此插件都会因路径不存在而渲染失败。

**教训**：做任何方案决策前，先问自己「这个插件会被其他人安装使用吗？」。如果是，方案必须是自包含的（资源在插件目录内、路径是相对路径）。

### 4. 同时修改多个不相关的问题

在同一次 sync 中修改了路由、导入、渲染、性能、数据文件五个维度的问题。导致：
- 无法确定哪个修改解决了哪个问题
- 回滚困难（一个 `git checkout` 丢失了大量修复）
- 排查新 bug 时需要排除的变量过多

**教训**：修改一个维度 → sync → 验证 → 确认无误 → 再改下一个。原子提交，原子测试。

### 5. 测试方法设计错误

用 NapCat 从 bot 向 debug QQ 发送消息作为测试手段。但 bot 发出的消息经过 AstrBot 事件总线时，行为与用户消息不完全一致（命令前缀处理、handler 匹配逻辑有差异）。应该直接用 AstrBot WebUI 的测试面板，或者至少对比验证两种发送方式的行为一致性。

**教训**：测试工具要模拟真实使用场景。不要用一个有差异的间接路径替代直接路径。

### 6. 没有及时更新 skill

Skill 中记录了已知的 pitfall（如 `keywords=[]` falsy、async generator 陷阱），但在实际调试中重复踩坑。Skill 是花钱（token）换来的经验，不加载 = 白花钱。

**教训**：加载 skill 后，先扫描 pitfall 部分，对照当前错误看是否命中已有记录。命中了直接修，没命中才自行排查。

---

## 二、发现的系统性缺陷

### A. `_load_json` 文件名不统一

项目中存在两种命名约定：
- AmiyaBot 原版：部分文件无 `.json` 后缀（如 `skill_table`、`charword_table`）
- 实际文件系统：所有文件均有 `.json` 后缀

`operator_model.py` 中 10 处 `_load_json()` 调用缺少 `.json` 后缀，导致这些文件加载返回空 dict，进而导致：
- 技能数据为空
- 种族/势力/阵营/队伍/生日数据为"未知"
- 声优数据为空
- 基建技能为空
- 模组数据缺失

**根因**：迁移时 AmiyaBot 的资源目录结构与新项目不一致，但代码直接复制了文件名参数，未适配。

### B. 资源图片完全缺失

插件目录的 `data/ArknightsGameResource/` 只包含：
- `gamedata/excel/*.json`（19 个 Excel 数据文件）
- `portrait/`（4 张立绘）

缺失：
- `item/` — 材料图标（~2000 个 png）
- `avatar/` — 干员头像（~1200 个 png）
- `skill/` — 技能图标（~800 个 png）
- `building_skill/` — 基建技能图标（~100 个 png）

HTML 模板通过 `gamedata.js` 中的 `itemIconPath()` / `avatarIconPath()` / `skillIconPath()` 引用这些图片。由于文件不存在，页面中所有图标区域均显示为破损图。

**正确方案**：
1. 从 ArknightsGameResource 仓库下载对应目录到插件 `data/ArknightsGameResource/` 下
2. 修改 `gamedata.js` 中的路径为相对路径（适配插件目录结构）
3. 或者修改 `resource.py` 的下载逻辑，在初始化时自动拉取

### C. `parse_template` 技能数值替换问题

待通过实际数据测试验证根因。初步判断可能是 html_tag_format 的处理顺序或正则细节问题。

---

## 三、具体改进措施

1. **修改任何代码前，先加载 `amiyabot-dev` skill 并阅读 MIGRATION_LOG.md**
2. **每次只改一个问题维度，sync → 重启 → 验证 → 再改下一个**
3. **所有路径引用必须是插件目录内的相对路径，不做任何外部依赖假设**
4. **测试直接用 AstrBot WebUI 测试面板，不通过 NapCat 间接发送**
5. **每完成一个修复，更新 MIGRATION_LOG.md 记录**
