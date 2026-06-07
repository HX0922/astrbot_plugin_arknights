     1|# AstrBot Arknights Plugin — 迁移日志
     2|
     3|## 会话开始
     4|- **时间**: 2026-05-31
     5|- **源**: AmiyaBot V6 9个插件
     6|- **目标**: astrbot_plugin_arknights
     7|
     8|---
     9|
    10|## Task 1: operator_info.py 皮肤过滤修复
    11|- **修改**: `["初始", "默认"]` → `["初始", "精英一", "精英二"]`
    12|- **原因**: AmiyaBot 原版过滤这三个默认皮肤，缺失会导致 skins_map 污染
    13|- **文件**: `src/operator_info.py:138`
    14|
    15|## Task 2: operator_core.py FuncsVerify 三元组修复
    16|- **修改**: 
    17|  - level_up 返回 `(bool, default_level + 2, info)`
    18|  - operator 返回 `(bool, default_level - 1, info)` 或 `(False, 0, info)`
    19|  - group 返回 `(bool, default_level + 1, info)` 或 `(False, 0, info)`
    20|  - 新增 `default_level = 8` 模块级常量
    21|  - search_info 移除 `similar_mode` 和 `length_limit` 多余参数
    22|- **原因**: AmiyaBot 原版返回三元组，level 用于路由优先级排序
    23|- **文件**: `src/operator_core.py:156-196`
    24|
    25|## Task 2b: main.py 路由适配三元组
    26|- **修改**: `_Router.dispatch()` 解包三元组 `(verified, level, keypoint)`，按 level 降序排序
    27|- **原因**: 适配 FuncsVerify 新返回格式
    28|- **文件**: `main.py:61-78`
    29|
    30|## Task 3: operator_data.py 方法命名修复
    31|- **修改**: `_find_operator_module_story` → `find_operator_module_story`
    32|- **原因**: 对齐 AmiyaBot 原版命名（无下划线前缀）
    33|- **文件**: `src/operator_data.py:276`
    34|
    35|## Task 4: enemy.py get_value 对齐
    36|- **修改**: 移除防御性 `else: return False, 0` 和 `.get()` 安全访问
    37|- **原因**: 对齐 AmiyaBot 原版行为（数据保证完整性，不处理 KeyError）
    38|- **文件**: `src/enemy.py:168-179`
    39|
    40|## Task 5: gacha.py 完全重写
    41|- **修改**: 完全重写，对齐 AmiyaBot gachaBuilder.py 概率算法
    42|  - rarity_range = {6:2, 5:8, 4:50, 3:40} 百分比分布
    43|  - soft pity: break_even > 50 时六星概率每抽 +2%
    44|  - 十连保底: 至少 1 个五星+
    45|  - 读取 gacha_table.json 获取卡池配置
    46|  - 权重归一化: pickup weight + fillin weight
    47|  - UP 率计算 (`__get_pickup_rate`)
    48|  - `get_rates()` 含水分提升扣除逻辑
    49|- **文件**: `src/gacha.py` (完全重写)
    50|
    51|---
    52|
    53|
## Task 6: recruit.py 完全重写
- **修改**: 完全重写，对齐 AmiyaBot recruit/main.py 算法
  - Recruit.init_tags_list() — jieba 标签词库
  - Recruit.action() — 核心计算流程
  - find_operator_tags_by_tags() — 严格对齐原版
  - find_combinations() — 标签组合生成（1-3标签）
  - all_match() — 检查标签全匹配
- **框架差异**: OCR 流水线暂不实现（平台依赖）
- **文件**: src/recruit.py (完全重写)

## Task 7: render.py 对齐验证
- **确认**: viewport=1600, networkidle, window.init() 注入均已对齐
- **模板**: 13 个 HTML 模板完整，含 operatorRecruit.html
- **文件**: src/render.py (无需修改，已对齐)

