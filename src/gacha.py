"""
卡池模拟模块 — 对齐 AmiyaBot 抽卡逻辑

使用 Operator 对象。
rarity 显示为 1-6 星。
"""

import random
from typing import List
from .game_data import ArknightsGameData


class GachaPool:
    """标准寻访卡池"""

    SIX_STAR_BASE = 0.02
    FIVE_STAR_BASE = 0.08
    FOUR_STAR_PROB = 0.50
    SOFT_PITY_START = 50
    HARD_PITY = 99
    SOFT_PITY_INCREMENT = 0.02

    def __init__(self, pool_type: str = "standard"):
        self.data = ArknightsGameData()
        self.pool_type = pool_type
        self.pity_counter = 0
        self._rarity_pools: dict[int, List[str]] = {}
        self._load_pool()

    def _load_pool(self):
        """从 operators 按稀有度分组 (rarity: 1-6)"""
        self._rarity_pools = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        for name, op in self.data.operators.items():
            if op.rarity in self._rarity_pools:
                self._rarity_pools[op.rarity].append(op.id)

    def single_pull(self) -> dict:
        """单抽"""
        self.pity_counter += 1
        effective_rate = self.SIX_STAR_BASE
        if self.pity_counter >= self.SOFT_PITY_START:
            effective_rate += (
                (self.pity_counter - self.SOFT_PITY_START + 1)
                * self.SOFT_PITY_INCREMENT
            )

        roll = random.random()

        if roll < effective_rate or self.pity_counter >= self.HARD_PITY:
            rarity = 6  # 6★
            self.pity_counter = 0
        elif roll < effective_rate + self.FIVE_STAR_BASE:
            rarity = 5  # 5★
        elif roll < effective_rate + self.FIVE_STAR_BASE + self.FOUR_STAR_PROB:
            rarity = 4  # 4★
        elif roll < effective_rate + self.FIVE_STAR_BASE + self.FOUR_STAR_PROB + 0.40:
            rarity = 3  # 3★
        else:
            rarity = 2  # 2★ (fallback)

        return self._pick_operator(rarity)

    def ten_pull(self) -> list[dict]:
        """十连，保底至少 1 个 5★+"""
        results = []
        has_high_rarity = False
        for _ in range(10):
            result = self.single_pull()
            results.append(result)
            if result["rarity"] >= 5:
                has_high_rarity = True

        if not has_high_rarity:
            results[-1] = self._pick_operator(5)

        return results

    def _pick_operator(self, rarity: int) -> dict:
        """从稀有度池随机选干员"""
        pool = self._rarity_pools.get(rarity, [])
        if not pool:
            for r in [rarity - 1, rarity + 1, rarity - 2]:
                if r in self._rarity_pools and self._rarity_pools[r]:
                    pool = self._rarity_pools[r]
                    break

        if not pool:
            return {
                "name": "未知干员",
                "rarity": rarity,
                "char_id": "",
                "profession": "",
            }

        char_id = random.choice(pool)
        op = self.data.operators.get(
            next((n for n, o in self.data.operators.items() if o.id == char_id), ""),
            None,
        )

        if op is None:
            return {"name": char_id, "rarity": rarity, "char_id": char_id, "profession": ""}

        return {
            "name": op.name,
            "rarity": rarity,
            "char_id": char_id,
            "profession": op.classes,
        }
