"""
AstrBot Arknights Plugin — 严格对齐 AmiyaBot

完整集成 5 个 AmiyaBot 插件:
- operator (6_2): 干员查询 + 技能 + 材料 + 模组 + 皮肤 + 语音 + 档案
- enemy (3_7):   敌方单位查询
- gamedata (4_0): 游戏数据加载（Operator 模型）
- material (2_8): 材料物品查询
- recruit (3_1):  公开招募标签计算
- stages (2_7):   关卡查询
"""

import asyncio
import os
from typing import Optional
from dataclasses import dataclass, field

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain, Image
from astrbot.api import logger

from .src.game_data import ArknightsGameData, ArknightsGameResource
from .src.operator_model import Operator
from .src.operator_info import OperatorInfo
from .src.operator_core import (
    OperatorSearchInfo, search_info, FuncsVerify,
    get_index, find_most_similar, any_match, get_index_from_text,
)
from .src.operator_data import OperatorData
from .src.render import render_operator_info, render_template, render_to_image
from .src.resource import initialize_resource

_curr_dir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEVEL = 8


# ════════════════════════════════════════════════════════
# 内部路由系统
# ════════════════════════════════════════════════════════

@dataclass
class _Route:
    group_id: str
    keywords: list
    verify: any
    level: int
    handler: any


class _Router:
    def __init__(self):
        self._routes: list[_Route] = []

    def on_message(self, group_id="operator", keywords=None, verify=None, level=DEFAULT_LEVEL):
        def decorator(handler):
            self._routes.append(_Route(group_id, keywords or [], verify, level, handler))
            return handler
        return decorator

    async def dispatch(self, event: AstrMessageEvent):
        text = event.message_str
        matched = []
        for route in self._routes:
            if route.verify:
                result = await route.verify(text) if asyncio.iscoroutinefunction(route.verify) else route.verify(text)
                # AmiyaBot verify 返回 (bool, level, info) 三元组
                if isinstance(result, tuple) and len(result) >= 3:
                    verified, level, keypoint = result[0], result[1], result[2]
                else:
                    verified, keypoint = result if len(result) == 2 else (result[0], None)
                    level = route.level
                if verified: matched.append((route, level, keypoint))
            elif route.keywords is not None and (any_match(text, route.keywords) if route.keywords else True):
                matched.append((route, route.level, None))
        if not matched:
            return None
        matched.sort(key=lambda x: -x[1])
        best_route, _, keypoint = matched[0]
        try:
            return best_route.handler(event, keypoint)
        except Exception as e:
            logger.error(f"[Arknights] Handler error: {e}", exc_info=True)
            return None


router = _Router()


# ════════════════════════════════════════════════════════
# 插件入口
# ════════════════════════════════════════════════════════

class ArknightsPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("[Arknights] 正在初始化插件...")
        try:
            self._ensure_chromium()
            initialize_resource()
            ArknightsGameData()
            OperatorInfo.ensure_initialized()

            # 初始化子系统
            from .src.material import MaterialData
            await MaterialData.init_materials()

            from .src.stage import Stage
            await Stage.init_stages()

            logger.info(
                f"[Arknights] 加载完成: {len(ArknightsGameData().operators)} 干员, "
                f"{len(MaterialData.materials)} 材料, "
                f"{len(ArknightsGameData().stages)} 关卡, "
                f"{len(ArknightsGameData().enemies)} 敌人"
            )
        except Exception as e:
            logger.error(f"[Arknights] 初始化失败: {e}", exc_info=True)

    async def terminate(self):
        logger.info("[Arknights] 插件已停止")

    @staticmethod
    def _ensure_chromium():
        import subprocess, sys, platform
        try:
            from playwright.sync_api import sync_playwright
            p = sync_playwright().start()
            try: p.chromium.launch(headless=True).close(); return
            except: pass
            finally: p.stop()
        except: pass
        logger.info("[Arknights] 安装 Playwright Chromium...")
        cmd = [sys.executable, "-m", "playwright", "install"]
        if platform.system() == "Linux": cmd.append("--with-deps")
        cmd.append("chromium")
        subprocess.run(cmd, check=False)

    # ── AstrBot 表面命令入口 ──────────────────────────

    @filter.command("角色")
    async def cmd_character(self, event):
        async for item in self._route_dispatch(event):
            yield item

    @filter.command("公招")
    async def cmd_recruit(self, event):
        tags_str = event.message_str.replace("/公招", "").replace("公招", "").strip()
        if not tags_str:
            yield event.plain_result("博士，请输入招募标签，用空格分隔。\n例如: /公招 狙击 输出")
            return
        from .src.recruit import RecruitCalculator
        tags = [t.strip() for t in tags_str.split()]
        calc = RecruitCalculator()
        if len(tags) >= 2:
            combos = calc.calculate_all_combinations(tags)
            if combos:
                lines = [f"当前可选标签: {', '.join(tags)}\n", "━━ 推荐组合 ━━"]
                for i, c in enumerate(combos[:8]):
                    top = c["results"][0][0]
                    lines.append(f"{i+1}. {', '.join(c['tags'])} → {'★'*top.rarity} {top.name}")
                yield event.plain_result("\n".join(lines)); return
        results = calc.calculate(tags)
        if not results:
            yield event.plain_result("博士，这个标签组合没有匹配的干员呢..."); return
        lines = [f"当前招募标签: {', '.join(tags)}\n"]
        for char, mt in results[:15]:
            lines.append(f"{'★'*char.rarity} {char.name} [{char.profession}] — 匹配: {', '.join(mt)}")
        yield event.plain_result("\n".join(lines))

    @filter.command("抽卡")
    async def cmd_gacha(self, event):
        from .src.gacha import GachaPool
        msg = event.message_str.replace("/抽卡", "").strip()
        is_ten = "十连" in msg or "10" in msg
        pool = GachaPool()
        results = pool.ten_pull() if is_ten else [pool.single_pull()]
        lines = [f"━━━ {'十连寻访' if is_ten else '单抽'}结果 ━━━"]
        for r in results: lines.append(f"{'★'*r['rarity']} {r['name']}")
        yield event.plain_result("\n".join(lines))

    @filter.command("材料")
    async def cmd_material(self, event):
        name = event.message_str.replace("/材料", "").replace("材料", "").strip()
        if not name: yield event.plain_result("博士，请输入材料名。\n用法: /材料 固源岩"); return
        from .src.material import MaterialData
        result = MaterialData.check_material(name)
        if not result:
            yield event.plain_result(f"博士，找不到材料「{name}」"); return
        info = result["info"]
        lines = [f"【{info['material_name']}】", info.get("material_desc", "")]
        children = result.get("children", [])
        if children:
            lines.append(f"\n合成配方 ({len(children)}个材料):")
            for c in children[:8]:
                lines.append(f"  · {c.get('material_name','?')} x{c.get('use_number',1)}")
        src = result.get("source", {})
        main_src = src.get("main", [])
        act_src = src.get("act", [])
        if main_src:
            lines.append(f"\n主线掉落: {', '.join(s['code'] for s in main_src[:5])}")
        if act_src:
            lines.append(f"活动掉落: {', '.join(s['code'] for s in act_src[:5])}")
        yield event.plain_result("\n".join(lines))

    @filter.command("关卡")
    async def cmd_stage(self, event):
        text = event.message_str.replace("/关卡", "").replace("关卡", "").strip()
        if not text: yield event.plain_result("博士，请输入关卡名或代号。\n用法: /关卡 1-7"); return
        from .src.stage import Stage, format_stage_info
        result = Stage.search(text)
        if not result:
            yield event.plain_result(f"博士，找不到关卡「{text}」"); return
        if result.get("multi"):
            ids = result["stage_ids"]
            gd = ArknightsGameData()
            lines = ["博士，找到以下同名关卡:\n"]
            for i, sid in enumerate(ids):
                s = gd.stages.get(sid, {})
                lines.append(f"  {i+1}. {s.get('code','?')} {s.get('name','?')}")
            yield event.plain_result("\n".join(lines))
        else:
            s = result["result"]
            yield event.plain_result(format_stage_info(s))

    @filter.command("敌人")
    async def cmd_enemy(self, event):
        name = event.message_str.replace("/敌人", "").replace("敌人", "").strip()
        if not name: yield event.plain_result("博士，请输入敌方单位名称。\n用法: /敌人 源石虫"); return
        from .src.enemy import Enemy, format_enemy_brief, format_enemy_index_list
        results = Enemy.find_enemies(name)
        if not results:
            yield event.plain_result(f"博士，没有找到敌方单位「{name}」的资料 >.<"); return
        if len(results) == 1:
            res = Enemy.get_enemy(results[0][0])
            if res:
                img_data = {**res, "search": name}
                img = await render_template("enemy.html", img_data)
                if img: yield event.chain_result([Image.fromFileSystem(img)]); return
        # 多结果: 列表
        from .src.state import wait_for
        uid = event.get_sender_id() if hasattr(event, 'get_sender_id') else str(id(event))
        wait_for(uid, "enemy_select", {"results": results})
        init = {"search": name, "result": {r[0]: r[1] for r in results}}
        img = await render_template("enemyIndex.html", init)
        if img: yield event.chain_result([Image.fromFileSystem(img)])
        else: yield event.plain_result(format_enemy_index_list([r[1] for r in results]))

    @filter.command("arkhelp")
    async def cmd_help(self, event):
        yield event.plain_result(
            "━━━ 明日方舟插件 ━━━\n"
            "/角色 <名称>   干员信息\n"
            "/公招 <标签>   招募标签\n"
            "/抽卡 [十连]   模拟寻访\n"
            "/材料 <名称>   材料查询\n"
            "/关卡 <编号>   关卡信息\n"
            "/敌人 <名称>   敌方单位\n"
            "/arkhelp       帮助"
        )

    @filter.regex(r"^\d+$")
    async def handle_index_select(self, event: AstrMessageEvent):
        from .src.state import check_wait
        uid = event.get_sender_id() if hasattr(event, 'get_sender_id') else str(id(event))
        state = check_wait(uid)
        if not state: return
        try: idx = int(event.message_str.strip()) - 1
        except ValueError: yield event.plain_result("请输入有效数字序号。"); return
        step = state["step"]
        if step == "enemy_select":
            from .src.enemy import Enemy, format_enemy_brief
            results = state["context"].get("results", [])
            if 0 <= idx < len(results):
                res = Enemy.get_enemy(results[idx][0])
                if res:
                    img_data = {**res, "search": results[idx][0]}
                    img = await render_template("enemy.html", img_data)
                    if img: yield event.chain_result([Image.fromFileSystem(img)])
                    else: yield event.plain_result("渲染失败")

    @filter.regex(r"^(?![/!！]|角色|公招|抽卡|材料|关卡|敌人|arkhelp)")
    async def handle_natural(self, event):
        async for item in self._route_dispatch(event):
            yield item

    async def _route_dispatch(self, event):
        result = await router.dispatch(event)
        if result is None:
            return
        if hasattr(result, "__aiter__"):
            async for item in result:
                yield item
        elif result is not None:
            yield result


