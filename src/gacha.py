"""
卡池模拟模块

模拟明日方舟标准寻访卡池的抽卡逻辑。

核心机制:
  - 6★: 2% (基础)
  - 5★: 8%
  - 4★: 50%
  - 3★: 40%
  - 软保底: 50 抽后每抽 6★ 概率 +2%
  - 硬保底: 99 抽必出 6★
  - 十连保底: 至少 1 个 5★+
"""

import random
from dataclasses import dataclass
from .game_data import ArkData


@dataclass
class GachaResult:
    chars: list[dict]
    total_6star: int = 0
    total_5star: int = 0
    total_4star: int = 0
    pity_counter: int = 0


class GachaPool:
    """标准寻访卡池"""

    SIX_STAR_BASE = 0.02
    FIVE_STAR_BASE = 0.08
    FOUR_STAR_BASE = 0.50
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
        """从 gacha_table.json 加载卡池干员分布"""
        gacha = self.data.gacha_table
        recruit_detail = gacha.get("recruitDetail", {})
        avail = recruit_detail.get("availChars", {})

        self._rarity_pools = {
            2: [],  # 3★
            3: [],  # 4★
            4: [],  # 5★
            5: [],  # 6★
        }

        for rarity_str, char_list in avail.items():
            try:
                rarity = int(rarity_str)
            except ValueError:
                continue
            if rarity in self._rarity_pools:
                self._rarity_pools[rarity] = list(char_list)

        # 如果数据为空，用全干员池填充
        if not any(self._rarity_pools.values()):
            for cid, char in self.data.chars.items():
                r = char.get("rarity", 0)
                if r in self._rarity_pools:
                    self._rarity_pools[r].append(cid)

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
        elif roll < effective_rate + self.FIVE_STAR_BASE + self.FOUR_STAR_BASE:
            rarity = 3  # 4★
        else:
            rarity = 2  # 3★
            self.pity_counter += 1

        return self._pick_operator(rarity)

    def ten_pull(self) -> list[dict]:
        """十连（保底至少 1 个 5★+）"""
        results = []
        has_guarantee = False
        for _ in range(10):
            result = self.single_pull()
            results.append(result)
            if result["rarity"] >= 5:
                has_guarantee = True

        if not has_guarantee:
            results[-1] = self._pick_operator(4)  # 替换最后一个为 5★

        return results

    def _pick_operator(self, rarity: int) -> dict:
        """从稀有度池随机选干员"""
        pool = self._rarity_pools.get(rarity, [])
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
