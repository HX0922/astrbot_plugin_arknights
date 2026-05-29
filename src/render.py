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
    """干员信息卡片"""
    from .game_data import ArkData
    gd = ArkData()

    name = char.get("name", "")
    rarity = char.get("rarity", 0) + 1
    phases = char.get("phases", [])
    max_phase = phases[-1] if phases else {}
    attrs = max_phase.get("attributesKeyFrames", [{}])[-1].get("data", {})

    # 先用简单模板测试 T2I 是否正常
    test_data = {
        "name": name,
        "stars": "★" * rarity,
        "classes": PROF_CN.get(char.get("profession", ""), char.get("profession", "")),
        "tags": ", ".join(char.get("tagList", [])),
        "hp": str(attrs.get("maxHp", "?")),
        "atk": str(attrs.get("atk", "?")),
        "def_": str(attrs.get("def", "?")),
        "talent": "无",
        "desc": (char.get("description", "") or "")[:100],
    }

    # 尝试天赋
    talents = char.get("talents", [])
    if talents:
        for t in talents:
            for c in t.get("candidates", []):
                if c.get("name") and "？" not in c.get("name", ""):
                    test_data["talent"] = c.get("name", "")
                    break

    # 先用 test.html 验证 T2I 可用
    result = await _render(star_self, "test.html", **test_data)
    if result:
        return result

    # T2I 不可用，跳过复杂模板
    return None