# ════════════════════════════════════════════════════════
# 路由注册 — 对齐 AmiyaBot main.py 顺序
# ════════════════════════════════════════════════════════

# ── 模组 ──
@router.on_message(keywords=["模组"])
async def op_module(event, _):
    info = search_info(event.message_str, source_keys=["name"])
    if not info.name: yield event.plain_result("博士，请说明需要查询的干员名"); return
    if info.name not in ArknightsGameData().operators: yield event.plain_result(f"博士，没有找到干员「{info.name}」"); return
    is_story = "故事" in event.message_str
    result = OperatorData.find_operator_module(info, is_story)
    if not result: yield event.plain_result(f"博士，干员{info.name}尚未拥有模组"); return
    if is_story: yield event.plain_result(result); return
    img = await render_template("operatorModule.html", result)
    if img: yield event.chain_result([Image.fromFileSystem(img)])

# ── 皮肤 ──
@router.on_message(keywords=["皮肤", "立绘"])
async def op_skin(event, _):
    info = search_info(event.message_str, source_keys=["skin_key", "name"])
    gd = ArknightsGameData()
    opt = None; skin_item = None
    if info.skin_key: skin_item = OperatorInfo.skins_map.get(info.skin_key)
    else:
        if not info.name: yield event.plain_result("博士，请说明需要查询的干员名"); return
        if info.name not in gd.operators: yield event.plain_result(f"博士，没有找到干员「{info.name}」"); return
        opt = gd.operators[info.name]; skins = opt.skins()
        idx = get_index(event.message_str, skins)
        if idx is None:
            text = f"博士，这是干员{info.name}的立绘列表\n\n"
            for i, s in enumerate(skins): text += f"[{i+1}] {s['skin_name']}\n"
            text += "\n回复【序号】查询"; yield event.plain_result(text); return
        skin_item = skins[min(idx, len(skins)-1)]
    if skin_item:
        if not opt: opt = gd.operators.get(skin_item["char_name"])
        sd = {"name": opt.name if opt else "", "data": skin_item, "path": ArknightsGameResource.get_skin_file(skin_item, encode_url=True)}
        img = await render_template("operatorSkin.html", sd)
        if img: yield event.chain_result([Image.fromFileSystem(img)])

