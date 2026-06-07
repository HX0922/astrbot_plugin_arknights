"""
关卡查询模块 — 对齐 AmiyaBot amiyabot-arknights-stages-2_7

提供:
- Stage.init_stages() — 构建 jieba 词库
- 关卡搜索 (jidba 分词 + stages_map 匹配)
- 活动列表查询
- 难度后缀处理 (_hard/_easy/_tough)
"""

import re
import os
import jieba
from .game_data import ArknightsGameData, remove_punctuation
from .operator_core import any_match, get_index_from_text


def create_dir(path: str, is_file: bool = False):
    if is_file:
        path = os.path.dirname(path)
    if path and not os.path.exists(path):
        os.makedirs(path)
    return path


class Stage:
    """关卡查询 — 对齐 AmiyaBot Stage"""

    _initialized = False

    @staticmethod
    async def init_stages():
        """构建关卡 jieba 词库"""
        import os
        gd = ArknightsGameData()
        stages = list(gd.stages_map.keys()) + list(gd.side_story_map.keys())

        cache_dir = "data/plugins/stages"
        plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cache_path = os.path.join(plugin_root, cache_dir)
        create_dir(cache_path)

        dict_file = os.path.join(cache_path, "stages.txt")
        with open(dict_file, mode="w", encoding="utf-8") as f:
            f.write("\n".join([f"{name} 500 n" for name in stages if name]))

        jieba.load_userdict(dict_file)
        Stage._initialized = True

    @classmethod
    def search(cls, text: str) -> dict | None:
        """搜索关卡 — 返回完整结果或 None"""
        gd = ArknightsGameData()

        level = ""
        level_str = ""
        if any_match(text, ["突袭"]):
            level = "_hard"
            level_str = "（突袭）"
        if any_match(text, ["简单", "剧情"]):
            level = "_easy"
            level_str = "（剧情）"
        if any_match(text, ["困难", "磨难"]):
            level = "_tough"
            level_str = "（磨难）"

        words = jieba.lcut(remove_punctuation(text, ["-"]).upper().replace(" ", ""))
        stages_map = gd.stages_map

        stage_ids = []
        for item in words:
            stage_key = item + level
            if stage_key in stages_map:
                stage_ids = stages_map[stage_key]

        if not stage_ids:
            return None

        if len(stage_ids) == 1:
            stage_id = stage_ids[0]
        else:
            # 多个同名关卡 → 返回列表供选择
            return {"multi": True, "stage_ids": stage_ids, "level_str": level_str}

        stage_data = gd.stages.get(stage_id)
        if not stage_data:
            return None

        res = {
            **stage_data,
            "name": stage_data["name"] + level_str,
            "zones": 0,
        }

        if level == "_easy":
            main_level = gd.stages.get(stage_id.replace("easy", "main"))
            if main_level:
                res["levelData"] = main_level.get("levelData")

        # 替换地图 ID（简化版：不做 map path 处理）
        res["stageId"] = stage_id.replace("#f#", "")

        return {"multi": False, "result": res}

    @classmethod
    def search_activity(cls, text: str):
        """搜索活动"""
        gd = ArknightsGameData()
        words = jieba.lcut(remove_punctuation(text, ["-"]).upper().replace(" ", ""))
        side_story_map = gd.side_story_map

        for key in words:
            if key in side_story_map:
                return {key: side_story_map[key]}

        # 活动列表
        if "活动" in text:
            return {act: data for act, data in reversed(side_story_map.items())}

        return None


def format_stage_info(stage: dict) -> str:
    """格式化关卡信息为纯文本"""
    code = stage.get("code", "") or ""
    name = stage.get("name", "") or ""
    ap = stage.get("apCost", "?")
    diff = stage.get("difficulty", "")
    
    lines = [
        f"【{code}】{name}",
        f"理智消耗: {ap}",
    ]

    if diff:
        lines.append(f"难度: {diff}")
    
    drops = stage.get("dropInfos", [])
    if drops:
        lines.append("掉落:")
        for d in drops[:10]:
            item = d.get("itemName") or d.get("info", {}).get("material_name", "")
            if item:
                lines.append(f"  · {item}")
    
    level_data = stage.get("levelData")
    if level_data:
        enemies = level_data.get("enemy", [])
        if enemies:
            lines.append(f"敌人数量: {len(enemies)}")

    return "\n".join(lines)
