"""
HTML 渲染 — Jinja2 注入数据到 Vue 模板，T2I 浏览器渲染

流程: 加载 Vue 模板 → Jinja2 注入 JSON 数据 → T2I 渲染 → 图片 URL
"""

import json
from pathlib import Path

PROF_CN = {"WARRIOR":"近卫","SNIPER":"狙击","TANK":"重装","MEDIC":"医疗","SUPPORT":"辅助","CASTER":"术师","SPECIAL":"特种","PIONEER":"先锋"}
TEAM_TABLE = {"rhodes":"罗德岛","penguin":"企鹅物流","blacksteel":"黑钢国际","rhine":"莱茵生命","kappa":"喀兰贸易","sweep":"S.W.E.E.P","yan":"炎","lgd":"龙门近卫局","lungmen":"龙门","siracusa":"叙拉古","victoria":"维多利亚","ursus":"乌萨斯","columbia":"哥伦比亚","sargon":"萨尔贡","higashi":"东国","laterano":"拉特兰","leithanien":"莱塔尼亚","kazimierz":"卡西米尔","rim":"雷姆必拓","iberia":"伊比利亚","kjerag":"谢拉格","dublinn":"深池","egir":"阿戈尔","abyssal":"深海猎人","followers":"使徒","babel":"巴别塔","glasgow":"格拉斯哥帮"}


def _load(name: str) -> str:
    p = Path(__file__).resolve().parent.parent / "templates" / name
    return p.read_text("utf-8") if p.exists() else ""


async def _render(star_self, template_name: str, **data) -> str | None:
    try:
        tmpl = _load(template_name)
        if not tmpl:
            return None
        return await star_self.html_render(tmpl, data)
    except Exception:
        return None


async def render_operator_info(star_self, char: dict, char_id: str) -> str | None:
    name = char.get("name", "")
    rarity = char.get("rarity", 0) + 1
    phases = char.get("phases", [])
    mp = phases[-1] if phases else {}
    a = mp.get("attributesKeyFrames", [{}])[-1].get("data", {})

    # ── talents ──
    talents = []
    for t in char.get("talents", []):
        for c in t.get("candidates", []):
            n = c.get("name", "")
            if n and "？" not in n:
                talents.append({"talents_name": n, "talents_desc": c.get("description", "")})
                break

    # ── skills ──
    skill_list = []
    skills_desc = {}
    for i, sk in enumerate(char.get("skills", [])):
        sid = sk.get("skillId", "")
        sdata = _load_skill(sid)
        lvs = sdata.get("levels", [])
        name = lvs[0].get("name", f"技能{sid}") if lvs else f"技能{sid}"
        skill_list.append({"skill_no": i, "skill_name": name, "skill_icon": f"skill_icon_{sid}"})
        descs = []
        for lv in lvs:
            descs.append({
                "sp_type": lv.get("spData", {}).get("spType", 1),
                "sp_init": lv.get("spData", {}).get("initSp", 0),
                "sp_cost": lv.get("spData", {}).get("spCost", 0),
                "duration": lv.get("duration", 0),
                "skill_type": lv.get("skillType", 0),
                "description": lv.get("description", ""),
                "range": "",
            })
        skills_desc[i] = descs

    # ── potential ──
    potential = [{"potential_rank": r.get("type", 0), "potential_desc": r.get("description", "")} for r in char.get("potentialRanks", [])]

    data = {
        "info": {
            "name": name, "en_name": char.get("appellation", "") or "",
            "number": char.get("displayNumber", "") or "", "rarity": rarity,
            "classes": PROF_CN.get(char.get("profession", ""), char.get("profession", "")),
            "classes_sub": char.get("subProfessionId", ""),
            "nation": TEAM_TABLE.get(char.get("nationId", ""), char.get("nationId", "") or ""),
            "group": TEAM_TABLE.get(char.get("groupId", ""), char.get("groupId", "") or ""),
            "team": TEAM_TABLE.get(char.get("teamId", ""), char.get("teamId", "") or ""),
            "race": "", "drawer": "", "birthday": "",
            "tags": char.get("tagList", []), "is_sp": char.get("isSpChar", False),
            "profile": char.get("itemUsage", "") or "", "impression": char.get("itemDesc", "") or "",
            "potential_item": "", "range": "", "real_name": [], "cv": {},
        },
        "detail": {"maxHp": a.get("maxHp", 0), "atk": a.get("atk", 0), "def": a.get("def", 0),
                   "magicResistance": a.get("magicResistance", 0), "attackSpeed": a.get("attackSpeed", 100),
                   "baseAttackTime": a.get("baseAttackTime", 0), "blockCnt": a.get("blockCnt", 1),
                   "cost": a.get("cost", 0), "respawnTime": a.get("respawnTime", 0),
                   "operator_trait": char.get("description", "") or ""},
        "trust": {}, "talents": talents, "potential": potential,
        "building_skills": [], "skill_list": skill_list, "skills_desc": skills_desc,
        "modules": [],
        "skin": f"https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/portrait/{char_id}_1.png",
    }
    data_json = json.dumps(data, ensure_ascii=False)
    return await _render(star_self, "operatorInfo.html", operator_data_json=data_json)


def _load_skill(sid: str) -> dict:
    try:
        p = Path(__file__).resolve().parent.parent / "data" / "ArknightsGameResource" / "gamedata" / "excel" / "skill_table.json"
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f).get(sid, {})
    except Exception:
        return {}
