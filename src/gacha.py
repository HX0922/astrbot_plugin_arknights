"""
卡池模拟模块

模拟明日方舟标准寻访卡池抽卡逻辑。

核心机制:
  - 6★: 2% (基础), 5★: 8%, 4★: 50%, 3★: 40%
  - 软保底: 50 抽后每抽 6★ 概率 +2%
  - 硬保底: 99 抽必出 6★
  - 十连保底: 至少 1 个 5★+

数据源: character_table.json (所有干员按稀有度分组)
"""

import random
from .game_data import ArkData


class GachaPool:
    """标准寻访卡池"""

    SIX_STAR_BASE = 0.02
    FIVE_STAR_BASE = 0.08
    FOUR_STAR_PROB = 0.50
    SOFT_PITY_START = 50
    HARD_PITY = 99
    SOFT_PITY_INCREMENT = 0.02

    def __init__(self, pool_type: str = "standard"):
        self.data = ArkData()
        self.pool_type = pool_type
        self.pity_counter = 0
        self._rarity_pools = {}
        self._load_pool()

    def _load_pool(self):
        """从 character_table 按稀有度分组"""
        self._rarity_pools = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}

        for char_id, char in self.data.chars.items():
            rarity = char.get("rarity", -1)
            if rarity in self._rarity_pools:
                self._rarity_pools[rarity].append(char_id)

    def single_pull(self) -> dict:
        """单抽"""
        effective_rate = self.SIX_STAR_BASE
        if self.pity_counter >= self.SOFT_PITY_START:
            effective_rate += (
                (self.pity_counter - self.SOFT_PITY_START + 1)
                * self.SOFT_PITY_INCREMENT
            )

        roll = random.random()

        if roll < effective_rate or self.pity_counter >= self.HARD_PITY:
            rarity = 5  # 6★
            self.pity_counter = 0
        elif roll < effective_rate + self.FIVE_STAR_BASE:
            rarity = 4  # 5★
        elif roll < effective_rate + self.FIVE_STAR_BASE + self.FOUR_STAR_PROB:
            rarity = 3  # 4★
        elif roll < effective_rate + self.FIVE_STAR_BASE + self.FOUR_STAR_PROB + 0.40:
            rarity = 2  # 3★
        else:
            rarity = 1  # 2★
            self.pity_counter += 1

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
            results[-1] = self._pick_operator(4)

        return results

    def _pick_operator(self, rarity: int) -> dict:
        """从稀有度池随机选干员"""
        pool = self._rarity_pools.get(rarity, [])
        if not pool:
            # fallback: try adjacent rarity
            for r in [rarity - 1, rarity + 1, rarity - 2]:
                if r in self._rarity_pools and self._rarity_pools[r]:
                    pool = self._rarity_pools[r]
                    break

        if not pool:
            return {"name": "未知干员", "rarity": rarity + 1, "char_id": "",
                    "profession": ""}

        char_id = random.choice(pool)
        char = self.data.chars.get(char_id, {})
        return {
            "name": char.get("name", "未知"),
            "rarity": rarity + 1,  # 0-index → 1-6 星显示
            "char_id": char_id,
            "profession": char.get("profession", ""),
        }
