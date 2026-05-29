"""
AstrBot Arknights Plugin — 明日方舟游戏数据查询插件

从 AmiyaBot V6 迁移至 AstrBot Star 插件架构。
支持: 干员查询 / 公开招募 / 卡池模拟 / 材料关卡查询

数据源: ArknightsGameResource (Git Submodule)
"""
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain, Image
from astrbot.api import logger

from .src.game_data import ArkData
from .src.operator import format_operator_brief
from .src.recruit import RecruitCalculator
from .src.gacha import GachaPool
from .src.enemy import search_enemy, format_enemy_brief, format_enemy_index_list
from .src.state import check_wait, wait_for
from .src.fuzzy import FuzzyMatcher
from .src.render import render_operator_info, render_recruit, render_enemy, render_enemy_index


class ArknightsPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """插件激活时加载游戏数据"""
        logger.info("[Arknights] 正在初始化插件...")
        try:
            ArkData()  # 触发数据预加载
            logger.info("[Arknights] 游戏数据加载完成")
        except Exception as e:
            logger.error(f"[Arknights] 数据加载失败: {e}")

    async def terminate(self):
        """插件禁用时清理"""
        logger.info("[Arknights] 插件已停止")

    # ── /角色 ──────────────────────────────────────────

    @filter.command("角色")
    async def cmd_character(self, event: AstrMessageEvent):
        """查询干员信息。用法: /角色 干员名"""
        name = event.message_str.replace("/角色", "").strip()
        if not name:
            yield event.plain_result(
                "博士，请输入要查询的干员名。\n用法: /角色 阿米娅"
            )
            return

        data = ArkData()
        char_ids = data.resolve_char(name)

        # 模糊匹配回退
        if not char_ids:
            matcher = FuzzyMatcher()
            all_names = {cid: c["name"] for cid, c in data.chars.items()}
            matches = matcher.match(name, list(all_names.values()))
            if matches:
                # 取最佳匹配的名称 → ID
                best_name = matches[0][0]
                for cid, cname in all_names.items():
                    if cname == best_name:
                        char_ids = [cid]
                        break

        if not char_ids:
            yield event.plain_result(
                f"博士，找不到名为「{name}」的干员，请检查名称。"
            )
            return

        if len(char_ids) > 1:
            names = [
                data.chars[cid]["name"]
                for cid in char_ids[:10]
                if cid in data.chars
            ]
            name_list = "\n".join(f"{i+1}. {n}" for i, n in enumerate(names))
            yield event.plain_result(
                f"博士，找到多个匹配干员：\n{name_list}\n"
                f"请使用 /角色 完整名称 查询。"
            )
            return

        char = data.chars[char_ids[0]]
        text = format_operator_brief(char)

        # 使用原版 AmiyaBot HTML 模板渲染
        try:
            img = await render_operator_info(self.context, char, char_ids[0])
        except Exception:
            img = None

        chain = [Plain(text)]
        if img:
            chain.append(Image.fromFileSystem(img))
        yield event.chain_result(chain)

    # ── /公招 ──────────────────────────────────────────

    @filter.command("公招")
    async def cmd_recruit(self, event: AstrMessageEvent):
        """公开招募标签计算。用法: /公招 标签1 标签2 ..."""
        tags_str = event.message_str.replace("/公招", "").strip()
        if not tags_str:
            yield event.plain_result(
                "博士，请输入招募标签，用空格分隔。\n"
                "例如: /公招 狙击 输出 高级资深干员\n\n"
                "可用标签: 狙击 术师 近卫 重装 辅助 特种 医疗 先锋 "
                "近战位 远程位 输出 防护 生存 治疗 费用回复 支援 削弱 "
                "控场 爆发 召唤 快速复活 位移 减速 资深干员 高级资深干员"
            )
            return

        tags = [t.strip() for t in tags_str.split()]
        calc = RecruitCalculator()

        # 使用全排列优化（标签 ≥2 时）
        if len(tags) >= 2:
            combos = calc.calculate_all_combinations(tags)
            if combos:
                lines = [f"当前可选标签: {', '.join(tags)}\n"]
                lines.append("━━ 推荐组合（按效果排序）━━")
                for i, combo in enumerate(combos[:8]):
                    prefix = "🌟 " if combo["highlight"] else f"{i+1}. "
                    top_op = combo["results"][0][0]
                    stars = "★" * (top_op.rarity + 1)
                    lines.append(
                        f"{prefix}{', '.join(combo['tags'])} "
                        f"→ {stars} {top_op.name} "
                        f"(共 {len(combo['results'])} 名)"
                    )
                yield event.plain_result("\n".join(lines))
                return

        # 单标签或回退到简单计算
        results = calc.calculate(tags)

        if not results:
            yield event.plain_result(
                "博士，这个标签组合没有匹配的干员呢..."
            )
            return

        lines = [f"当前招募标签: {', '.join(tags)}\n"]
        for char, matched_tags in results[:15]:
            stars = "★" * (char.rarity + 1)
            lines.append(
                f"{stars} {char.name} [{char.profession}] "
                f"— 匹配: {', '.join(matched_tags)}"
            )

        if len(results) > 15:
            lines.append(f"\n... 还匹配 {len(results) - 15} 名干员")

        yield event.plain_result("\n".join(lines))

    # ── /抽卡 ──────────────────────────────────────────

    @filter.command("抽卡")
    async def cmd_gacha(self, event: AstrMessageEvent):
        """模拟寻访。用法: /抽卡 [十连]"""
        msg = event.message_str.replace("/抽卡", "").strip()
        is_ten = "十连" in msg or "10" in msg

        pool = GachaPool()
        if is_ten:
            results = pool.ten_pull()
        else:
            results = [pool.single_pull()]

        lines = [f"━━━ {'十连寻访' if is_ten else '单抽'}结果 ━━━"]
        for r in results:
            stars = "★" * r["rarity"]
            lines.append(
                f"{stars} {r['name']} [{r.get('profession', '')}]"
            )
        lines.append("━━━━━━━━━━━━━━━━━")
        lines.append(f"当前保底计数: {pool.pity_counter}")

        six_star = sum(1 for r in results if r["rarity"] == 6)
        if six_star > 0:
            lines.append(f"🌈 出货! {six_star}个六星!")

        yield event.plain_result("\n".join(lines))

    # ── /材料 ──────────────────────────────────────────

    @filter.command("材料")
    async def cmd_material(self, event: AstrMessageEvent):
        """查询材料信息。用法: /材料 材料名"""
        name = event.message_str.replace("/材料", "").strip()
        if not name:
            yield event.plain_result(
                "博士，请输入要查询的材料名。\n用法: /材料 固源岩"
            )
            return

        from .src.material import search_material, format_material_info
        results = search_material(name)

        # 模糊回退
        if not results:
            matcher = FuzzyMatcher()
            items = ArkData().items
            all_names = {iid: it["name"] for iid, it in items.items() if "name" in it}
            matches = matcher.match(name, list(all_names.values()))
            if matches:
                best = matches[0][0]
                for iid, iname in all_names.items():
                    if iname == best:
                        results = [{"id": iid, **items[iid]}]
                        break

        if not results:
            yield event.plain_result(f"博士，找不到材料「{name}」")
            return

        text = format_material_info(results[0])
        yield event.plain_result(text)

    # ── /关卡 ──────────────────────────────────────────

    @filter.command("关卡")
    async def cmd_stage(self, event: AstrMessageEvent):
        """查询关卡信息。用法: /关卡 关卡名"""
        name = event.message_str.replace("/关卡", "").strip()
        if not name:
            yield event.plain_result(
                "博士，请输入要查询的关卡名。\n用法: /关卡 1-7"
            )
            return

        from src.stage import search_stage, format_stage_info
        results = search_stage(name)
        if not results:
            yield event.plain_result(f"博士，找不到关卡「{name}」")
            return

        text = format_stage_info(results[0])
        # 显示难度标签
        diff_label = results[0].get("_difficulty_label", "")
        if diff_label:
            text = f"【{diff_label}模式】\n{text}"
        yield event.plain_result(text)

    # ── /敌人 ──────────────────────────────────────────

    @filter.command("敌人")
    async def cmd_enemy(self, event: AstrMessageEvent):
        """查询敌方单位。用法: /敌人 名称"""
        name = event.message_str.replace("/敌人", "").strip()
        if not name:
            yield event.plain_result(
                "博士，请输入要查询的敌方单位名称。\n用法: /敌人 源石虫"
            )
            return

        results = search_enemy(name)
        if not results:
            yield event.plain_result(
                f"博士，没有找到与「{name}」相关的敌方单位。"
            )
            return

        # 精确匹配
        exact = [e for e in results if e["name"] == name]
        if len(exact) == 1:
            text = format_enemy_brief(exact[0])
            yield event.plain_result(text)
            return

        # 单个结果直接返回
        if len(results) == 1:
            yield event.plain_result(format_enemy_brief(results[0]))
            return

        # 多个结果，让用户选择
        uid = event.get_sender_id() if hasattr(event, 'get_sender_id') else str(id(event))
        wait_for(uid, "enemy_select", {"results": results})
        yield event.plain_result(format_enemy_index_list(results))

    @filter.regex(r"^\d+$")
    async def handle_index_select(self, event: AstrMessageEvent):
        """处理多结果序号选择（状态机）"""
        uid = event.get_sender_id() if hasattr(event, 'get_sender_id') else str(id(event))
        state = check_wait(uid)
        if not state:
            return  # 不是等待状态，不处理

        try:
            idx = int(event.message_str.strip()) - 1
        except ValueError:
            yield event.plain_result("博士，请输入有效的数字序号。")
            return

        results = state["context"].get("results", [])
        step = state["step"]

        if step == "enemy_select":
            if 0 <= idx < len(results):
                yield event.plain_result(format_enemy_brief(results[idx]))
            else:
                yield event.plain_result(
                    f"博士，请输入 1 到 {len(results)} 之间的序号。"
                )

    # ── /arkhelp ───────────────────────────────────────

    @filter.command("arkhelp")
    async def cmd_help(self, event: AstrMessageEvent):
        """显示插件帮助"""
        help_text = (
            "━━━ 明日方舟插件帮助 ━━━\n"
            "/角色 <名称>    查询干员信息\n"
            "/公招 <标签...>  公开招募标签计算\n"
            "/抽卡 [十连]     模拟寻访\n"
            "/材料 <名称>     查询材料信息\n"
            "/关卡 <编号>     查询关卡信息\n"
            "/arkhelp         显示此帮助"
        )
        yield event.plain_result(help_text)
