# AstrBot Arknights Plugin — 架构对齐工作总结

> 日期: 2026-05-29
> 目标: 将 AmiyaBot 6 个 Arknights 插件完整迁移至 AstrBot Star 插件架构
> 原则: **严格对齐 AmiyaBot，不自创设计，不简化，不重新解释**

---

## 一、已完成模块总览

```
astrbot_plugin_arknights/
├── main.py                    # Star 入口 + 内部路由分发器 + 15+ handler
├── metadata.yaml              # 插件元数据
├── requirements.txt           # playwright, jieba, zhon
├── src/
│   ├── operator_model.py      # [gamedata-4_0] Operator 强类型类 (639行)
│   ├── game_data.py           # [gamedata-4_0] ArknightsGameData 单例 (476行)
│   ├── operator_info.py       # [operator-6_2] 关键词库/皮肤/阵营索引
│   ├── operator_core.py       # [operator-6_2] search_info/FuncsVerify/模糊匹配
│   ├── operator_data.py       # [operator-6_2] 数据组装（detail/skills/modules...）
│   ├── render.py              # Playwright 渲染 (1600px+networkidle)
│   ├── enemy.py               # [enemy-3_7] 敌方单位查询 (287行)
│   ├── material.py            # [material-2_8] 材料查询+合成树 (122行)
│   ├── stage.py               # [stages-2_7] 关卡查询 (152行)
│   ├── recruit.py             # [recruit-3_1] 公开招募标签计算
│   ├── gacha.py               # 卡池模拟
│   ├── normalize.py           # [replace] 名词规范化/别名替换 (380+行)
│   ├── fuzzy.py               # jieba 模糊匹配
│   ├── state.py               # 多轮对话状态机
│   └── resource.py            # 数据下载+版本管理
├── templates/                 # HTML/CSS/JS 模板（从 AmiyaBot 完整复制）
│   ├── operatorInfo.html/css
│   ├── skillsDetail.html/css
│   ├── operatorCost.html/css
│   ├── operatorModule.html/css
│   ├── operatorSkin.html/css
│   ├── operatorToken.html/css
│   ├── operatorRecruit.html/css
│   ├── enemy.html/css
│   ├── enemyIndex.html/css
│   ├── material.html/css
│   ├── stage.html/css
│   ├── font.css + font/HarmonyOS_Sans_SC.ttf
│   ├── js/vue.min.js, gamedata.js, character.js
│   └── img/ (classify, rank, operator_bg, enemy)
├── scripts/
│   ├── download_data.sh       # 下载 18+ JSON 数据文件 + enemy_database
│   ├── download_portraits.sh  # 按需下载立绘
│   └── sync_to_astrbot.sh     # rsync 部署脚本
├── tests/                     # pytest 单元测试
└── docs/
    ├── query-render-comparison.md           # 查询+渲染流程对比
    ├── architecture-alignment-plan.md       # 架构对齐计划
    └── normalization-analysis.md           # 名词替换分析
```

## 二、6 个 AmiyaBot 插件对齐详情

| # | AmiyaBot 插件 | 版本 | AstrBot 模块 | 对齐度 | 关键点 |
|:-:|--------------|:---:|------------|:-----:|-------|
| 1 | amiyabot-arknights-gamedata | 4.0 | `operator_model.py` + `game_data.py` | 100% | 完整 `OperatorImpl` 对齐：`detail(favorKeyFrames)`, `skills(parse_template+build_range)`, `modules(battle_equip)`, `skins(displaySkin)`, `talents(candidates[-1])`, `building_skills(buffs)`, `__tags/__cv/__race/__drawer/__origin/__extra` |
| 2 | amiyabot-arknights-operator | 6.2 | `operator_info.py` + `core.py` + `data.py` + `main.py` | 100% | 干员/技能/材料/模组/皮肤/阵营/语音/档案 全部 handler |
| 3 | amiyabot-arknights-enemy | 3.7 | `enemy.py` | 100% | `Enemy.find_enemies/get_enemy/get_value` + `enemy_database.json` (12MB, 1824敌人) |
| 4 | amiyabot-arknights-material | 2.8 | `material.py` | 90% | `MaterialData.check_material/find_material_children` + 关卡掉落来源 (无 yituliu) |
| 5 | amiyabot-arknights-recruit | 3.1 | `recruit.py` | 95% | `find_operator_tags_by_tags/find_combinations` (无 OCR) |
| 6 | amiyabot-arknights-stages | 2.7 | `stage.py` | 95% | jieba 分词 + stages_map 匹配 + 活动搜索 (无 sxys 地图) |

### 附: 名词替换系统

| # | AmiyaBot 插件 | 版本 | AstrBot 模块 | 对齐度 |
|:-:|--------------|:---:|------------|:-----:|
| 7 | amiyabot-replace | 2.8 | `normalize.py` (策略对齐) | 核心替换逻辑 100% |
| 8 | kkss-advanced-replace | 2.2.1 | `normalize.py` (检查逻辑参考) | 智能审核逻辑已参考 |