# ── 精英化/材料 ──
@router.on_message(verify=FuncsVerify.level_up)
async def op_level_up(event, keypoint):
    info: OperatorSearchInfo = keypoint
    if not info.name: yield event.plain_result("博士，请说明需要查询的干员名"); return
    if "材料" in event.message_str:
        if info.char and info.char.rarity <= 2: yield event.plain_result(f"博士，干员{info.name}不需要消耗材料进行升级哦~"); return
        result = await OperatorData.get_level_up_cost(info); template_name = "operatorCost.html"
    else:
        if info.char and info.char.rarity <= 2: yield event.plain_result(f"博士，干员{info.name}没有技能哦~"); return
        result = await OperatorData.get_skills_detail(info); template_name = "skillsDetail.html"
    if not result: yield event.plain_result("博士，请仔细描述想要查询的信息哦"); return
    img = await render_template(template_name, result)
    if img: yield event.chain_result([Image.fromFileSystem(img)])

# ── 阵营 ──
@router.on_message(keywords=["阵营"])
async def op_group(event, _):
    groups = OperatorInfo.operator_group_map
    def c(op): return f"<span style=\"color: {'#FF4343' if op.rarity>=6 else '#FEA63A' if op.rarity>=5 else '#A288B5'}\">{op.name}</span>"
    text = "|阵营名|干员|\n|----|----|\n"
    for gn in sorted(groups.keys()): text += f"|{gn}|{'、'.join(c(o) for o in groups[gn])}|\n"
    yield event.plain_result(text)

# ── 干员信息 ──
@router.on_message(verify=FuncsVerify.operator)
async def op_info(event, keypoint):
    info: OperatorSearchInfo = keypoint
    if "技能" in event.message_str:
        if info.char and info.char.rarity <= 2: yield event.plain_result(f"博士，干员{info.name}没有技能哦~"); return
        result = await OperatorData.get_skills_detail(info)
        if result:
            img = await render_template("skillsDetail.html", result)
            if img: yield event.chain_result([Image.fromFileSystem(img)]); return
    else:
        result, tokens = await OperatorData.get_operator_detail(info)
        if result:
            msgs = []
            if "召唤物" not in event.message_str:
                img = await render_operator_info(None, result, "")
                if img: msgs.append(Image.fromFileSystem(img))
            if tokens and tokens.get("tokens"):
                if "召唤物" in event.message_str:
                    img = await render_template("operatorToken.html", tokens)
                    if img: msgs.append(Image.fromFileSystem(img))
            if msgs: yield event.chain_result(msgs); return
    yield event.plain_result("博士，请仔细描述想要查询的信息哦")

