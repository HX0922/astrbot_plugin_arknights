"""fuzzy.py unit tests"""

import pytest
from src.fuzzy import FuzzyMatcher, fuzzy_search, best_fuzzy


@pytest.fixture
def matcher():
    return FuzzyMatcher()


@pytest.fixture
def operator_names():
    return ["阿米娅", "能天使", "德克萨斯", "推进之王", "银灰", "艾雅法拉", "伊芙利特",
            "闪灵", "夜莺", "塞雷娅", "星熊", "安洁莉娜"]


def test_exact_match(matcher, operator_names):
    results = matcher.match("阿米娅", operator_names)
    assert results[0] == ("阿米娅", 1.0)


def test_substring_match(matcher, operator_names):
    results = matcher.match("能天", operator_names)
    assert len(results) > 0
    assert results[0][0] == "能天使"


def test_empty_query(matcher):
    results = matcher.match("", ["a", "b"])
    assert results == []


def test_empty_candidates(matcher):
    results = matcher.match("test", [])
    assert results == []


def test_score_range(matcher, operator_names):
    results = matcher.match("天使", operator_names)
    for name, score in results:
        assert 0 <= score <= 1.0


def test_no_match(matcher):
    results = matcher.match("xyzabc123", ["阿米娅", "能天使"])
    assert results == []


def test_best_match(matcher, operator_names):
    result = matcher.best_match("能天", operator_names)
    assert result is not None
    assert result[0] == "能天使"


def test_fuzzy_search():
    items = {"char_002": "阿米娅", "char_103": "能天使", "char_102": "德克萨斯"}
    results = fuzzy_search("能天", items)
    assert len(results) > 0
    assert results[0][1] == "能天使"


def test_best_fuzzy():
    items = {"char_002": "阿米娅", "char_103": "能天使"}
    result = best_fuzzy("能天", items)
    assert result is not None
    assert result[1] == "能天使"
