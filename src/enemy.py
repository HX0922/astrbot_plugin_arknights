"""
敌人查询模块 — 对齐 AmiyaBot 的 Enemy 类

提供完整的敌方单位查询能力:
- Enemy.find_enemies(name) — 按名称/编号模糊搜索
- Enemy.get_enemy(name) — 获取敌人完整信息（含属性、关联敌人）
- Enemy.get_value(key, source) — 嵌套字典值遍历

使用 ArknightsGameData().enemies，数据来自:
- enemy_handbook_table.json['enemyData'] (基本信息)
- levels/enemydata/enemy_database.json (等级属性数据)

严格对齐 AmiyaBot:
  /mnt/g/Coding/vscode_python_project_holder/Amiya-Bot/plugins/amiyabot-arknights-enemy-3_7/main.py
"""

from collections import Counter
from .game_data import ArknightsGameData
from .operator_model import integer


# ── 等级 / 伤害类型中文名 ──────────────────────────────

LEVEL_CN = {
    "BOSS": "领袖",
    "ELITE": "精英",
    "NORMAL": "普通",
}

DAMAGE_TYPE_CN = {
    "PHYSIC": "物理",
    "MAGIC": "法术",
    "HEAL": "治疗",
    "NO_DAMAGE": "无伤害",
}

RACE_NAMES = {}  # 延迟加载


def _load_race_names():
    """加载种族中文名"""
    global RACE_NAMES
    if RACE_NAMES:
        return
    import json
    from pathlib import Path
    from .game_data import ArknightsGameResource
    root = ArknightsGameResource.get_data_root()
    path = root / "gamedata" / "excel" / "enemy_handbook_table.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        race_data = data.get("raceData", {})
        for race_id, race in race_data.items():
            RACE_NAMES[race_id] = race.get("raceName", race_id)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# Enemy 类 — 对齐 AmiyaBot Enemy
# ═══════════════════════════════════════════════════════════

class Enemy:
    """敌方单位查询类 — 严格对齐 AmiyaBot

    使用方式:
        results = Enemy.find_enemies("源石虫")
        enemy = Enemy.get_enemy("源石虫")
    """

    @classmethod
    def find_enemies(cls, name: str) -> list:
        """按名称模糊搜索敌方单位

        匹配规则 (与 AmiyaBot 完全一致):
        - 名称精确匹配 (忽略大小写)
        - 或 name_len > 1 且 name 是敌方名称的子串

        Returns:
            list of [enemy_name, enemy_item] pairs
        """
        result = []
        name = name.lower()
        enemies = ArknightsGameData().enemies

        for e_name, item in enemies.items():
            if name == e_name.lower() or (len(name) > 1 and name in e_name.lower()):
                result.append([e_name, item])

        return result

    @classmethod
    def get_enemy(cls, name: str, get_links: bool = True) -> dict | None:
        """获取单个敌人的完整信息

        解析嵌套的 key_map 属性 (attributes.maxHp → maxHp)，
        返回 {enemy_data + 'attrs' + 'link_items'}。

        Args:
            name: 敌方单位名称
            get_links: 是否递归获取关联敌人

        Returns:
            dict with keys: info fields + attrs + link_items, or None
        """
        key_map = {
            "attributes.maxHp": {"title": "maxHp", "value": ""},
            "attributes.atk": {"title": "atk", "value": ""},
            "attributes.def": {"title": "def", "value": ""},
            "attributes.magicResistance": {"title": "magicResistance", "value": ""},
            "attributes.moveSpeed": {"title": "moveSpeed", "value": ""},
            "attributes.baseAttackTime": {"title": "baseAttackTime", "value": ""},
            "attributes.hpRecoveryPerSec": {"title": "hpRecoveryPerSec", "value": ""},
            "attributes.massLevel": {"title": "massLevel", "value": ""},
            "attributes.stunImmune": {"title": "stunImmune", "value": ""},
            "attributes.silenceImmune": {"title": "silenceImmune", "value": ""},
            "attributes.sleepImmune": {"title": "sleepImmune", "value": ""},
            "attributes.frozenImmune": {"title": "frozenImmune", "value": ""},
            "attributes.levitateImmune": {"title": "levitateImmune", "value": ""},
            "attributes.disarmedCombatImmune": {"title": "disarmedCombatImmune", "value": ""},
            "attributes.fearedImmune": {"title": "fearedImmune", "value": ""},
            "attributes.palsyImmune": {"title": "palsyImmune", "value": ""},
            "attributes.attractImmune": {"title": "attractImmune", "value": ""},
            "rangeRadius": {"title": "rangeRadius", "value": ""},
            "lifePointReduce": {"title": "lifePointReduce", "value": ""},
        }

        enemies = ArknightsGameData().enemies
        enemy = enemies.get(name)

        attrs = {}
        link_items = []

        if not enemy:
            return None

        if enemy.get("data"):
            for item in enemy["data"]:
                level = item.get("level")
                attrs[level] = {}

                detail_data = item.get("enemyData", {})
                for key in key_map:
                    defined, value = cls.get_value(key, detail_data)
                    if defined:
                        key_map[key]["value"] = value
                    else:
                        value = key_map[key]["value"]

                    attrs[level][key_map[key]["title"]] = value

        if get_links:
            for link_id in enemy.get("info", {}).get("linkEnemies", []):
                res = cls.get_enemy(link_id, get_links=False)
                if res:
                    link_items.append(res)

        return {**enemy, "attrs": attrs, "link_items": link_items}

    @classmethod
    def get_value(cls, key: str, source: dict) -> tuple:
        """嵌套字典值遍历 — 严格对齐 AmiyaBot

        按 '.' 分割 key 逐层进入 source dict，
        返回 (m_defined, m_value) 元组。

        AmiyaBot 原版不处理 KeyError（数据保证完整性）。
        """
        for item in key.split("."):
            if item in source:
                source = source[item]
        return source["m_defined"], integer(source["m_value"])


