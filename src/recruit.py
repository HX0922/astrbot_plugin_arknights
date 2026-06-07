"""
公开招募标签计算模块 — 严格对齐 AmiyaBot recruit/main.py 算法

核心对齐点:
- find_operator_tags_by_tags() — 按标签筛选可公招干员
- all_match() — 检查组合标签是否全部命中
- find_combinations() — 生成标签组合（最多3个）
- 资深干员/高级资深干员标签过滤
- 按 tags 数量 + max_rarity 排序结果

框架差异:
- OCR 流水线暂不实现（AstrBot 环境下需适配不同图片接口）
- 仅实现文本输入模式
"""
import jieba
import os
from itertools import combinations
from typing import List, Dict
from .game_data import ArknightsGameData
from .operator_model import Operator

curr_dir = os.path.dirname(os.path.abspath(__file__))


def all_match(source: list, target: list) -> bool:
    """检查 target 所有元素是否都在 source 中 — 对齐 AmiyaBot core.util.all_match"""
    for item in target:
        if item not in source:
            return False
    return True


class Recruit:
    """公开招募计算器 — 严格对齐 AmiyaBot Recruit"""

    tags_list: List[str] = []

    @staticmethod
    def init_tags_list():
        """构建标签 jieba 词库 — 对齐 AmiyaBot Recruit.init_tags_list()"""
        jieba.setLogLevel(20)  # 静默 jieba 日志

        tags = ["资深", "高资", "高级资深"]
        data = ArknightsGameData()
        for name, item in data.operators.items():
            for tag in item.tags:
                if tag not in tags:
                    tags.append(tag)

        dict_file = os.path.join(curr_dir, "..", "data", "plugins", "tags.txt")
        dict_path = os.path.normpath(dict_file)
        os.makedirs(os.path.dirname(dict_path), exist_ok=True)

        with open(dict_path, mode="w+", encoding="utf-8") as f:
            f.write("\n".join([f"{t} 500 n" for t in tags]))

        jieba.load_userdict(dict_path)
        Recruit.tags_list = tags

    @classmethod
    def action(cls, text: str) -> Dict | None:
        """执行公招计算 — 对齐 AmiyaBot Recruit.action()

        Returns:
            dict: {"groups": [...], "tags": [...]} 供 HTML 模板渲染
            None: 无法匹配
        """
        words = jieba.lcut(text.replace("公招", "").replace("公开招募", ""))

        tags = []
        max_rarity = 5
        for item in words:
            word = item.strip()
            if word in cls.tags_list:
                if word in ["资深", "资深干员"] and "资深干员" not in tags:
                    tags.append("资深干员")
                    continue
                if word in ["高资", "高级资深", "高级资深干员"] and "高级资深干员" not in tags:
                    tags.append("高级资深干员")
                    max_rarity = 6
                    continue
                if word not in tags:
                    tags.append(word)

        if not tags:
            return None

        result = find_operator_tags_by_tags(tags, max_rarity)
        if not result:
            return None

        # 去重合并: 同一个干员可能被多个标签匹配
        operators = {}
        for item in result:
            name = item["operator_name"]
            if name not in operators:
                operators[name] = item
            else:
                operators[name]["operator_tags"] += item["operator_tags"]

        # 生成标签组合并计算每组可出的干员
        groups = []
        combs = [tags] if len(tags) == 1 else find_combinations(tags)

        for comb in combs:
            lst = []
            max_r = 0
            for name, item in operators.items():
                rarity = item["operator_rarity"]
                if all_match(item["operator_tags"], comb):
                    if rarity == 6 and "高级资深干员" not in comb:
                        continue
                    if rarity >= 4 or rarity == 1:
                        if rarity > max_r:
                            max_r = rarity
                        lst.append(item)
                    else:
                        break
            else:
                if lst:
                    groups.append({"tags": comb, "max_rarity": max_r, "operators": lst})

        if not groups:
            return None

        # 按标签数量降序，同标签数按 max_rarity 降序
        groups = sorted(groups, key=lambda n: (-len(n["tags"]), -n["max_rarity"]))

        return {"groups": groups, "tags": tags}


def find_operator_tags_by_tags(tags: List[str], max_rarity: int) -> List[Dict]:
    """筛选匹配标签的干员 — 严格对齐 AmiyaBot find_operator_tags_by_tags()

    Args:
        tags: 用户输入的标签列表
        max_rarity: 最高稀有度（有高资时为 6，否则 5）

    Returns:
        [{"operator_id", "operator_name", "operator_rarity", "operator_tags": tag}, ...]
    """
    data = ArknightsGameData()
    res = []
    for name, item in data.operators.items():
        if not item.is_recruit or item.rarity > max_rarity:
            continue
        for tag in item.tags:
            if tag in tags:
                res.append({
                    "operator_id": item.id,
                    "operator_name": name,
                    "operator_rarity": item.rarity,
                    "operator_tags": tag,
                })
    return sorted(res, key=lambda n: -n["operator_rarity"])


def find_combinations(tags: List[str]) -> List[List[str]]:
    """生成标签组合（1-3个标签）— 严格对齐 AmiyaBot find_combinations()

    返回按标签数量降序排列的组合列表。
    过滤掉同时包含"高级资深干员"和"资深干员"的组合（矛盾）。
    """
    result = []
    for i in range(3):
        for combo in combinations(tags, i + 1):
            combo = list(combo)
            if combo and not ("高级资深干员" in combo and "资深干员" in combo):
                result.append(combo)
    result.reverse()
    return result
