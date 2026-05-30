"""
公开招募标签计算模块 — 对齐 AmiyaBot recruit 计算逻辑

使用 Operator 对象代替原来的 raw dict。
"""

from dataclasses import dataclass, field
from itertools import combinations
from typing import List
from .game_data import ArknightsGameData
from .operator_model import Operator


@dataclass
class RecruitResult:
    char_id: str
    name: str
    rarity: int  # 0-5 (游戏内显示 1-6 星)
    tags: list[str]
    profession: str


# 用户输入 → 游戏内标签名映射
TAG_MAP = {
    "狙击": "狙击", "术师": "术师", "近卫": "近卫",
    "重装": "重装", "辅助": "辅助", "特种": "特种",
    "医疗": "医疗", "先锋": "先锋",
    "近战位": "近战位", "远程位": "远程位",
    "输出": "输出", "防护": "防护", "生存": "生存",
    "治疗": "治疗", "费用回复": "费用回复",
    "支援": "支援", "削弱": "削弱",
    "控场": "控场", "爆发": "爆发",
    "召唤": "召唤", "快速复活": "快速复活",
    "位移": "位移", "减速": "减速",
    "资深干员": "资深干员", "高级资深干员": "高级资深干员",
}

# 位置标签反向映射
POS_REVERSE = {"MELEE": "近战位", "RANGED": "远程位"}


class RecruitCalculator:
    """公开招募计算器 — 对齐 AmiyaBot 逻辑"""

    def __init__(self):
        self.data = ArknightsGameData()
        self._pool: List[RecruitResult] = None

    @property
    def pool(self) -> list[RecruitResult]:
        if self._pool is None:
            self._load_pool()
        return self._pool

    def _load_pool(self):
        """从 operators 提取所有可公招的干员"""
        self._pool = []
        for name, op in self.data.operators.items():
            rarity = op.rarity  # 1-6
            tags = self._op_tags(op)
            if not tags:
                continue

            self._pool.append(RecruitResult(
                char_id=op.id,
                name=op.name,
                rarity=rarity,
                tags=tags,
                profession=op.classes_code,
            ))

        self._pool.sort(key=lambda x: -x.rarity)

    def _op_tags(self, op: Operator) -> list[str]:
        """提取干员的公招标签"""
        tags = []

        # 职业标签（raw profession name）
        prof = op.classes_code  # "WARRIOR", "SNIPER", etc.
        if prof:
            tags.append(prof)

        # 位置标签
        pos = op.type  # "MELEE" / "RANGED"
        if pos:
            tags.append(pos)
            tags.append(POS_REVERSE.get(pos, pos))

        # tagList（已包含中文标签如 "输出"、"防护"）
        for t in op.tags:
            tags.append(t)

        # 稀有度隐含标签 (rarity: 1-6)
        if op.rarity >= 5:   # 5★+
            tags.append("资深干员")
        if op.rarity >= 6:   # 6★
            tags.append("高级资深干员")

        return tags

    def calculate(self, tags: list[str]) -> list[tuple[RecruitResult, list[str]]]:
        """根据标签组合计算匹配干员"""
        if not self.pool or not tags:
            return []

        search_tags = set()
        for tag in tags:
            tag = tag.strip()
            mapped = TAG_MAP.get(tag, tag)
            search_tags.add(mapped)

        results = []
        for char in self.pool:
            char_tags = set(char.tags)
            matched = search_tags & char_tags
            if matched:
                results.append((char, list(matched)))

        results.sort(key=lambda x: (-x[0].rarity, -len(x[1])))
        return results

    def get_all_tags(self) -> list[str]:
        return list(TAG_MAP.keys())

    def calculate_all_combinations(self, tags: list[str]) -> list[dict]:
        """生成所有标签子集组合，按招募效果排序"""
        if not self.pool or not tags:
            return []

        mapped = [TAG_MAP.get(t.strip(), t.strip()) for t in tags if t.strip()]
        if len(mapped) < 1:
            return []

        seen_results = {}
        all_combos = []

        for r in range(1, min(len(mapped) + 1, 6)):
            for combo in combinations(mapped, r):
                combo_key = frozenset(combo)
                if combo_key in seen_results:
                    continue

                results = self.calculate(list(combo))
                if not results:
                    continue

                seen_results[combo_key] = results

                top_rarity = results[0][0].rarity if results else 0
                precision = 1.0 / len(results) if results else 0
                score = top_rarity * 10 + precision * 5

                all_combos.append({
                    "tags": list(combo),
                    "results": results,
                    "score": score,
                    "highlight": top_rarity >= 5,  # 5★+ 高亮
                })

        all_combos.sort(key=lambda x: -x["score"])
        return all_combos[:20]
