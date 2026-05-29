"""
jieba 模糊匹配层

为所有查询模块提供统一的模糊搜索接口。
替代 AmiyaBot 的 find_most_similar() + jieba 分词方案。

用法:
    from src.fuzzy import FuzzyMatcher

    matcher = FuzzyMatcher()
    results = matcher.match("阿能", all_operator_names)
    # -> [("能天使", 0.85), ("能天使(泳装)", 0.72), ...]
"""

import jieba
from difflib import SequenceMatcher
from collections import OrderedDict


class FuzzyMatcher:
    """模糊匹配器

    策略:
    1. 精确匹配 → 直接返回
    2. jieba 分词后的子串匹配 (用户输入是目标名的子串)
    3. SequenceMatcher 相似度排序
    """

    def __init__(self, min_score: float = 0.5, max_results: int = 12):
        self.min_score = min_score
        self.max_results = max_results

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """jieba 分词"""
        return [w for w in jieba.cut(text) if w.strip()]

    def match(self, query: str, candidates: list[str]) -> list[tuple[str, float]]:
        """在候选列表中搜索 query

        Args:
            query: 用户输入
            candidates: 候选名称列表

        Returns:
            [(name, score), ...] 按相似度降序
        """
        if not query or not candidates:
            return []

        query_lower = query.lower().strip()

        # 1. 精确匹配
        exact_matches = [(c, 1.0) for c in candidates if c.lower() == query_lower]
        if exact_matches:
            return exact_matches

        # 2. jieba 子串: 用户输入的所有分词都在候选名中
        query_tokens = set(self.tokenize(query))
        substring_matches = []
        for cand in candidates:
            cand_lower = cand.lower()
            cand_tokens = set(self.tokenize(cand))
            # 查询词是候选词的子串
            if query_lower in cand_lower:
                substring_matches.append((cand, 0.85))

        # 3. 分词包含: 查询的所有词都被候选包含
        if not substring_matches:
            for cand in candidates:
                cand_lower = cand.lower()
                cand_tokens = set(self.tokenize(cand))
                if query_tokens and query_tokens.issubset(cand_tokens):
                    substring_matches.append((cand, 0.75))

        # 4. SequenceMatcher 降级
        scored = []
        seen = {m[0] for m in substring_matches}
        for cand in candidates:
            if cand in seen:
                continue
            score = SequenceMatcher(None, query_lower, cand.lower()).ratio()
            if score >= self.min_score:
                scored.append((cand, score))

        # 合并并排序
        all_results = substring_matches + scored
        all_results.sort(key=lambda x: -x[1])

        # 去重
        unique = OrderedDict()
        for name, score in all_results:
            if name not in unique:
                unique[name] = score

        return list(unique.items())[:self.max_results]

    def best_match(self, query: str, candidates: list[str]) -> tuple[str, float] | None:
        """返回最佳匹配"""
        results = self.match(query, candidates)
        return results[0] if results else None


# ── 模块级方便函数 ────────────────────────────────────

_default_matcher = FuzzyMatcher()


def fuzzy_search(query: str, items: dict[str, str]) -> list[tuple[str, str, float]]:
    """在 {id: name} 字典中搜索

    Returns: [(id, name, score), ...]
    """
    names = list(items.values())
    id_by_name = {v: k for k, v in items.items()}
    matches = _default_matcher.match(query, names)
    return [
        (id_by_name.get(name, ""), name, score)
        for name, score in matches
    ]


def best_fuzzy(query: str, items: dict[str, str]) -> tuple[str, str, float] | None:
    """返回最佳模糊匹配"""
    results = fuzzy_search(query, items)
    return results[0] if results else None
