"""
本地 Playwright 渲染 — 复刻 AmiyaBot 的方案

用无头 Chromium 加载 Vue 模板（file:// 协议），
注入数据后截图。所有本地资源（CSS/JS/图片）直接可用。
"""

import json
import os
import tempfile
from pathlib import Path

_playwright = None
_browser = None

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _get_playwright():
    global _playwright
    if _playwright is None:
        from playwright.async_api import async_playwright
        _playwright = async_playwright
    return _playwright


async def _get_browser():
    global _browser
    if _browser is None:
        import os as _os
        pw = _get_playwright()
        p = await pw().__aenter__()
        # Playwright 1.60+ uses headless shell, fall back to old chromium
        exe = None
        local_appdata = _os.environ.get("LOCALAPPDATA", _os.path.expanduser("~/AppData/Local"))
        for ver in ["1223", "1179", "1150", "1124"]:
            candidates = [
                f"{local_appdata}/ms-playwright/chromium-{ver}/chrome-win/chrome.exe",
                f"{local_appdata}/ms-playwright/chromium_headless_shell-{ver}/chrome-headless-shell-win64/chrome-headless-shell.exe",
            ]
            for c in candidates:
                if _os.path.exists(c):
                    exe = c
                    break
            if exe:
                break
        _browser = await p.chromium.launch(
            headless=True,
            executable_path=exe if exe else None,
            args=["--no-sandbox"],
        )
    return _browser


async def render_to_image(html_path: str, data: dict, width: int = 800) -> str | None:
    """用 Playwright 加载本地 HTML 文件，注入数据，截图返回路径"""
    try:
        browser = await _get_browser()
        page = await browser.new_page(viewport={"width": width, "height": 1000})

        # 加载本地 HTML（file:// 协议，所有相对路径自动解析）
        await page.goto(f"file:///{html_path}", wait_until="domcontentloaded")

        # 注入数据（AmiyaBot 方式：window.init = this.init → init(data)）
        data_json = json.dumps(data, ensure_ascii=False)
        await page.evaluate(f"window.init({data_json})")

        # 等待 Vue 渲染完成
        await page.wait_for_timeout(500)

        # 截图
        output = str(Path(tempfile.gettempdir()) / f"arknights_{os.getpid()}.png")
        await page.screenshot(path=output, full_page=True)
        await page.close()
        return output
    except Exception as e:
        from astrbot.api import logger
        logger.error(f"[Arknights] Playwright 渲染失败: {e}")
        return None


# ── 数据准备（对齐 AmiyaBot operatorData.py）─────────

PROF_CN = {"WARRIOR":"近卫","SNIPER":"狙击","TANK":"重装","MEDIC":"医疗","SUPPORT":"辅助","CASTER":"术师","SPECIAL":"特种","PIONEER":"先锋"}

TEAM_TABLE = {"rhodes":"罗德岛","penguin":"企鹅物流","blacksteel":"黑钢国际","rhine":"莱茵生命","kappa":"喀兰贸易","sweep":"S.W.E.E.P","yan":"炎","lgd":"龙门近卫局","lungmen":"龙门","siracusa":"叙拉古","victoria":"维多利亚","ursus":"乌萨斯","columbia":"哥伦比亚","sargon":"萨尔贡","higashi":"东国","laterano":"拉特兰","leithanien":"莱塔尼亚","kazimierz":"卡西米尔","rim":"雷姆必拓","iberia":"伊比利亚","kjerag":"谢拉格","dublinn":"深池","egir":"阿戈尔","abyssal":"深海猎人","followers":"使徒","babel":"巴别塔","glasgow":"格拉斯哥帮"}


async def render_operator_info(star_self, char: dict, char_id: str) -> str | None:
    """渲染干员信息 — Playwright 本地截图"""
    name = char.get("name", "")
    rarity = char.get("rarity", 0) + 1
    phases = char.get("phases", [])
    mp = phases[-1] if phases else {}
    a = mp.get("attributesKeyFrames", [{}])[-1].get("data", {})

    # 天赋
    talents = []
    for t in char.get("talents", []):
        for c in t.get("candidates", []):
            n = c.get("name", "")
            if n and "？" not in n:
                talents.append({"talents_name": n, "talents_desc": c.get("description","")})
                break

    # 技能
    skill_list = []
    skills_desc = {}
    for i, sk in enumerate(char.get("skills", [])):
        sid = sk.get("skillId", "")
        sdata = _load_skill(sid)
        lvs = sdata.get("levels", [])
        nm = lvs[0].get("name", f"技能{sid}") if lvs else f"技能{sid}"
        skill_list.append({"skill_no": i, "skill_name": nm, "skill_icon": f"skill_icon_{sid}"})
        descs = []
        for lv in lvs:
            descs.append({"sp_type": lv.get("spData",{}).get("spType",1), "sp_init": lv.get("spData",{}).get("initSp",0),
                          "sp_cost": lv.get("spData",{}).get("spCost",0), "duration": lv.get("duration",0),
                          "skill_type": lv.get("skillType",0), "description": lv.get("description",""), "range":""})
        skills_desc[i] = descs

    # 潜能
    potential = [{"potential_rank": r.get("type",0), "potential_desc": r.get("description","")} for r in char.get("potentialRanks",[])]

    data = {
        "info": {
            "name": name, "en_name": char.get("appellation","") or "",
            "number": char.get("displayNumber","") or "", "rarity": rarity,
            "classes": PROF_CN.get(char.get("profession",""), char.get("profession","")),
            "classes_sub": char.get("subProfessionId",""),
            "nation": TEAM_TABLE.get(char.get("nationId",""), char.get("nationId","") or ""),
            "group": TEAM_TABLE.get(char.get("groupId",""), char.get("groupId","") or ""),
            "team": TEAM_TABLE.get(char.get("teamId",""), char.get("teamId","") or ""),
            "race": "", "drawer": "", "birthday": "",
            "tags": char.get("tagList",[]), "is_sp": char.get("isSpChar", False),
            "profile": char.get("itemUsage","") or "", "impression": char.get("itemDesc","") or "",
            "potential_item": "", "range": "", "real_name": [], "cv": {},
        },
        "detail": {"maxHp": a.get("maxHp",0), "atk": a.get("atk",0), "def": a.get("def",0),
                   "magicResistance": a.get("magicResistance",0), "attackSpeed": a.get("attackSpeed",100),
                   "baseAttackTime": a.get("baseAttackTime",0), "blockCnt": a.get("blockCnt",1),
                   "cost": a.get("cost",0), "respawnTime": a.get("respawnTime",0),
                   "operator_trait": char.get("description","") or ""},
        "trust": {}, "talents": talents, "potential": potential,
        "building_skills": [], "skill_list": skill_list, "skills_desc": skills_desc,
        "modules": [], "skin": f"../../data/ArknightsGameResource/portrait/{char_id}_1.png",
    }

    html_path = str(TEMPLATE_DIR / "operatorInfo.html")
    return await render_to_image(html_path, data)


def _load_skill(sid: str) -> dict:
    try:
        p = DATA_DIR / "ArknightsGameResource" / "gamedata" / "excel" / "skill_table.json"
        return json.loads(p.read_text("utf-8")).get(sid, {})
    except Exception:
        return {}
