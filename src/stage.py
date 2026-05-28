"""
关卡查询模块

搜索关卡信息，包括掉落物、理智消耗、敌人等。
"""

from .game_data import ArkData


def search_stage(keyword: str) -> list[dict]:
    """按 ID 或名称搜索关卡"""
    return ArkData().search_stages(keyword)


def format_stage_info(stage: dict) -> str:
    """格式化关卡详细信息"""
    stage_id = stage.get("stageId", stage.get("id", ""))
    code = stage.get("code", stage_id)
    name = stage.get("name", "")
    stage_type = stage.get("stageType", "")
    difficulty = stage.get("difficulty", "NORMAL")

    lines = [
        f"【{code}】{name}",
        f"类型: {stage_type} | 难度: {difficulty}",
    ]

    # 理智消耗
    ap_cost = stage.get("apCost", "?")
    lines.append(f"消耗理智: {ap_cost}")

    # 掉落物
    drops = _get_drop_info(stage)
    if drops:
        lines.append(f"主要掉落: {', '.join(drops[:8])}")

    # 特殊掉落
    extra = _get_extra_drop(stage)
    if extra:
        lines.append(f"额外掉落: {', '.join(extra[:5])}")

    # 敌人信息
    enemies = stage.get("enemyData", [])
    if enemies:
        enemy_count = len(enemies)
        lines.append(f"敌人数量: {enemy_count}")

    return "\n".join(lines)


def _get_drop_info(stage: dict) -> list[str]:
    """提取掉落物名称列表"""
    data = ArkData()
    drop_names = []

    # 普通掉落
    drops = stage.get("dropInfos", [])
    for drop in drops:
        item_id = drop.get("itemId", "")
        if item_id and item_id in data.items:
            drop_names.append(data.items[item_id].get("name", item_id))

    return drop_names


def _get_extra_drop(stage: dict) -> list[str]:
    """提取额外掉落"""
    data = ArkData()
    drop_names = []

    extra = stage.get("extraDropInfos", [])
    for drop in extra:
        item_id = drop.get("itemId", "")
        if item_id and item_id in data.items:
            drop_names.append(data.items[item_id].get("name", item_id))

    return drop_names
