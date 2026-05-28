"""
材料/物品查询模块

搜索材料和物品，提供用途、获取关卡、合成配方等信息。
"""

from .game_data import ArkData


def search_material(keyword: str) -> list[dict]:
    """模糊搜索材料"""
    return ArkData().search_items(keyword)


def format_material_info(item: dict) -> str:
    """格式化材料详细信息"""
    name = item.get("name", "未知")
    item_id = item.get("id", "")
    rarity = item.get("rarity", 0)
    stars = "★" * (rarity + 1) if rarity < 5 else "★★★★★"

    lines = [f"【{name}】{stars}", f"ID: {item_id}"]

    # 用途
    usage = item.get("usage", "")
    if usage:
        lines.append(f"用途: {usage}")

    # 描述
    desc = item.get("description", "")
    if desc:
        lines.append(f"描述: {desc}")

    # 获取方式
    obtain = item.get("obtainApproach", "")
    if obtain:
        lines.append(f"获取方式: {obtain}")

    # 建造/制造时间
    build = item.get("buildingProductList", [])
    if build:
        for b in build[:3]:
            room = b.get("roomType", "")
            formula = b.get("formulaId", "")
            count = b.get("count", 1)
            lines.append(f"制造: {room} | 配方: {formula} | 产出: {count}")

    return "\n".join(lines)


def format_material_list(items: list[dict], max_display: int = 10) -> str:
    """格式化材料搜索结果列表"""
    if not items:
        return "未找到匹配的材料。"

    lines = [f"找到 {len(items)} 个匹配材料:"]
    for item in items[:max_display]:
        stars = "★" * (item.get("rarity", 0) + 1)
        lines.append(f"  {stars} {item['name']} ({item.get('id', '')})")

    if len(items) > max_display:
        lines.append(f"  ... 还有 {len(items) - max_display} 个结果")

    return "\n".join(lines)
