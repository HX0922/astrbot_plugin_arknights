"""
干员查询核心 — 严格对齐 AmiyaBot operatorCore.py

包含:
- search_info() — 查询匹配
- FuncsVerify — 消息验证
- OperatorSearchInfo — 查询结果数据类
- get_index() / get_longest() — 数字和子串提取
- find_most_similar() — 模糊匹配
- 工具函数（chinese_to_digits 等）
"""

import re
import difflib
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from .game_data import ArknightsGameData
from .operator_model import Operator, remove_punctuation
from .operator_info import OperatorInfo


# ── 工具函数（对齐 core/util/common.py）─────────────────

def any_match(text: str, items: list) -> Optional[str]:
    for item in items:
        if item in text:
            return item
    return None


def chinese_to_digits(text: str) -> str:
    """中文数字转阿拉伯数字"""
    if not text:
        return text

    character_relation = {
        "零": 0, "一": 1, "二": 2, "两": 2,
        "三": 3, "四": 4, "五": 5, "六": 6,
        "七": 7, "八": 8, "九": 9, "十": 10,
        "百": 100, "千": 1000, "万": 10000, "亿": 100000000,
    }
    start_symbol = ["一", "二", "两", "三", "四", "五", "六", "七", "八", "九", "十"]
    more_symbol = list(character_relation.keys())

    symbol_str = ""
    found = False

    def _digits(chinese: str) -> int:
        total = 0
        r = 1
        for i in range(len(chinese) - 1, -1, -1):
            val = character_relation[chinese[i]]
            if val >= 10 and i == 0:
                r = max(val, r) if val > r else r * val
                total += val if val > r else r
            elif val >= 10:
                r = max(val, r) if val > r else r * val
            else:
                total += r * val
        return total

    result = list(text)
    i = 0
    while i < len(result):
        if result[i] in start_symbol:
            start = i
            while i < len(result) and result[i] in more_symbol:
                i += 1
            digits_str = "".join(result[start:i])
            try:
                result[start:i] = [str(_digits(digits_str))]
            except (KeyError, ValueError):
                pass
        i += 1

    return "".join(result)


def is_contain_digit(text: str) -> bool:
    return any(n.isdigit() for n in text)


def find_most_similar(text: str, text_list: list) -> Optional[str]:
    """对齐 AmiyaBot find_most_similar — 使用 SequenceMatcher + 公共字符数"""
    res = find_similar_list(text, text_list)
    if res:
        return res[0]
    return None


def find_similar_list(text: str, text_list: list) -> list:
    """对齐 AmiyaBot find_similar_list"""
    result = {}
    for item in text_list:
        rate = float(
            difflib.SequenceMatcher(None, text, item).quick_ratio()
            * len([n for n in text if n in set(item)])
        )
        if rate > 0:
            result.setdefault(rate, []).append(item)

    if result:
        return result[sorted(result.keys())[-1]]
    return []


def get_index_from_text(text: str, array: list) -> Optional[int]:
    """从文本中提取数字序号 — 对齐 AmiyaBot get_index_from_text"""
    r = re.search(r"(\d+)", text)
    if r:
        index = abs(int(r.group(1))) - 1
        if index >= len(array):
            index = len(array) - 1
        return index
    return None


def get_longest(text: str, items: list) -> str:
    """子串最长匹配 — 对齐 AmiyaBot get_longest()"""
    res = ""
    for item in items:
        if item in text and len(item) >= len(res):
            res = item
    return res


def get_index(text: str, array: list) -> Optional[int]:
    """从文本提取数字序号（过滤干扰词）"""
    import re
    for item in OperatorInfo.operator_contain_digit_list:
        # 移除包含数字的干员名中的数字干扰
        # 使用简单方法：针对每个干扰词去数字后做替换
        pass
    text_lower = text.lower()
    for item in OperatorInfo.operator_contain_digit_list:
        item_lower = item.lower()
        text_lower = text_lower.replace(item_lower, "")
    return get_index_from_text(text_lower, array)


# ── 查询结果 ──────────────────────────────────────────

@dataclass
class OperatorSearchInfo:
    char: Optional[Operator] = None
    name: str = ""
    skin_key: str = ""
    group_key: str = ""
    voice_key: str = ""
    story_key: str = ""


# ── 消息验证 ──────────────────────────────────────────

class FuncsVerify:
    """消息触发验证 — 对齐 AmiyaBot FuncsVerify"""

    @classmethod
    async def level_up(cls, data_text: str) -> tuple:
        info = search_info(data_text, source_keys=["name"])
        condition = any_match(data_text, ["精英", "专精", "材料"])
        return bool(condition), info

    @classmethod
    async def operator(cls, data_text: str, block_mishap: bool = True) -> tuple:
        info = search_info(data_text, source_keys=["name"])
        condition = any_match(data_text, ["技能", "召唤物"])

        flag = True
        if block_mishap:
            # blockMishap 模式：文本不能等于纯干员名触发，需要带关键词
            # AmiyaBot 原版检查: info.name != data.text and '查询' not in data.text
            if info.name and info.name != data_text and "查询" not in data_text:
                flag = bool(condition)

        if flag:
            return bool(info.name), info
        else:
            return False, info

    @classmethod
    async def group(cls, data_text: str) -> tuple:
        info = search_info(data_text, source_keys=["group_key"])
        if info.group_key and info.group_key != data_text and "查询" not in data_text:
            return False, info
        return bool(info.group_key), info


# ── 查询匹配 ──────────────────────────────────────────

def search_info(
    data_text: str,
    data_text_words: Optional[List[str]] = None,
    source_keys: Optional[list] = None,
    similar_mode: bool = True,
    length_limit: int = 50,
) -> OperatorSearchInfo:
    """核心查询匹配 — 严格对齐 AmiyaBot operatorCore.search_info()

    Args:
        data_text: 原始消息文本
        data_text_words: jieba 分词结果
        source_keys: 查询目标 key 列表 ['name', 'skin_key', ...]
        similar_mode: True → find_most_similar, False → get_longest
        length_limit: 文本长度限制
    """
    info_source = {
        "name": OperatorInfo.operator_list + list(OperatorInfo.operator_en_name_map.keys()),
        "skin_key": list(OperatorInfo.skins_map.keys()),
        "group_key": list(OperatorInfo.operator_group_map.keys()),
        "voice_key": OperatorInfo.voice_keywords,
        "story_key": OperatorInfo.stories_keywords,
    }

    info = OperatorSearchInfo()
    source_keys = source_keys or []

    import jieba

    if len(data_text) > int(length_limit):
        return info

    match_method = find_most_similar if similar_mode else get_longest

    for key_name in source_keys:
        candidates = info_source.get(key_name, [])
        if not candidates:
            continue

        res = match_method(data_text, candidates)
        if res and remove_punctuation(res) in remove_punctuation(data_text):
            setattr(info, key_name, res)

            if key_name == "name":
                # 英文名 → 中文名
                if info.name in OperatorInfo.operator_en_name_map:
                    info.name = OperatorInfo.operator_en_name_map[info.name]

                # 检查 name 是否在 jieba 分词中
                if data_text_words is None:
                    data_text_words = jieba.lcut(data_text.lower().replace(" ", ""))
                if info.name not in data_text_words:
                    # AmiyaBot: 不在分词中则继续匹配
                    continue

    # 填充 char
    if info.name:
        data = ArknightsGameData()
        info.char = data.operators.get(info.name)

    return info
