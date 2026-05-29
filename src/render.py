"""
HTML 模板渲染适配层
"""

import json
import re
from pathlib import Path

TEAM_TABLE = {
    "rhodes": "罗德岛", "penguin": "企鹅物流", "blacksteel": "黑钢国际",
    "rhine": "莱茵生命", "sweep": "S.W.E.E.P", "kappa": "喀兰贸易",
    "gavial": "嘉维尔团队", "yan": "炎", "lgd": "龙门近卫局",
    "siracusa": "叙拉古", "siesta": "汐斯塔", "victoria": "维多利亚",
    "ursus": "乌萨斯", "bolivar": "玻利瓦尔", "columbia": "哥伦比亚",
    "sargon": "萨尔贡", "sami": "萨米", "higashi": "东国",
    "laterano": "拉特兰", "leithanien": "莱塔尼亚", "kazimierz": "卡西米尔",
    "rim": "雷姆必拓", "minos": "米诺斯", "iberia": "伊比利亚",
    "kjerag": "谢拉格", "dublinn": "深池", "egir": "阿戈尔",
    "abyssal": "深海猎人", "followers": "使徒", "babel": "巴别塔",
    "siracusano": "叙拉古", "glasgow": "格拉斯哥帮", "lungmen": "龙门",
}

PROF_CN = {
    "WARRIOR": "近卫", "SNIPER": "狙击", "TANK": "重装",
    "MEDIC": "医疗", "SUPPORT": "辅助", "CASTER": "术师",
    "SPECIAL": "特种", "PIONEER": "先锋",
}


def _load_template(name: str) -> str:
    path = Path(__file__).resolve().parent.parent / "templates" / name
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


async def _render(star_self, template_name: str, **data) -> str | None:
    try:
        tmpl = _load_template(template_name)
        if not tmpl:
            return None
        return await star_self.html_render(tmpl, data)
    except Exception:
        return None


async def render_operator_info(star_self, char: dict, char_id: str) -> str | None:
    """干员信息卡片 — 数据格式对齐 AmiyaBot OperatorData.get_operator_detail()"""
    from .game_data import ArkData
    gd = ArkData()

    name = char.get("name", "")
    rarity = char.get("rarity", 0) + 1
    phases = char.get("phases", [])
    max_phase = phases[-1] if phases else {}
    attrs = max_phase.get("attributesKeyFrames", [{}])[-1].get("data", {})

    # ── info (对齐 AmiyaBot operator.infos 列表) ──
    info = {
        "name": name,
        "en_name": char.get("appellation", "") or "",
        "number": char.get("displayNumber", "") or "",
        "rarity": rarity,
        "classes": PROF_CN.get(char.get("profession", ""), char.get("profession", "")),
        "classes_sub": char.get("subProfessionId", ""),
        "nation": _resolve_team(char.get("nationId", "")),
        "group": _resolve_team(char.get("groupId", "")),
        "team": _resolve_team(char.get("teamId", "")),
        "race": _parse_race(char),
        "drawer": _parse_drawer(char),
        "birthday": _parse_birthday(char),
        "tags": char.get("tagList", []),
        "is_sp": char.get("isSpChar", False),
        "profile": char.get("itemUsage", "") or "",
        "impression": char.get("itemDesc", "") or "",
        "potential_item": "",
        "range": "",
        "real_name": [],
        "cv": {},
    }

    # ── detail (属性) ──
    detail = {
        "maxHp": attrs.get("maxHp", 0),
        "atk": attrs.get("atk", 0),
        "def": attrs.get("def", 0),
        "magicResistance": attrs.get("magicResistance", 0),
        "attackSpeed": attrs.get("attackSpeed", 100),
        "baseAttackTime": attrs.get("baseAttackTime", 0),
        "blockCnt": attrs.get("blockCnt", 1),
        "cost": attrs.get("cost", 0),
        "respawnTime": attrs.get("respawnTime", 0),
        "operator_trait": _clean_trait(char.get("description", "")),
    }

    # ── 天赋 ──
    talents = []
    for t in char.get("talents", []):
        for c in t.get("candidates", []):
            if c.get("name") and "？" not in c.get("name", ""):
                talents.append({
                    "talents_name": c.get("name", ""),
                    "talents_desc": _clean_desc(c.get("description", "")),
                })
                break

    # ── 技能 ──
    skill_list = []
    skills_desc = {}
    raw_skills = char.get("skills", [])
    for i, sk in enumerate(raw_skills):
        sid = sk.get("skillId", "")
        skill_data = _load_skill_json(gd, sid)
        levels = skill_data.get("levels", [])
        skill_name = levels[0].get("name", f"技能{sid}") if levels else f"技能{sid}"
        skill_list.append({
            "skill_no": i,
            "skill_name": skill_name,
            "skill_icon": f"skill_icon_{sid}",
        })
        # Build skills_desc (each level)
        skill_descs = []
        for lv in levels:
            skill_descs.append({
                "sp_type": lv.get("spData", {}).get("spType", 1),
                "sp_init": lv.get("spData", {}).get("initSp", 0),
                "sp_cost": lv.get("spData", {}).get("spCost", 0),
                "duration": lv.get("duration", 0),
                "skill_type": lv.get("skillType", 0),
                "description": _clean_desc(lv.get("description", "")),
                "range": "",
            })
        skills_desc[i] = skill_descs

    # ── 潜能 ──
    potential = []
    for rank in char.get("potentialRanks", []):
        potential.append({
            "potential_rank": rank.get("type", 0),
            "potential_desc": rank.get("description", ""),
        })

    # ── 基建技能 ──
    building_skills = []
    for bs in char.get("trait", {}).get("candidates", []) if char.get("trait") else []:
        pass  # Amiya doesn't have building skills in trait

    data = {
        "info": info,
        "detail": detail,
        "trust": {},
        "talents": talents,
        "potential": potential,
        "building_skills": building_skills,
        "skill_list": skill_list,
        "skills_desc": skills_desc,
        "modules": [],
        "skin": gd.get_char_image_path(char_id, "portrait"),
    }

    data_json = json.dumps(data, ensure_ascii=False)
    return await _render(star_self, "operatorInfo.html", operator_data_json=data_json)


def _resolve_team(tid) -> str:
    if not tid: return ""
    return TEAM_TABLE.get(tid, tid)


def _parse_race(char: dict) -> str:
    desc = char.get("description", "") or char.get("itemUsage", "") or ""
    m = re.search(r'【(\w+)】', desc)
    if m: return m.group(1)
    return ""


def _parse_drawer(char: dict) -> str:
    return ""


def _parse_birthday(char: dict) -> str:
    return ""


def _clean_trait(text: str) -> str:
    return re.sub(r'<@[^>]+>', '', text)


def _clean_desc(text: str) -> str:
    return re.sub(r'<@[^>]+>', '', text)


def _load_skill_json(gd, skill_id: str) -> dict:
    try:
        return gd._load_json("skill_table.json").get(skill_id, {})
    except Exception:
        return {}