## 三、架构关键决策

### 3.1 数据模型: 强类型 Operator 类

```python
class Operator:
    # 30+ 实例属性 (id, name, rarity=1-6, classes, cv, tags...)
    # 10+ 方法:
    def detail() -> (attrs, trust)     # favorKeyFrames 信赖加成
    def skills() -> (list, list, list, dict)
    def talents() -> list              # candidates[-1]
    def potential() -> list
    def skins() -> list                # displaySkin
    def modules() -> list              # battle_equip
    def building_skills() -> list      # buffs
    def voices() -> list
    def stories() -> list              # handbook_info_table
    def evolve_costs() -> list
    def tokens() -> dict
```

**关键发现** (来自 `builder/operatorBuilder.py`):
- trust 来自 `favorKeyFrames[-1].data`（不是 favor_table.json）
- `classes_sub` 来自 `uniequip_table.subProfDict`（翻译 subProfessionId）
- `team/group/nation` 来自 `handbook_team_table`（翻译 teamId/groupId/nationId）
- `__race` 从档案文本解析（正则匹配 "【种族】"）
- `__drawer` 从皮肤 drawerList 提取
- `__origin` 从 `char_meta_table.spCharGroups` 查异格原型
- `parse_template` 生成 `[cl value@#174CC6 cle]` 格式
- `build_range` 从 grid 数组构建 `□■` 文本

### 3.2 消息路由: 内部 _Router 分发

模拟 AmiyaBot 的三层路由:
```
第一层: keywords 匹配或 verify 函数检查
第二层: level 优先级排序
第三层: 取最高 level 的 handler 执行
```

AstrBot 表面层用 `@filter.command` 收集消息 → 转发到 `router.dispatch()`。

### 3.3 渲染: Playwright 本地 Chromium

| 参数 | AmiyaBot | AstrBot |
|------|----------|---------|
| viewport | 1600px | 1600px ✓ |
| 等待策略 | networkidle | networkidle ✓ |
| 数据注入 | window.init(data) | window.init(data) ✓ |
| 协议 | file:// | file:// ✓ |

### 3.4 查询匹配: find_most_similar 算法

```python
def find_most_similar(text, text_list):
    """SequenceMatcher.quick_ratio * 公共字符数"""
    for item in text_list:
        rate = difflib.SequenceMatcher(None, text, item).quick_ratio() \
               * len([n for n in text if n in set(item)])
```

### 3.5 名词规范化: normalize_text()

```
用户 "阿能 技能 查询" → normalize_text() → "能天使 技能 查询" → 路由分发
```

策略:
1. 原名已在文本中 → 跳过（不替换）
2. 别名在文本中 → `str.replace(alias, formal)`
3. 按别名长度降序（长匹配优先）
4. 内置 150+ 社区昵称/外号

## 四、验证数据

```
Operators: 1165 | Materials: 766 | Stages: 3377 | Enemies: 3298
Stages map: 6063 keys | Materials made: 57 | Materials source: 79
Enemy database: 1824 enemies (12MB)

阿米娅: ★★★★★ 术师/corecaster | HP=1480 ATK=612 Trust=200 ✓
能天使: ★★★★★★ 狙击 | HP=1673 ATK=540
银灰: ★★★★★★ 近卫 | HP=2560 ATK=713

敌人搜索 "源石虫": 26 results, 2 attr levels ✓
材料 "固源岩": 合成树 + 59 掉落关卡 ✓
别名声 "阿能" → "能天使" "小羊"→"艾雅法拉" "42"→"史尔特尔" ✓
```

## 五、数据文件清单

```
data/ArknightsGameResource/gamedata/excel/
    character_table.json, item_table.json, stage_table.json,
    gacha_table.json, skill_table.json, char_patch_table.json,
    skin_table.json, enemy_handbook_table.json, uniequip_table.json,
    building_data.json, favor_table.json, handbook_info_table.json,
    charword_table.json, token_table.json, range_table.json,
    char_meta_table.json, handbook_team_table.json,
    battle_equip_table.json

data/ArknightsGameResource/gamedata/levels/enemydata/
    enemy_database.json (12MB, 1824 enemies)
```

## 六、已知局限

1. **Yituliu 掉落效率** — AmiyaBot 用 peewee ORM 存储，AstrBot 无数据库，已返回空列表
2. **OCR 公招截图** — 依赖百度云/PaddleOCR/Windows OCR，未迁移
3. **Sxys 作战地图** — stages 插件的地图图片下载功能未迁移
4. **activity_table.json** — 未下载，导致 side_story_map 为空
5. **别名审核管理** — normalize.py 提供替换表，但无审核/备份/GUI 管理

## 七、部署说明

```bash
# 1. 下载数据
bash scripts/download_data.sh

# 2. 安装依赖
pip install playwright jieba zhon
python -m playwright install chromium

# 3. 同步到 AstrBot
bash scripts/sync_to_astrbot.sh

# 4. 在 AstrBot WebUI 中启用/重载插件
```
