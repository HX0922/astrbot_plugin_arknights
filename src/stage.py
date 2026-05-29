"""
关卡查询模块

搜索关卡信息，包括掉落物、理智消耗、敌人等。
"""

from .game_data import ArkData


def search_stage(keyword: str) -> list[dict]:
    """按 ID 或名称搜索关卡，支持难度变体"""
    data = ArkData()
    kw = keyword.strip()

    # 难度检测
    diff_prefix = ""
    diff_label = ""
    for diff_kw, (prefix, label) in DIFFICULTY_MAP.items():
        if diff_kw in kw:
            diff_prefix = prefix
            diff_label = label
            kw = kw.replace(diff_kw, "").strip()
            break

    results = data.search_stages(kw)

    # 应用难度变换
    if diff_prefix and results:
        # 在现有结果中找匹配难度的
        for stage in results:
            sid = stage.get("stageId", stage.get("id", ""))
            if diff_prefix in sid:
                stage["_difficulty_label"] = diff_label
                return [stage]
        # 回退: 尝试构造难度 ID
        stage = results[0]
        orig_id = stage.get("stageId", "")
        for candidate in [f"{diff_prefix}{orig_id}", f"{orig_id}{diff_prefix}"]:
            if candidate in data.stages:
                return [{"id": candidate, **data.stages[candidate], "_difficulty_label": diff_label}]

    return results


DIFFICULTY_MAP = {
    "突袭": ("_hard", "突袭"),
    "简单": ("easy_", "简单"),
    "剧情": ("easy_", "剧情"),
    "困难": ("tough_", "困难"),
    "磨难": ("tough_", "磨难"),
}


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
