"""
干员信息查询模块

提供干员详细信息格式化输出，包括:
- 基础信息（名称、星级、职业、标签）
- 属性（生命、攻击、防御、法抗等）
- 技能列表
- 天赋
- 潜能/模组/皮肤信息
"""

from .game_data import ArkData, RARITY_STARS

# ── 职业中文名 ──────────────────────────────────────────

PROFESSION_CN = {
    "WARRIOR": "近卫",
    "SNIPER": "狙击",
    "TANK": "重装",
    "MEDIC": "医疗",
    "SUPPORT": "辅助",
    "CASTER": "术师",
    "SPECIAL": "特种",
    "PIONEER": "先锋",
}

# ── 子职业映射 ─────────────────────────────────────────

# 从 character_table 的 subProfessionId 翻译
# 加载时动态构建，此处留空


def _profession_name(char: dict) -> str:
    """获取职业中文名"""
    prof = char.get("profession", "UNKNOWN")
    return PROFESSION_CN.get(prof, prof)


# ── 干员简要信息 ──────────────────────────────────────

def format_operator_brief(char: dict) -> str:
    """返回干员简要信息纯文本"""
    data = ArkData()
    rarity = char.get("rarity", 0) + 1  # 0-indexed → 1-6
    stars = RARITY_STARS.get(rarity, "★" * rarity)
    name = char.get("name", "未知")

    lines = [
        f"【{name}】{stars}",
        f"职业: {_profession_name(char)} | 子职业: {char.get('subProfessionId', '无')}",
    ]

    # 标签
    tags = char.get("tagList", [])
    if tags:
        lines.append(f"标签: {', '.join(tags)}")

    # 获取方式
    obtain = char.get("itemObtainApproach", "")
    if obtain:
        lines.append(f"获取方式: {obtain}")

    # 特性描述
    trait_desc = _get_trait_description(char)
    if trait_desc:
        lines.append(f"特性: {trait_desc}")

    # 基础属性（精二满级 or 精一满级 or 初始）
    phases = char.get("phases", [])
    if phases:
        attrs = _get_attributes(char, len(phases) - 1)
        if attrs:
            lines.append(
                f"生命: {attrs.get('maxHp', '?')} | "
                f"攻击: {attrs.get('atk', '?')} | "
                f"防御: {attrs.get('def', '?')} | "
                f"法抗: {attrs.get('magicResistance', '?')}"
            )
            lines.append(f"费用: {attrs.get('cost', '?')} | 阻挡: {attrs.get('blockCnt', '?')}")

    # 天赋
    talents = char.get("talents", [])
    if talents:
        talent_names = []
        for t in talents:
            candidates = t.get("candidates", [])
            if candidates:
                talent_names.append(candidates[-1].get("name", ""))
        if talent_names:
            lines.append(f"天赋: {' | '.join(talent_names)}")

    return "\n".join(lines)


def _get_trait_description(char: dict) -> str:
    """提取特性描述"""
    trait = char.get("trait", {})
    candidates = trait.get("candidates", [])
    if candidates:
        blackboard = candidates[0].get("blackboard", [])
        if blackboard:
            val = blackboard[0].get("value", "")
            if val and isinstance(val, (int, float)):
                return f"{candidates[0].get('rangeId', '')}: {val}"
        override = candidates[0].get("overrideDescriptions", "")
        name = candidates[0].get("name", "")
        if name:
            return name
    return ""


def _get_attributes(char: dict, phase: int) -> dict:
    """获取指定阶段的属性 keyframes"""
    phases = char.get("phases", [])
    if phase >= len(phases):
        return {}
    attrs = phases[phase].get("attributesKeyFrames", [])
    if attrs:
        return attrs[-1].get("data", {})
    return {}


# ── 技能详情 ──────────────────────────────────────────

def format_operator_skills(
    char: dict, char_id: str, level: int = 7
) -> list[dict]:
    """返回技能列表 [{name, desc, icon_path}, ...]"""
    skills = char.get("skills", [])
    results = []
    data = ArkData()

    for skill in skills:
        skill_id = skill.get("skillId", "")
        skill_data = _load_skill_data(skill_id)

        name = skill_data.get("levels", [{}])[0].get("name", f"技能 {skill_id}")
        level_data = None
        if level - 1 < len(skill_data.get("levels", [])):
            level_data = skill_data["levels"][level - 1]

        desc = level_data.get("description", "") if level_data else ""
        icon_path = data.get_skill_image_path(skill_id)

        results.append({
            "skill_id": skill_id,
            "name": name,
            "description": desc,
            "icon_path": icon_path,
        })

    return results


def _load_skill_data(skill_id: str) -> dict:
    """加载单个技能数据"""
    data = ArkData()
    path = data._data_root / "gamedata" / "excel" / "skill_table.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            all_skills = json.load(f)
        return all_skills.get(skill_id, {})
    except Exception:
        return {}


# ── 模组信息 ──────────────────────────────────────────

def format_operator_modules(char: dict) -> list[dict]:
    """返回模组列表 [{name, desc, type}, ...]"""
    modules = char.get("modules", [])
    if not modules:
        return []

    data = ArkData()
    mod_table = data._load_json("uniequip_table.json")
    equip_dict = mod_table.get("equipDict", {})

    results = []
    for mod in modules:
        mod_id = mod.get("uniEquipId", "")
        mod_info = equip_dict.get(mod_id, {})
        results.append({
            "id": mod_id,
            "name": mod_info.get("uniEquipName", mod_id),
            "type": mod_info.get("typeName1", ""),
        })
    return results


# ── 皮肤列表 ──────────────────────────────────────────

def format_operator_skins(char_id: str) -> list[dict]:
    """返回皮肤列表 [{name, image_path}, ...]"""
    data = ArkData()
    skins = data.skins.get(char_id, [])
    if not skins:
        return []

    results = []
    for skin_id in skins:
        skin_info = data.skins.get(skin_id, {})
        name = skin_info.get("displaySkin", {}).get("skinName", skin_id)
        path = data._data_root / "skin" / f"{skin_id}.png"
        results.append({
            "id": skin_id,
            "name": name,
            "image_path": str(path) if path.exists() else "",
        })
    return results


# ── 内置导入 ───────────────────────────────────────────

import json
