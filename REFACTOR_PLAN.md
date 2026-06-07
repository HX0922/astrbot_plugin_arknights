# AstrBot Arknights Plugin — 严格对齐 AmiyaBot 重构计划

## 目标
将 astrbot_plugin_arknights 的所有功能（除 replace 合并重写外）严格对齐 AmiyaBot 实现。
要求：低耦合、框架层与业务层分离、HTML 渲染完全对齐。

## 架构原则
1. **框架适配层** (`main.py`, `state.py`): 仅处理 AstrBot 事件 → 业务层调用的翻译
2. **业务逻辑层** (`src/*.py`): 完全复刻 AmiyaBot，不依赖任何框架
3. **数据层** (`game_data.py`, `operator_model.py`): 与 AmiyaBot Operator/ArknightsGameData API 完全一致
4. **渲染层** (`render.py`): 对齐 AmiyaBot Chain.html() 行为

## 修复优先级（按依赖）

| # | 模块 | 问题 | 严重 |
|---|------|------|------|
| 1 | operator_info.py | 皮肤过滤列表缺 '精英一'/'精英二' | 🔴 |
| 2 | operator_core.py | FuncsVerify 缺少 level 返回值 | 🔴 |
| 3 | operator_core.py | search_info 多余参数 | 🟡 |
| 4 | operator_data.py | find_operator_module_story 命名 | 🟡 |
| 5 | gacha.py | 完全重写，对齐 gacha_table.json | 🔴 |
| 6 | recruit.py | 完整 OCR 流水线 + 组合计算 | 🔴 |
| 7 | render.py | 对齐 AmiyaBot Chain.html() | 🟡 |
| 8 | enemy.py | get_value 行为对齐 | 🟡 |
| 9 | main.py | 路由结构调整 | 🟡 |

## 第一轮：修复业务逻辑层（低耦合、纯 Python）

### Task 1: operator_info.py — 皮肤过滤修复
- 将 `["初始", "默认"]` → `['初始', '精英一', '精英二']`

### Task 2: operator_core.py — FuncsVerify 签名修复
- level_up: 返回 `(bool, default_level + 2, info)`
- operator: 返回 `(bool, default_level - 1, info)`
- group: 返回 `(bool, default_level + 1, info)`
- search_info: 移除多余参数，改为内部读取
- blockMishap: 保留简化版（框架差异，不影响业务逻辑）

### Task 3: operator_data.py — 命名修复
- `_find_operator_module_story` → `find_operator_module_story`

### Task 4: enemy.py — get_value 对齐
- 移除防御性 else 返回，对齐原版行为

### Task 5: gacha.py — 完全重写
- 读取 gacha_table.json
- 对齐概率递增算法
- 对齐保底机制
- 对齐卡池记录

### Task 6: recruit.py — 完整重写
- find_operator_tags_by_tags
- find_combinations + all_match
- HTML 模板渲染
- OCR 流水线（可选，取决于运行环境）

### Task 7: render.py — 对齐验证
- viewport 1600
- networkidle 等待
- window.init() 注入
- 模板兼容性检查

## 第二轮：框架适配层

### Task 8: main.py — 路由调整
- 适配新的业务层 API

## 记录文件
- `MIGRATION_LOG.md` — 所有修改记录
- 每个 Task 完成后追加详细记录
