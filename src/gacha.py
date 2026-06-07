"""
卡池模拟模块 — 严格对齐 AmiyaBot gachaBuilder.py 概率算法

核心对齐点:
- 概率分布: rarity_range = {6:2, 5:8, 4:50, 3:40, 2:0, 1:0} (百分比)
- Soft pity: break_even > 50 时六星概率每抽 +2%
- 十连保底: 至少 1个五星+
- Pool 读取 gacha_table.json
- 权重归一化: pickup + special + fillin
"""
import os
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .game_data import ArknightsGameData, ArknightsGameResource
from .operator_model import Operator

# AmiyaBot 原版概率分布 (百分比)
RARITY_RANGE = {6: 2, 5: 8, 4: 50, 3: 40, 2: 0, 1: 0}

# 稀有度颜色 (对齐 AmiyaBot gachaBuilder.color)
COLOR = {6: "FF4343", 5: "FEA63A", 4: "A288B5", 3: "7F7F7F", 2: "7F7F7F", 1: "7F7F7F"}


def _load_gacha_table() -> dict:
    """读取 gacha_table.json — 对齐 AmiyaBot 从数据库 Pool 表读取"""
    root = ArknightsGameResource.get_data_root()
    path = root / "gamedata" / "excel" / "gacha_table.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class GachaPool:
    """标准寻访卡池 — 对齐 AmiyaBot GachaBuilder 概率算法

    AmiyaBot 原版流程 (gachaBuilder.start_gacha):
    1. break_even += 1
    2. get_rates() — 计算含 soft pity 的概率分布
    3. random.choices(rarity_keys, weights=rarity_weights) — 稀有度抽取
    4. 抽出六星 → break_even = 0
    5. choose_operator(rarity) — 在该稀有度池中按权重选干员
    """

    def __init__(self):
        self.data = ArknightsGameData()
        self._gacha_table = _load_gacha_table()
        self._pool = self._find_default_pool()
        self.break_even = 0

        # 构建各稀有度权重字典 (对齐 __get_gacha)
        self._rarity_pools: Dict[int, dict] = {}
        self._build_rarity_pools()

    # ════════════════════════════════════════════════════
    # 卡池配置
    # ════════════════════════════════════════════════════

    def _find_default_pool(self) -> dict:
        """找到默认标准寻访池 — 对齐 AmiyaBot get_official_pool()"""
        pools = self._gacha_table.get("gachaPoolClient", [])
        # 找最新的 NORMAL 类型池子
        for pool in sorted(pools, key=lambda p: p.get("openTime", 0), reverse=True):
            if pool.get("gachaType") == "NORMAL":
                return pool
        return {}

    @property
    def pool_name(self) -> str:
        return self._pool.get("gachaPoolName", "标准寻访")

    def _get_pickup_rate(self, rarity: int) -> float:
        """获取指定稀有度的 UP 率 — 对齐 AmiyaBot __get_pickup_rate()"""
        pool = self._pool
        detail = pool.get("gachaPoolDetail", {})
        if rarity == 6:
            return detail.get("sixPer", detail.get("sixStarPer", 0.5))
        elif rarity == 5:
            return detail.get("fivePer", detail.get("fiveStarPer", 0.5))
        elif rarity == 4:
            return detail.get("fourPer", detail.get("fourStarPer", 0.0))
        return 0.0

    def _get_pickup_operators(self, rarity: int) -> List[str]:
        """获取 UP 干员列表 — 对齐 AmiyaBot pool.pickup_{rarity}"""
        pool = self._pool
        detail = pool.get("gachaPoolDetail", {})
        key_map = {6: "gachaPicker6", 5: "gachaPicker5", 4: "gachaPicker4"}
        key = key_map.get(rarity)
        if not key:
            return []
        pickers = detail.get(key, [])
        return [p.get("charId", "") for p in pickers if p.get("charId")]

    # ════════════════════════════════════════════════════
    # 权重构建 (对齐 __get_gacha + __get_weight)
    # ════════════════════════════════════════════════════

    def _build_rarity_pools(self):
        """为每个稀有度构建最终权重字典"""
        for rarity in [1, 2, 3, 4, 5, 6]:
            self._rarity_pools[rarity] = self._build_single_rarity_pool(rarity)

    def _build_single_rarity_pool(self, rarity: int) -> dict:
        """构建单个稀有度的权重字典 — 对齐 AmiyaBot __get_gacha()"""
        scale = 10000  # 对齐 AmiyaBot 的放大系数
        up_rate = self._get_pickup_rate(rarity)
        up_rate = max(0.0, min(1.0, up_rate))

        # pickup 权重 (pool.pickup_X 字段)
        pickup_ops = self._get_pickup_operators(rarity)
        pickup_weight = {name: 1 for name in pickup_ops}

        # fillin: 所有该稀有度干员 (每人权重 1)
        fillin = []
        for name, op in self.data.operators.items():
            if op.rarity == rarity:
                fillin.append(name)

        # special 权重 (对齐 pool.pickup_s_X，这里简化: 空)
        special_weight = {}

        final_weight = {}
        weight_pickup_total = sum(max(0, w) for w in pickup_weight.values())

        # Step 1: 填充 UP 干员权重
        if weight_pickup_total > 0:
            for name, w in pickup_weight.items():
                if w > 0:
                    final_weight[name] = up_rate * scale * w / weight_pickup_total
        else:
            for name in pickup_weight:
                final_weight[name] = 0

        # Step 2: 填充 fillin + special (非UP干员)
        combined = {}
        for name in special_weight:
            combined[name] = special_weight[name]
        for name in fillin:
            combined[name] = combined.get(name, 0) + 1

        weight_fillin_total = 0
        for name, w in combined.items():
            if w > 0 and name not in final_weight:
                weight_fillin_total += w

        if weight_fillin_total > 0:
            for name, w in combined.items():
                if w > 0 and name not in final_weight:
                    final_weight[name] = (1 - up_rate) * scale * w / weight_fillin_total

        return final_weight

    def _choose_operator(self, rarity: int) -> Tuple[str, Optional[Operator]]:
        """在指定稀有度池中按权重选干员 — 对齐 AmiyaBot choose_operator()"""
        pool = self._rarity_pools.get(rarity, {})
        if not pool:
            # fallback: 同稀有度随机
            names = [n for n, op in self.data.operators.items() if op.rarity == rarity]
            if names:
                name = random.choice(names)
                return name, self.data.operators.get(name)
            return "未知干员", None

        names = list(pool.keys())
        weights = list(pool.values())
        name = random.choices(names, weights=weights, k=1)[0]
        return name, self.data.operators.get(name)

    # ════════════════════════════════════════════════════
    # 概率计算 (对齐 get_rates)
    # ════════════════════════════════════════════════════

    def get_rates(self) -> Dict[int, int]:
        """计算含 soft pity 的概率分布 — 对齐 AmiyaBot get_rates()"""
        rates = RARITY_RANGE.copy()
        break_even_rate = rates[6]

        if self.break_even > 50:
            break_even_rate += (self.break_even - 50) * 2

        shift_up = break_even_rate - rates[6]
        rates[6] = break_even_rate

        # 从低星开始扣除提升的概率
        for i in [1, 2, 3, 4, 5]:
            if shift_up >= rates[i]:
                shift_up -= rates[i]
                rates[i] = 0
            else:
                rates[i] -= shift_up
                break

        return rates

    def _roll_rarity(self) -> int:
        """抽取稀有度 — 对齐 AmiyaBot start_gacha() 核心循环"""
        self.break_even += 1
        rates = self.get_rates()
        keys = list(rates.keys())
        weights = list(rates.values())
        rarity = random.choices(keys, weights=weights, k=1)[0]

        if rarity == 6:
            self.break_even = 0

        return rarity

    # ════════════════════════════════════════════════════
    # 公开 API
    # ════════════════════════════════════════════════════

    def single_pull(self) -> dict:
        """单抽 — 对齐 AmiyaBot start_gacha(times=1)"""
        rarity = self._roll_rarity()
        name, op = self._choose_operator(rarity)

        return {
            "name": name,
            "rarity": rarity,
            "char_id": op.id if op else "",
            "profession": op.classes if op else "",
            "classes_sub": op.classes_sub if op else "",
        }

    def ten_pull(self) -> List[dict]:
        """十连 — 对齐 AmiyaBot start_gacha(times=10)
        保底: 至少 1 个 5★+
        """
        results = []
        has_high = False
        for _ in range(10):
            result = self.single_pull()
            results.append(result)
            if result["rarity"] >= 5:
                has_high = True

        if not has_high:
            # 十连保底: 最后一抽替换为五星
            results[-1] = self._force_rarity(5)

        return results

    def _force_rarity(self, rarity: int) -> dict:
        """强制指定稀有度（十连保底用）"""
        name, op = self._choose_operator(rarity)
        return {
            "name": name,
            "rarity": rarity,
            "char_id": op.id if op else "",
            "profession": op.classes if op else "",
            "classes_sub": op.classes_sub if op else "",
        }

    def check_break_even_text(self) -> str:
        """保底状态文本 — 对齐 AmiyaBot check_break_even()"""
        break_even_rate = 98
        if self.break_even > 50:
            break_even_rate -= (self.break_even - 50) * 2

        return (
            f"当前已经抽取了 {self.break_even} 次而未获得六星干员\n"
            f"下次抽出六星干员的概率为 {100 - break_even_rate}%\n"
        )
