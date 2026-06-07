# ArknightsGameResource Excel 数据文件参考

> 路径: `data/ArknightsGameResource/gamedata/excel/`
> 来源: https://github.com/yuanyan3060/ArknightsGameResource

## 文件清单 (20 个 JSON)

| 文件 | 大小 | 用途 | 迁移必要性 |
|------|------|------|-----------|
| `character_table.json` | 14MB | 干员基础数据 (name/rarity/skills/talents/phases) | 🔴 必须 |
| `skill_table.json` | 11MB | 技能详情 (levels/blackboard/description/spData) | 🔴 必须 |
| `skin_table.json` | 3.1MB | 皮肤/立绘数据 (displaySkin/skinId/drawerList) | 🔴 必须 |
| `item_table.json` | 1.7MB | 物品数据 (材料/信物图标和描述) | 🔴 必须 |
| `stage_table.json` | 20MB | 关卡数据 (code/name/drops/apCost) | 🔴 必须 |
| `building_data.json` | 5.1MB | 基建技能 (buffs/chars/buffChar) | 🔴 必须 |
| `char_patch_table.json` | 46KB | 干员数据补丁 (patchChars → 合并到 character_table) | 🔴 必须 |
| `uniequip_table.json` | 3.2MB | 模组数据 (subProfDict/charEquip/equipDict/missionList) | 🔴 必须 |
| `battle_equip_table.json` | 5.6MB | 模组战斗属性 (phases/attributeBlackboard) | 🔴 必须 |
| `gacha_table.json` | 419KB | 卡池数据 (recruitDetail) | 🟡 抽卡功能 |
| `handbook_info_table.json` | 5.6MB | 干员档案 (storyTextAudio → 【代号】【种族】【生日】) | 🔴 种族/生日/阵营 |
| `handbook_team_table.json` | 10KB | 阵营/队伍/势力翻译 (powerName) | 🔴 势力/队伍翻译 |
| `charword_table.json` | 11MB | 语音数据 (voiceLangDict → cvName) | 🔴 CV声优 |
| `char_meta_table.json` | 64KB | 异格干员关系 (spCharGroups → origin_name) | 🟡 异格原型 |
| `enemy_handbook_table.json` | 1.6MB | 敌方单位数据 (enemyData) | 🔴 敌人查询 |
| `range_table.json` | 53KB | 攻击范围网格 (grids → build_range) | 🔴 范围渲染 |
| `favor_table.json` | — | 信赖加成 | 🟡 |
| `token_table.json` | — | 召唤物数据 | 🟡 |
| `activity_table.json` | — | 活动列表 (插曲/别传 sideStory) | 🟡 |
| `building_data.json` | — | (重复见上) | — |

## 关键数据关系

```
skill_table[skillId].levels[]
  ├── blackboard[] → {key, value} → parse_template 数值替换
  ├── description → {atk:0%} 模板标记
  └── spData → {spType, initSp, spCost, maxChargeTime}

handbook_info_table[charId].storyTextAudio[]
  └── stories[0].storyText → 【代号】xxx\n【种族】xxx\n【生日】x月x日

handbook_team_table[id].powerName
  ├── teamId → team (队伍名)
  ├── groupId → group (阵营名)
  └── nationId → nation (势力名)

charword_table.voiceLangDict[charId].dict[]
  └── cvName → 声优名

building_data.chars[charId].buffChar[].buffData[]
  └── buffId → buffs[buffId] → {skillIcon, buffName, description}

skin_table.charSkins[skinId].displaySkin
  ├── skinName, drawerList, skinGroupName
  └── skinId → PRTS Wiki URL (via indexes/skinUrls.json)
```

## 额外资源 (非 excel)

| 目录 | 内容 | 来源 |
|------|------|------|
| `portrait/` | 干员头像 (小图) | ArknightsGameResource repo |
| `skin/` | 完整精二立绘 (大图) | PRTS Wiki CDN 下载缓存 |
| `item/` | 材料图标 | ArknightsGameResource repo |
| `avatar/` | 干员头像 | ArknightsGameResource repo |
| `skill/` | 技能图标 | ArknightsGameResource repo |
| `building_skill/` | 基建技能图标 | ArknightsGameResource repo |
| `indexes/skinUrls.json` | 立绘 PRTS Wiki URL 索引 | ArknightsGameResource repo |
