"""
HTML 模板渲染适配层

AstrBot html_render(tmpl_str, data) 内部处理 Jinja2 渲染 →
远程 T2I 浏览器端点截图。Vue 模板需用 {% raw %} 保护。

用法:
    from .src.render import render_operator_info
    img_path = await render_operator_info(self.context, char, char_id)
"""

import json
from pathlib import Path


def _load_template(name: str) -> str:
    """加载模板文件内容"""
    path = Path(__file__).resolve().parent.parent / "templates" / name
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


async def _render(context, template_name: str, **data) -> str | None:
    """异步渲染模板为图片路径"""
    try:
        tmpl = _load_template(template_name)
        if not tmpl:
            return None
        return await context.html_render(tmpl, data)
    except Exception:
        return None


# ── 干员 ──────────────────────────────────────────────

async def render_operator_info(context, char: dict, char_id: str) -> str | None:
    """干员信息卡片"""
    from .game_data import ArkData
    gd = ArkData()
    name = char.get("name", "")
    rarity = char.get("rarity", 0) + 1
    phases = char.get("phases", [])
    max_phase = phases[-1] if phases else {}
    attrs = max_phase.get("attributesKeyFrames", [{}])[-1].get("data", {})

    data = {
        "info": {
            "name": name,
            "en_name": char.get("appellation", "") or "",
            "number": "",
            "rarity": rarity,
            "classes": char.get("profession", ""),
            "classes_sub": char.get("subProfessionId", ""),
            "nation": char.get("nationId", "") or "",
            "group": char.get("groupId", "") or "",
            "team": char.get("teamId", "") or "",
            "race": char.get("race", "") or "",
            "drawer": "", "birthday": "",
            "tags": char.get("tagList", []),
            "is_sp": False,
            "profile": char.get("itemUsage", "") or "",
            "impression": char.get("description", "") or "",
            "potential_item": "",
            "range": "",
            "real_name": [],
            "cv": {},
        },
        "detail": {
            "maxHp": attrs.get("maxHp", 0),
            "atk": attrs.get("atk", 0),
            "def": attrs.get("def", 0),
            "magicResistance": attrs.get("magicResistance", 0),
            "attackSpeed": attrs.get("attackSpeed", 100),
            "baseAttackTime": attrs.get("baseAttackTime", 0),
            "blockCnt": attrs.get("blockCnt", 1),
            "cost": attrs.get("cost", 0),
            "respawnTime": attrs.get("respawnTime", 0),
            "operator_trait": char.get("description", "") or "",
        },
        "trust": {},
        "talents": [],
        "potential": [],
        "building_skills": [],
        "skill_list": [],
        "skills_desc": {},
        "modules": [],
        "skin": gd.get_char_image_path(char_id, "portrait"),
    }

    return await _render(context, "operatorInfo.html", operator_data=data)


# ── 其他模块 ──────────────────────────────────────────

async def render_skills_detail(context, char: dict, char_id: str) -> str | None:
    return None  # TODO

async def render_recruit(context, recruit_data: dict) -> str | None:
    return await _render(context, "operatorRecruit.html", **recruit_data)

async def render_material(context, item: dict) -> str | None:
    return await _render(context, "material.html",
        name=item.get("name", ""), description=item.get("description", ""),
        usage=item.get("usage", ""), obtain=item.get("obtainApproach", ""))

async def render_stage(context, stage: dict) -> str | None:
    return await _render(context, "stage.html",
        code=stage.get("code", ""), name=stage.get("name", ""),
        ap_cost=stage.get("apCost", 0))

async def render_enemy(context, enemy: dict) -> str | None:
    return await _render(context, "enemyDetail.html", **enemy)

async def render_enemy_index(context, enemies: list[dict]) -> str | None:
    return await _render(context, "enemyIndex.html", items=enemies, count=len(enemies))
