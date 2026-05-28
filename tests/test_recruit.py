"""recruit.py unit tests"""

import pytest
from src.recruit import RecruitCalculator


@pytest.fixture
def calc():
    return RecruitCalculator()


def test_pool_loaded(calc):
    """公招池正确加载"""
    assert len(calc.pool) > 0
    # 所有条目都是 RecruitResult
    for char in calc.pool[:5]:
        assert char.name
        assert char.rarity >= 0
        assert char.char_id


def test_calculate_single_tag(calc):
    """单标签计算"""
    results = calc.calculate(["狙击"])
    if results:
        for char, tags in results[:3]:
            assert "狙击" in tags or "SNIPER" in tags


def test_calculate_multi_tags(calc):
    """多标签组合计算"""
    results = calc.calculate(["狙击", "输出"])
    if results:
        # 验证按稀有度降序
        rarities = [r[0].rarity for r in results]
        assert rarities == sorted(rarities, reverse=True)


def test_calculate_senior_operator(calc):
    """高级资深干员标签"""
    results = calc.calculate(["高级资深干员"])
    if results:
        # 应该只匹配高稀有度
        for char, _ in results:
            assert char.rarity >= 4  # 5★+


def test_empty_tags(calc):
    """空标签返回空"""
    results = calc.calculate([])
    assert results == []


def test_unknown_tag(calc):
    """未知标签不崩溃"""
    results = calc.calculate(["不存在的标签"])
    assert results == []