# ═══════════════════════════════════════════════════════════
# 向下兼容的便捷函数
# ═══════════════════════════════════════════════════════════

def search_enemy(keyword: str) -> list[dict]:
    """按名称/编号搜索敌人 (向下兼容)"""
    results = Enemy.find_enemies(keyword)
    # 返回 info dict 列表（保持旧接口兼容）
    return [
        item[1].get("info", item[1])
        for item in results
    ]


def format_enemy_brief(enemy: dict) -> str:
    """格式化敌人简要信息（纯文本，用于列表和命令返回）"""
    _load_race_names()

    # 兼容新旧结构: enemy 可能是 {'info': ..., 'data': ...} 或纯 info dict
    info = enemy.get("info", enemy)
    name = info.get("name", "未知")
    index = info.get("enemyIndex", "")
    level = info.get("enemyLevel", "")
    level_cn = LEVEL_CN.get(level, level)

    lines = [f"【{name}】编号: {index}"]

    if level_cn:
        lines.append(f"等级: {level_cn}")

    # 种族
    tags = info.get("enemyTags", [])
    races = [RACE_NAMES.get(t, t) for t in tags if t in RACE_NAMES]
    if races:
        lines.append(f"种族: {', '.join(races)}")

    # 伤害类型
    dmg = info.get("damageType", [])
    if dmg:
        dmg_cn = [DAMAGE_TYPE_CN.get(d, d) for d in dmg]
        lines.append(f"伤害类型: {', '.join(dmg_cn)}")

    # 描述
    desc = info.get("description", "")
    if desc:
        lines.append(f"\n{desc}")

    # 能力
    abilities = info.get("abilityList", [])
    if abilities:
        lines.append("\n【能力】")
        for ab in abilities:
            text = ab.get("text", "")
            if text:
                lines.append(f"  · {text}")

    # 关联敌人
    links = info.get("linkEnemies", [])
    if links:
        data = ArknightsGameData()
        link_names = []
        for link_id in links:
            link_enemy = data.enemies.get(link_id, {})
            link_info = link_enemy.get("info", link_enemy)
            lname = link_info.get("name", link_id)
            link_names.append(lname)
        lines.append(f"\n关联敌人: {', '.join(link_names)}")

    return "\n".join(lines)


def format_enemy_index_list(enemies: list[dict], max_display: int = 12) -> str:
    """格式化敌人搜索结果列表，供用户选择"""
    if not enemies:
        return "博士，没有找到匹配的敌人单位。"

    lines = [f"找到 {len(enemies)} 个匹配的敌人单位:\n"]

    for i, enemy in enumerate(enemies[:max_display]):
        info = enemy.get("info", enemy)
        name = info.get("name", "未知")
        index = info.get("enemyIndex", "")
        level = LEVEL_CN.get(info.get("enemyLevel", ""), "")
        lines.append(f"  {i + 1}. {name} [{index}] {level}")

    if len(enemies) > max_display:
        lines.append(f"  ... 还有 {len(enemies) - max_display} 个结果")

    lines.append("\n回复【序号】查看详细信息")
    return "\n".join(lines)


def get_enemy_by_name(name: str) -> dict | None:
    """通过名称精确查找敌人 (向下兼容)"""
    result = Enemy.get_enemy(name)
    if result:
        result["id"] = result.get("info", {}).get("enemyId", "")
    return result
