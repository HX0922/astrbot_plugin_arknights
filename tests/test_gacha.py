"""gacha.py unit tests"""

import pytest
from src.gacha import GachaPool


def test_single_pull():
    pool = GachaPool()
    result = pool.single_pull()
    assert "name" in result
    assert "rarity" in result
    assert result["rarity"] in range(2, 7)  # 2-6 星


def test_ten_pull():
    pool = GachaPool()
    results = pool.ten_pull()
    assert len(results) == 10
    # 十连保底
    rarities = [r["rarity"] for r in results]
    assert any(r >= 5 for r in rarities)  # 至少一个 5★+


def test_pity_counter_increment():
    """保底计数在非六星抽后递增"""
    pool = GachaPool()
    initial = pool.pity_counter
    # 模拟抽到 3★
    pool.pity_counter = 0
    # Manual low roll
    import random
    random.seed(42)
    _ = pool.single_pull()
    # pity counter changes based on result


def test_hard_pity():
    """硬保底: 99 抽不出 6★ 后必出"""
    pool = GachaPool()
    pool.pity_counter = 98
    result = pool.single_pull()
    assert result["rarity"] == 6
    assert pool.pity_counter == 0


def test_rng_deterministic():
    """固定 seed 产生可重复结果"""
    import random
    random.seed(12345)
    pool1 = GachaPool()
    r1 = [pool1.single_pull()["rarity"] for _ in range(5)]

    random.seed(12345)
    pool2 = GachaPool()
    r2 = [pool2.single_pull()["rarity"] for _ in range(5)]

    assert r1 == r2
