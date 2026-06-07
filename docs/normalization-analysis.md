# AmiyaBot 名词替换插件解析文档

## 对比分析: amiyabot-replace (2.8) vs kkss-advanced-replace (2.2.1)

### 1. amiyabot-replace-2_8 (官方词语替换)

**架构**: 在 `@bot.message_created` 钩子中拦截所有消息，在路由分发前完成文本替换。

**核心替换流程** (main.py:89-114):
```
收到消息 → message_created 钩子
    │
    ├── 1. 查 TextReplace 表: 本群生效 + 全局生效 的规则
    │
    ├── 2. 遍历规则（倒序 reversed）:
    │   ├── 如果 'origin'(目标原名) 已在原文中 → 跳过（不替换）
    │   └── 如果 'replace'(别名) 在原文中 → replace → origin
    │
    ├── 3. 可选: 真名替换（从 PRTS wiki 爬取角色真名表）
    │   └── 真名 → 角色名
    │
    └── 4. data.set_text() 更新消息文本
         → 进入消息路由分发
```

**关键特性**:
- 数据库驱动: `TextReplace` 表 (origin/replace/user_id/group_id/is_active/is_global)
- 基本校验: 检查数字替换词、前缀词冲突、白名单
- 百度内容审核: 通过百度文本审核 API 检查替换词合规性
- 远程同步: 从官方 DEMO 拉取全局替换规则
- 真名替换: 爬取 PRTS wiki 角色真名页面

**数据库模型**:
```python
TextReplace:
    origin: str       # 原名（替换目标）
    replace: str      # 别名（被替换）
    user_id: str      # 提交者
    group_id: str     # 所属群
    is_active: int    # 是否审核通过
    is_global: int    # 是否全局生效
```

### 2. kkss-advanced-replace-2_2_1 (词语替换优化)

**架构**: 增强型别名管理系统，提供智能审核 + 备份管理。

**审核子系统 (checkReplace.py)**:
```
1. init_dict(): 构建游戏数据名称索引
   ├── 干员: name → {name, id}
   ├── 敌人: info.name → {name, id}
   └── 材料: material_name → {name, id}
   所有索引键: remove_punctuation(name).lower()

2. 审核流程:
   ├── legal(): 原名→别名重定向检查 / 别名是否已是原名 / 原名是否存在于游戏数据
   ├── exist(): 别名是否已被其他规则占用
   ├── candidate(): 审核队列中是否已有
   └── custom(): 黑名单/最小长度检查
```

**别名申请流程** (advancedReplace.py:99-207):
```
用户: "阿能 别名 能天使" (通过 addKeyword 配置触发)
    │
    ├── 1. 合法检查 (legal)
    ├── 2. 对象识别 (search_object) → 确定原名是干员/敌人/材料
    ├── 3. 存在检查 (exist)
    ├── 4. 自定义检查 (custom)
    │
    ├── 管理员 → 直接通过 (save_replace)
    └── 普通用户 → 进入审核队列 (save_candidate)
        └── 通知管理员 → @verify_code 通过 / @-verify_code 忽略
```

**备份管理**:
- 备份: `json.dump(TextReplace表)` → .rpbak文件
- 恢复: 合并模式(merge) or 覆盖模式(overwrite)
- 合并: priority_list优先，later_list去重追加

### 3. 应用于 AstrBot Arknights 插件的方案

**目标**: 在消息路由前，将用户输入的昵称/别名/俗名替换为游戏数据中的正式名称。

**设计方案**:

```
AstrBot 消息进入
    │
    ├── 1. 预处理层 (src/normalize.py)
    │   ├── 加载替换表（启动时构建，内存常驻）
    │   │   ├── 干员别名: 阿能→能天使, 小羊→艾雅法拉, ...
    │   │   ├── 别名→原名 正向表（用于路由匹配前）
    │   │   └── 原名→别名 反向表（仅用于查询）
    │   │
    │   ├── normalize(text) → 规范化后文本
    │   │   ├── 1. 去除标点 + 小写化匹配
    │   │   ├── 2. 最长匹配替换（避免 "阿" 误匹配 "阿米娅"）
    │   │   └── 3. 保留原文本其他部分不变
    │   │
    │   └── 替换策略: 与 AmiyaBot 一致
    │       - 如果正式名称已在文本中 → 不替换
    │       - 如果别名在文本中 → 替换为正式名
    │
    └── 2. 路由分发 (现有逻辑)
        └── search_info(normalized_text, ...)
```

**别名字典设计**:
```python
_ALIAS_MAP = {
    "阿能": "能天使",
    "小羊": "艾雅法拉",
    "羊": "艾雅法拉",
    "42": "史尔特尔",
    "银老板": "银灰",
    "推王": "推进之王",
    "黑": "黑",          # 正式名
    "老爷子": "赫拉格",
    ...
}
```

**在 main.py 中集成**:
```python
@filter.command("角色")
async def cmd_character(self, event):
    name = event.message_str.replace("/角色", "").strip()
    normalized = normalize_text(name)     # ← 预处理
    # ... 后续匹配使用 normalized
```

### 4. 两个插件的关键差异总结

| 维度 | amiyabot-replace | kkss-advanced-replace |
|------|:---:|:---:|
| 触发时机 | message_created 钩子 | verify 路由 |
| 数据库 | TextReplace (peewee) | +AdvancedReplaceCandidate/Record |
| 替换方向 | alias → origin | 同 |
| 审核 | 百度 API + 白名单 | 游戏数据合法性检查 + 黑名单 |
| 对象识别 | 无 | 干员/敌人/材料类型识别 |
| 备份 | 无 | .rpbak 文件 + 合并/覆盖 |
| 真名替换 | PRTS wiki 爬取 | 无 |
| 同步 | 远程 console API | 覆盖 amiyabot-replace 的同步 |