# ── 默认干员查询 ──
@router.on_message(keywords=[], level=DEFAULT_LEVEL - 1)
async def op_default(event, _):
    info = search_info(event.message_str, source_keys=["name"])
    if not info.name: return
    result, tokens = await OperatorData.get_operator_detail(info)
    if not result: return
    img = await render_operator_info(None, result, "")
    if img: yield event.chain_result([Image.fromFileSystem(img)])
    else:
        op = info.char
        if op:
            d, _ = op.detail()
            yield event.plain_result(f"【{op.name}】{'★'*op.rarity}\n职业: {op.classes} | {op.classes_sub}\n生命: {d.get('maxHp','?')} | 攻击: {d.get('atk','?')} | 防御: {d.get('def','?')} | 费用: {d.get('cost','?')}")

# ── 材料查询 (自然语言) ──
@router.on_message(keywords=["材料"], level=6)
async def mat_natural(event, _):
    name = event.message_str.replace("材料", "").replace("阿米娅", "").strip()
    if not name: yield event.plain_result("博士，请说明需要查询的材料名称"); return
    from .src.material import MaterialData
    result = MaterialData.check_material(name)
    if not result:
        n = find_most_similar(name, MaterialData.materials)
        if n: result = MaterialData.check_material(n)
    if result:
        info = result["info"]
        lines = [f"【{info['material_name']}】", info.get("material_desc", "")]
        children = result.get("children", [])
        if children:
            lines.append(f"\n合成配方:")
            for c in children[:5]: lines.append(f"  · {c.get('material_name','?')} x{c.get('use_number',1)}")
        yield event.plain_result("\n".join(lines))
    else: yield event.plain_result(f"博士，没有找到材料「{name}」的资料 >.<")

# ── 敌方单位查询 ──
@router.on_message(keywords=["敌人", "敌方", "查询"], level=5)
async def enemy_router(event, _):
    from .src.enemy import Enemy, format_enemy_brief, format_enemy_index_list
    import re
    r = re.search(r"(/)?(敌[人|方])?(单位)?(资料)?(.*)", event.message_str)
    name_char = r.group(5).strip() if r else ""
    if not name_char:
        yield event.plain_result("博士，请说明需要查询的敌方单位名称"); return
    results = Enemy.find_enemies(name_char)
    if not results:
        yield event.plain_result(f"博士，没有找到敌方单位{name_char}的资料 >.<"); return
    if len(results) == 1:
        res = Enemy.get_enemy(results[0][0])
        if res:
            img_data = {**res, "search": name_char}
            img = await render_template("enemy.html", img_data)
            if img: yield event.chain_result([Image.fromFileSystem(img)]); return
    from .src.state import wait_for
    uid = event.get_sender_id() if hasattr(event, 'get_sender_id') else str(id(event))
    wait_for(uid, "enemy_select", {"results": results})
    yield event.plain_result(format_enemy_index_list([r[1].get("info", r[1]) for r in results]) + "\n回复【序号】查看详情")

# ── 地图/关卡查询 ──
@router.on_message(keywords=["地图", "关卡"], level=5)
async def stage_router(event, _):
    from .src.stage import Stage, format_stage_info
    text = event.message_str.strip()
    result = Stage.search(text)
    if result:
        if result.get("multi"):
            ids = result["stage_ids"]
            gd = ArknightsGameData()
            lines = ["博士，找到以下同名关卡:\n"]
            for i, sid in enumerate(ids): lines.append(f"  {i+1}. {gd.stages.get(sid,{}).get('code','?')} {gd.stages.get(sid,{}).get('name','?')}")
            yield event.plain_result("\n".join(lines))
        else: yield event.plain_result(format_stage_info(result["result"]))
        return
    activity = Stage.search_activity(text)
    if activity:
        for aname, adata in activity.items():
            if isinstance(adata, dict):
                lines = [f"博士，以下是活动【{aname}】的关卡列表:\n"]
                for i, (sid, sdata) in enumerate(list(adata.items())):
                    lines.append(f"  {sdata.get('code','?')} {sdata.get('name','?')}")
                yield event.plain_result("\n".join(lines[:30])); return
    yield event.plain_result("抱歉博士，没有查询到相关地图信息")
