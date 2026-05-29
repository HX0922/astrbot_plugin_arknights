"""
HTML 模板渲染适配层

将 AmiyaBot 原版 Jinja2/Vue.js 模板适配到 AstrBot 的 html_render()。
流程: 加载模板 → Jinja2 填充数据 → html_render() → 图片路径
"""

import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


# Jinja2 环境（延迟初始化）
_env: Environment | None = None


def _get_env() -> Environment:
    """获取 Jinja2 环境单例"""
    global _env
    if _env is None:
        templates_dir = Path(__file__).resolve().parent.parent / "templates"
        _env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html"]),
        )
    return _env


def render_template(template_name: str, data: dict) -> str:
    """用 Jinja2 渲染模板，返回 HTML 字符串

    Args:
        template_name: 模板文件名 (e.g., 'operatorInfo.html')
        data: 模板变量字典

    Returns:
        渲染后的 HTML 字符串
    """
    env = _get_env()
    template = env.get_template(template_name)
    return template.render(**data)


def render_to_image_path(context, template_name: str, data: dict) -> str:
    """渲染模板为图片，返回文件路径

    Args:
        context: AstrBot Star 的 self.context
        template_name: 模板文件名
        data: 模板变量

    Returns:
        渲染后的图片绝对路径
    """
    html = render_template(template_name, data)
    # AstrBot 内置 html_render 将 HTML 转为 PNG
    if hasattr(context, "html_render"):
        return context.html_render(html)
    # 回退: 保存为 HTML 文件
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        return f.name


# ── 各模块渲染快捷方法 ─────────────────────────────────

def render_operator_info(context, char: dict, char_id: str) -> str:
    """渲染干员基础信息"""
    data = _prepare_operator_data(char, char_id)
    return render_to_image_path(context, "operatorInfo.html", data)


def render_skills_detail(context, char: dict, char_id: str) -> str:
    """渲染技能详情"""
    data = _prepare_operator_data(char, char_id)
    return render_to_image_path(context, "skillsDetail.html", data)


def render_operator_cost(context, char: dict, char_id: str) -> str:
    """渲染精英化/技能升级材料"""
    data = _prepare_operator_data(char, char_id)
    return render_to_image_path(context, "operatorCost.html", data)


def render_operator_skin(context, skin_data: dict) -> str:
    """渲染皮肤信息"""
    return render_to_image_path(context, "operatorSkin.html", skin_data)


def render_operator_module(context, module_data: dict) -> str:
    """渲染模组信息"""
    return render_to_image_path(context, "operatorModule.html", module_data)


def render_recruit(context, recruit_data: dict) -> str:
    """渲染公招结果"""
    return render_to_image_path(context, "operatorRecruit.html", recruit_data)


def render_material(context, material_data: dict) -> str:
    """渲染材料信息"""
    return render_to_image_path(context, "material.html", material_data)


def render_stage(context, stage_data: dict) -> str:
    """渲染关卡信息"""
    return render_to_image_path(context, "stage.html", stage_data)


def render_enemy(context, enemy_data: dict) -> str:
    """渲染敌人信息"""
    return render_to_image_path(context, "enemyDetail.html", enemy_data)


def render_enemy_index(context, index_data: dict) -> str:
    """渲染敌人索引列表"""
    return render_to_image_path(context, "enemyIndex.html", index_data)


# ── 数据预处理 ─────────────────────────────────────────

def _prepare_operator_data(char: dict, char_id: str) -> dict:
    """将 game_data 的干员数据转为模板需要的格式"""
    from .game_data import ArkData, RARITY_STARS
    from .operator import (
        format_operator_skills, format_operator_modules,
        format_operator_skins, _profession_name,
    )

    data = ArkData()
    rarity = char.get("rarity", 0) + 1

    # 基础信息
    result = {
        "name": char.get("name", "未知"),
        "rarity": rarity,
        "stars": RARITY_STARS.get(rarity, "★" * rarity),
        "profession": _profession_name(char),
        "subProfession": char.get("subProfessionId", ""),
        "tags": char.get("tagList", []),
        "obtain": char.get("itemObtainApproach", ""),
        "description": char.get("description", ""),
        "char_id": char_id,
        "image_path": data.get_char_image_path(char_id, "portrait"),
        "avatar_path": data.get_char_image_path(char_id, "avatar"),
    }

    # 属性
    phases = char.get("phases", [])
    if phases:
        max_phase = phases[-1]
        attrs = max_phase.get("attributesKeyFrames", [{}])[-1].get("data", {})
        result["attributes"] = attrs

    # 技能
    result["skills"] = format_operator_skills(char, char_id)

    # 天赋
    talents = char.get("talents", [])
    result["talents"] = []
    for t in talents:
        candidates = t.get("candidates", [])
        if candidates:
            result["talents"].append({
                "name": candidates[-1].get("name", ""),
                "description": candidates[-1].get("description", ""),
            })

    # 模组
    result["modules"] = format_operator_modules(char)

    # 皮肤
    result["skins"] = format_operator_skins(char_id)

    return result
