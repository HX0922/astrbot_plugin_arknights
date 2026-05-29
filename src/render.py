"""
HTML 模板渲染适配层

流程: Jinja2 填充数据 → AstrBot html_render() → 图片路径
所有 Vue.js 方法已预计算为纯数据字段，模板使用纯 Jinja2 语法。
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


_env: Environment | None = None


def _get_env() -> Environment:
    global _env
    if _env is None:
        templates_dir = Path(__file__).resolve().parent.parent / "templates"
        _env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html"]),
        )
    return _env


def _render(context, template_name: str, **data) -> str | None:
    """渲染模板为图片路径。失败返回 None。"""
    try:
        html = _get_env().get_template(template_name).render(**data)
        if hasattr(context, "html_render") and callable(context.html_render):
            return context.html_render(html)
        return None
    except Exception:
        return None


# ── 干员信息 ──────────────────────────────────────────

def render_operator_info(context, char: dict, char_id: str) -> str | None:
    """渲染干员基础信息卡片"""
    data = _build_operator_data(char, char_id)
    return _render(context, "operatorInfo.html", data=data, background_url="")


def render_skills_detail(context, char: dict, char_id: str) -> str | None:
    """渲染技能详情"""
    data = _build_operator_data(char, char_id)
    return _render(context, "skillsDetail.html", data=data)


def render_operator_cost(context, char: dict, char_id: str) -> str | None:
    """渲染升级材料"""
    data = _build_operator_data(char, char_id)
    return _render(context, "operatorCost.html", data=data)


def render_operator_skin(context, char: dict, char_id: str) -> str | None:
    """渲染皮肤"""
    from .game_data import ArkData
    from .operator import format_operator_skins
    skins = format_operator_skins(char_id)
    return _render(context, "operatorSkin.html", skins=skins, char_name=char.get("name", ""))


def render_operator_module(context, char: dict, char_id: str) -> str | None:
    """渲染模组"""
    from .operator import format_operator_modules
    modules = format_operator_modules(char)
    return _render(context, "operatorModule.html", modules=modules, char_name=char.get("name", ""))


# ── 公招 ──────────────────────────────────────────────

def render_recruit(context, recruit_data: dict) -> str | None:
    """渲染公招结果"""
    return _render(context, "operatorRecruit.html", **recruit_data)


# ── 材料 ──────────────────────────────────────────────

def render_material(context, item: dict) -> str | None:
    """渲染材料信息"""
    data = _build_material_data(item)
    return _render(context, "material.html", **data)


# ── 关卡 ──────────────────────────────────────────────

def render_stage(context, stage: dict) -> str | None:
    """渲染关卡信息"""
    data = _build_stage_data(stage)
    return _render(context, "stage.html", **data)


# ── 敌人 ──────────────────────────────────────────────

def render_enemy(context, enemy: dict) -> str | None:
    """渲染敌人详情"""
    data = _build_enemy_data(enemy)
    return _render(context, "enemyDetail.html", **data)


def render_enemy_index(context, enemies: list[dict]) -> str | None:
    """渲染敌人索引列表"""
    items = [_build_enemy_index_item(e) for e in enemies]
    return _render(context, "enemyIndex.html", items=items, count=len(items))


# ════════════════════════════════════════════════════════
# 数据预计算（替代原 Vue.js 方法）
# ════════════════════════════════════════════════════════

def _build_operator_data(char: dict, char_id: str) -> dict:
    """预计算干员模板所需的所有数据字段"""
    from .game_data import ArkData
    gd = ArkData()

    rarity = char.get("rarity", 0) + 1
    phases = char.get("phases", [])
    max_phase = phases[-1] if phases else {}
    attrs = max_phase.get("attributesKeyFrames", [{}])[-1].get("data", {})
    trust = {}  # 信赖加成（如有精英阶段）
    if len(phases) > 1:
        trust_frame = phases[1].get("attributesKeyFrames", [{}])[-1].get("data", {})
        trust = {k: trust_frame.get(k, 0) - attrs.get(k, 0) for k in attrs if trust_frame.get(k, 0) > attrs.get(k, 0)}

    # 属性（基础 + 信赖 + 模组）
    def _attr_val(key):
        base = attrs.get(key, 0)
        t = trust.get(key, 0)
        return {
            key: base,
            f"{key}_trust": f"+{t}" if t > 0 else "",
            f"{key}_module": "",
        }

    attr_data = {}
    for k in ["maxHp", "atk", "def", "magicResistance", "attackSpeed", "baseAttackTime", "blockCnt", "cost", "respawnTime"]:
        attr_data.update(_attr_val(k))

    # 技能
    from .operator import format_operator_skills, _profession_name
    skills_raw = format_operator_skills(char, char_id)
    skill_list = []
    for i, s in enumerate(skills_raw):
        skill_list.append({
            "skill_no": i,
            "skill_name": s.get("name", ""),
            "skill_icon_url": f"../skill/skill_icon_{s.get('skill_id', '')}.png",
            "sp_type": 1,
            "sp_type_class": "t1",
            "sp_type_text": "自动回复",
            "sp_init": 0,
            "sp_cost": 0,
            "duration": 0,
            "skill_type_text": "手动触发",
            "description_html": s.get("description", ""),
            "range_html": "",
            "range_id": "",
        })

    # 天赋
    talents = []
    for t in char.get("talents", []):
        candidates = t.get("candidates", [])
        if candidates:
            talents.append({
                "talents_name": candidates[-1].get("name", ""),
                "talents_desc": candidates[-1].get("description", ""),
            })

    # CV
    cv_list = [{"lang": "中文普通话", "value": "未知"}]

    return {
        "info": {
            "name": char.get("name", "未知"),
            "en_name": char.get("appellation", ""),
            "number": char.get("itemUsage", "") or "",
            "rarity": rarity,
            "classes": _profession_name(char),
            "classes_sub": char.get("subProfessionId", ""),
            "classes_icon_url": "",
            "nation": char.get("nationId", ""),
            "group": char.get("groupId", ""),
            "team": char.get("teamId", ""),
            "race": char.get("race", ""),
            "drawer": "",
            "birthday": "",
            "tags": char.get("tagList", []),
            "is_sp": False,
            "profile": "",
            "impression": "",
            "potential_item": "",
            "range_html": "",
            "real_name": [],
            "cv_list": cv_list,
        },
        "detail": {
            **attr_data,
            "operator_trait": char.get("description", ""),
        },
        "talents": talents,
        "skill_list": skill_list,
        "building_skills": [],
        "modules": [],
        "potential": [],
    }


def _build_material_data(item: dict) -> dict:
    """预计算材料模板数据"""
    return {
        "name": item.get("name", ""),
        "icon": "",
        "rarity": item.get("rarity", 0),
        "usage": item.get("usage", ""),
        "description": item.get("description", ""),
        "obtain": item.get("obtainApproach", ""),
        "children_rendered": "",
        "source": [],
    }


def _build_stage_data(stage: dict) -> dict:
    """预计算关卡模板数据"""
    return {
        "code": stage.get("code", stage.get("id", "")),
        "name": stage.get("name", ""),
        "ap_cost": stage.get("apCost", 0),
        "drop_groups": [],
        "enemies": [],
        "map_path": "",
        "description_html": stage.get("description", ""),
        "zone_map_paths": [],
    }


def _build_enemy_data(enemy: dict) -> dict:
    """预计算敌人模板数据"""
    from .game_data import ArkData
    gd = ArkData()

    name = enemy.get("name", "")
    desc = enemy.get("description", "")
    dmg = enemy.get("damageType", [])
    dmg_cn = {"PHYSIC": "物理", "MAGIC": "法术", "HEAL": "治疗", "NO_DAMAGE": "无伤害"}
    dmg_text = ", ".join(dmg_cn.get(d, d) for d in dmg)

    abilities = enemy.get("abilityList", [])
    ability_html = "<br>".join(a.get("text", "") for a in abilities) if abilities else ""

    links = enemy.get("linkEnemies", [])
    link_items = []
    for lid in links:
        le = gd.enemies.get(lid, {})
        link_items.append({
            "name": le.get("name", lid),
            "icon_path": "",
            "class_level": le.get("enemyLevel", "").lower(),
            "level_name": le.get("enemyLevel", ""),
        })

    return {
        "name": name,
        "index": enemy.get("enemyIndex", ""),
        "description": desc,
        "damage_type": dmg_text,
        "ability_html": ability_html,
        "level": {
            "name": enemy.get("enemyLevel", ""),
        },
        "endura": True,
        "attack": True,
        "defence": True,
        "resistance": True,
        "link_items": link_items,
    }


def _build_enemy_index_item(enemy: dict) -> dict:
    """预计算敌人索引项"""
    return {
        "name": enemy.get("name", ""),
        "index": enemy.get("enemyIndex", ""),
        "level_name": enemy.get("enemyLevel", ""),
        "enemy_icon_path": "",
    }
