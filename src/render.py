"""
HTML 模板渲染 — 纯 Python 字符串拼接，不依赖 Jinja2
"""

from pathlib import Path


def _load_html(name: str) -> str:
    path = Path(__file__).resolve().parent.parent / "templates" / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


async def _render_raw(star_self, html: str) -> str | None:
    """发送纯 HTML 到 T2I，数据已内联，无需 Jinja2"""
    try:
        return await star_self.html_render(html, {})
    except Exception:
        return None


PROF_CN = {
    "WARRIOR": "近卫", "SNIPER": "狙击", "TANK": "重装",
    "MEDIC": "医疗", "SUPPORT": "辅助", "CASTER": "术师",
    "SPECIAL": "特种", "PIONEER": "先锋",
}


async def render_operator_info(star_self, char: dict, char_id: str) -> str | None:
    """渲染干员信息 — 纯 Python 拼 HTML，不经过 Jinja2"""
    name = char.get("name", "?")
    rarity = char.get("rarity", 0) + 1
    stars = "★" * rarity
    prof = PROF_CN.get(char.get("profession", ""), char.get("profession", ""))
    sub = char.get("subProfessionId", "")
    phases = char.get("phases", [])
    max_phase = phases[-1] if phases else {}
    attrs = max_phase.get("attributesKeyFrames", [{}])[-1].get("data", {})

    hp = str(attrs.get("maxHp", "?"))
    atk = str(attrs.get("atk", "?"))
    def_ = str(attrs.get("def", "?"))
    mres = str(attrs.get("magicResistance", "?"))
    cost = str(attrs.get("cost", "?"))
    block = str(attrs.get("blockCnt", "?"))

    tags_html = " ".join(
        f'<span class="tag">{t}</span>' for t in char.get("tagList", [])
    )

    talent = "无"
    for t in char.get("talents", []):
        for c in t.get("candidates", []):
            if c.get("name") and "？" not in c.get("name", ""):
                talent = c.get("name", "")
                break

    obtain = char.get("itemObtainApproach", "") or ""
    desc = (char.get("description", "") or "")[:150]

    # 立绘
    portrait_url = f"https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/portrait/{char_id}_1.png"
    portrait_html = f'<img src="{portrait_url}" style="max-width:100%;border-radius:5px;margin-top:10px">'

    tmpl = _load_html("test.html")
    html = tmpl % (
        name, stars, prof, sub, hp, atk, def_, mres, cost, block,
        tags_html, talent, obtain, desc, portrait_html,
    )

    return await _render_raw(star_self, html)
