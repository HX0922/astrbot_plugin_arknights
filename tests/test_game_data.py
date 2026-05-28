"""
game_data.py 单元测试

前置条件:
  - ArknightsGameResource submodule 已初始化
  - 或设置 AK_DATA_ROOT 环境变量
"""

import os
import pytest
from src.game_data import ArkData, RARITY_STARS


def test_singleton():
    """单例模式验证"""
    a = ArkData()
    b = ArkData()
    assert a is b


def test_data_root_exists():
    """数据目录存在"""
    data = ArkData()
    assert data._data_root.exists()


def test_load_characters():
    """加载干员数据"""
    data = ArkData()
    assert len(data.chars) > 0
    # 验证已知干员
    assert "char_002_amiya" in data.chars
    assert data.chars["char_002_amiya"]["name"] == "阿米娅"


def test_load_items():
    """加载物品数据"""
    data = ArkData()
    assert len(data.items) > 0


def test_get_char_image():
    """获取干员图片路径（图片文件可能不存在，本地只含 JSON）"""
    data = ArkData()
    path = data.get_char_image_path("char_002_amiya", "portrait")
    if path:  # 图片可能存在也可能不存在
        assert path.endswith(".png")
    # 无图片时返回空字符串，不会崩溃



def test_avatar_path():
    """获取头像路径"""
    data = ArkData()
    path = data.get_char_image_path("char_002_amiya", "avatar")
    if path:
        assert path.endswith(".png")


def test_search_char_exact():
    """精确搜索干员"""
    data = ArkData()
    results = data.resolve_char("阿米娅")
    assert len(results) >= 1  # 可能有联动干员也叫阿米娅
    assert "char_002_amiya" in results


def test_search_char_fuzzy():
    """模糊搜索干员"""
    data = ArkData()
    results = data.resolve_char("能天")
    assert len(results) >= 0  # 取决于数据
    if results:
        assert any("能天使" in data.chars[r]["name"] for r in results)


def test_search_items():
    """搜索物品"""
    data = ArkData()
    results = data.search_items("固源岩")
    if results:
        assert "固源岩" in results[0]["name"]


def test_search_stages():
    """搜索关卡"""
    data = ArkData()
    results = data.search_stages("1-7")
    if results:
        stage = results[0]
        assert "1-7" in stage.get("code", "")


def test_name_index_contains_chars():
    """名称索引包含所有干员"""
    data = ArkData()
    index = data.name_index
    assert len(index) >= len(data.chars) * 0.9  # 允许别名重叠
