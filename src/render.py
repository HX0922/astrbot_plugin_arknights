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

PROF_CN = {
    "WARRIOR": "近卫", "SNIPER": "狙击", "TANK": "重装",
    "MEDIC": "医疗", "SUPPORT": "辅助", "CASTER": "术师",
    "SPECIAL": "特种", "PIONEER": "先锋",
}


def _load_template(name: str) -> str:
    """加载模板文件内容"""
    path = Path(__file__).resolve().parent.parent / "templates" / name
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


async def _render(star_self, template_name: str, **data) -> str | None:
    """异步渲染模板为图片路径"""
    try:
        tmpl = _load_template(template_name)
        if not tmpl:
            from astrbot.api import logger
            logger.error(f"[Arknights] 模板文件未找到: {template_name}")
            return None
        from astrbot.api import logger
        logger.info(f"[Arknights] 模板 {template_name} 加载成功 ({len(tmpl)} chars), 准备调用 html_render")
        result = await star_self.html_render(tmpl, data)
        logger.info(f"[Arknights] html_render 返回: {result}")
        return result
    except Exception as e:
        from astrbot.api import logger
        logger.error(f"[Arknights] _render 失败 ({template_name}): {e}", exc_info=True)
        return None


# ── 干员 ──────────────────────────────────────────────

async def render_operator_info(star_self, char: dict, char_id: str) -> str | None:
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
            "classes": PROF_CN.get(char.get("profession", ""), char.get("profession", "")),
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

    # Pre-serialize to avoid Jinja2 tojson unicode escaping
    data_json = json.dumps(data, ensure_ascii=False)
    return await _render(star_self, "operatorInfo.html", operator_data_json=data_json)


# ── 其他模块 ──────────────────────────────────────────

async def render_skills_detail(star_self, char: dict, char_id: str) -> str | None:
    return None  # TODO

async def render_recruit(star_self, recruit_data: dict) -> str | None:
    return await _render(star_self, "operatorRecruit.html", **recruit_data)

async def render_material(star_self, item: dict) -> str | None:
    return await _render(star_self, "material.html",
        name=item.get("name", ""), description=item.get("description", ""),
        usage=item.get("usage", ""), obtain=item.get("obtainApproach", ""))

async def render_stage(star_self, stage: dict) -> str | None:
    return await _render(star_self, "stage.html",
        code=stage.get("code", ""), name=stage.get("name", ""),
        ap_cost=stage.get("apCost", 0))

async def render_enemy(star_self, enemy: dict) -> str | None:
    return await _render(star_self, "enemyDetail.html", **enemy)

async def render_enemy_index(star_self, enemies: list[dict]) -> str | None:
    return await _render(star_self, "enemyIndex.html", items=enemies, count=len(enemies))
