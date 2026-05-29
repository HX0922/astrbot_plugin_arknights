"""
敌人查询模块

查询明日方舟敌方单位信息，包括:
- 基础信息（名称、编号、等级、种族）
- 描述
- 能力列表
- 伤害类型
- 关联敌人

数据源: enemy_handbook_table.json
"""

from .game_data import ArkData

# 等级中文名
LEVEL_CN = {
    "BOSS": "领袖",
    "ELITE": "精英",
    "NORMAL": "普通",
}

# 伤害类型
DAMAGE_TYPE_CN = {
    "PHYSIC": "物理",
    "MAGIC": "法术",
    "HEAL": "治疗",
    "NO_DAMAGE": "无伤害",
}

# 种族名
RACE_NAMES = {}  # 延迟加载


def _load_race_names():
    """加载种族中文名"""
    global RACE_NAMES
    if RACE_NAMES:
        return
    data = ArkData()
    race_data = data._load_json("enemy_handbook_table.json").get("raceData", {})
    for race_id, race in race_data.items():
        RACE_NAMES[race_id] = race.get("raceName", race_id)


def search_enemy(keyword: str) -> list[dict]:
    """按名称/编号搜索敌人"""
    return ArkData().search_enemies(keyword)


def format_enemy_brief(enemy: dict) -> str:
    """格式化敌人简要信息（纯文本，用于列表和命令返回）"""
    _load_race_names()

    name = enemy.get("name", "未知")
    index = enemy.get("enemyIndex", "")
    level = enemy.get("enemyLevel", "")
    level_cn = LEVEL_CN.get(level, level)

    lines = [f"【{name}】编号: {index}"]

    if level_cn:
        lines.append(f"等级: {level_cn}")

    # 种族
    tags = enemy.get("enemyTags", [])
    races = [RACE_NAMES.get(t, t) for t in tags if t in RACE_NAMES]
    if races:
        lines.append(f"种族: {', '.join(races)}")

    # 伤害类型
    dmg = enemy.get("damageType", [])
    if dmg:
        dmg_cn = [DAMAGE_TYPE_CN.get(d, d) for d in dmg]
        lines.append(f"伤害类型: {', '.join(dmg_cn)}")

    # 描述
    desc = enemy.get("description", "")
    if desc:
        lines.append(f"\n{desc}")

    # 能力
    abilities = enemy.get("abilityList", [])
    if abilities:
        lines.append("\n【能力】")
        for ab in abilities:
            text = ab.get("text", "")
            if text:
                lines.append(f"  · {text}")

    # 关联敌人
    links = enemy.get("linkEnemies", [])
    if links:
        data = ArkData()
        link_names = []
        for link_id in links:
            link_enemy = data.enemies.get(link_id, {})
            name = link_enemy.get("name", link_id)
            link_names.append(name)
        lines.append(f"\n关联敌人: {', '.join(link_names)}")

    return "\n".join(lines)


def format_enemy_index_list(enemies: list[dict], max_display: int = 12) -> str:
    """格式化敌人搜索结果列表，供用户选择"""
    if not enemies:
        return "博士，没有找到匹配的敌人单位。"

    lines = [f"找到 {len(enemies)} 个匹配的敌人单位:\n"]

    for i, enemy in enumerate(enemies[:max_display]):
        name = enemy.get("name", "未知")
        index = enemy.get("enemyIndex", "")
        level = LEVEL_CN.get(enemy.get("enemyLevel", ""), "")
        lines.append(f"  {i + 1}. {name} [{index}] {level}")

    if len(enemies) > max_display:
        lines.append(f"  ... 还有 {len(enemies) - max_display} 个结果")

    lines.append("\n回复【序号】查看详细信息")
    return "\n".join(lines)


def get_enemy_by_name(name: str) -> dict | None:
    """通过名称精确查找敌人"""
    data = ArkData()
    for eid, enemy in data.enemies.items():
        if enemy.get("name", "") == name:
            return {"id": eid, **enemy}
    return None
