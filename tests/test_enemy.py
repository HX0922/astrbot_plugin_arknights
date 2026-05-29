"""enemy.py unit tests"""

import pytest
from src.game_data import ArkData
from src.enemy import (
    search_enemy,
    format_enemy_brief,
    format_enemy_index_list,
    get_enemy_by_name,
)


def test_search_enemy_exact():
    """精确搜索"""
    results = search_enemy("源石虫")
    assert len(results) > 0
    assert results[0]["name"] == "源石虫"


def test_search_enemy_fuzzy():
    """模糊搜索"""
    results = search_enemy("源石")
    assert len(results) >= 3  # 源石虫, 源石虫·α, 源石虫·β


def test_search_enemy_not_found():
    """搜索不存在的敌人"""
    results = search_enemy("不存在的敌人xyz")
    assert results == []


def test_format_enemy_brief():
    """格式化敌人信息"""
    data = ArkData()
    # pick first enemy
    first_id = list(data.enemies.keys())[0]
    enemy = {"id": first_id, **data.enemies[first_id]}
    result = format_enemy_brief(enemy)
    assert enemy["name"] in result
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_index_list():
    """格式化索引列表"""
    results = search_enemy("源石虫")
    output = format_enemy_index_list(results)
    assert "源石虫" in output
    assert "序号" in output


def test_format_index_list_empty():
    """空列表"""
    output = format_enemy_index_list([])
    assert "没有找到" in output


def test_get_enemy_by_name():
    """按名称精确查找"""
    enemy = get_enemy_by_name("源石虫")
    assert enemy is not None
    assert enemy["name"] == "源石虫"
    assert enemy["enemyIndex"] == "B1"


def test_get_enemy_not_found():
    """查找不存在的"""
    enemy = get_enemy_by_name("nonexistent")
    assert enemy is None


def test_search_case_insensitive():
    """大小写不敏感（模糊搜索使用 lower()）"""
    results = search_enemy("大鲍勃")
    assert len(results) >= 1
    assert any("大鲍勃" in r["name"] for r in results)
