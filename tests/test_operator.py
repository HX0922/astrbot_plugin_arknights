"""operator.py unit tests"""

import pytest
from src.game_data import ArkData
from src.operator import (
    format_operator_brief,
    format_operator_skills,
    format_operator_modules,
    format_operator_skins,
)


@pytest.fixture
def amiya():
    data = ArkData()
    return data.chars.get("char_002_amiya", {})


def test_format_brief_has_name(amiya):
    if not amiya:
        pytest.skip("Amiya not found in data")
    result = format_operator_brief(amiya)
    assert "阿米娅" in result
    assert "★" in result


def test_format_brief_has_profession(amiya):
    if not amiya:
        pytest.skip("Amiya not found in data")
    result = format_operator_brief(amiya)
    assert "职业" in result


def test_format_skills(amiya):
    if not amiya:
        pytest.skip("Amiya not found in data")
    skills = format_operator_skills(amiya, "char_002_amiya")
    assert isinstance(skills, list)


def test_format_modules(amiya):
    if not amiya:
        pytest.skip("Amiya not found in data")
    modules = format_operator_modules(amiya)
    assert isinstance(modules, list)


def test_format_skins():
    skins = format_operator_skins("char_002_amiya")
    assert isinstance(skins, list)
