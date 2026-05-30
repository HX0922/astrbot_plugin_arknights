"""
干员关键词系统 — 严格对齐 AmiyaBot operatorInfo.py

构建查询所需的关键词库:
- operator_list: 所有干员中文名
- operator_en_name_map: 英文名 → 中文名
- operator_group_map: 阵营名 → [Operator, ...]
- skins_map: 皮肤名 → skin数据
- voice_keywords: 语音标题列表
- stories_keywords: 档案标题列表
"""

import re
import os
import jieba
from typing import Dict, List
from .game_data import ArknightsGameData
from .operator_model import Operator


curr_dir = os.path.dirname(os.path.abspath(__file__))


class OperatorInfo:
    """干员信息初始化器 — 对齐 AmiyaBot OperatorInfo"""
    skins_map: Dict[str, dict] = {}
    stories_keywords: List[str] = []

    operator_list: List[str] = []
    operator_one_char_list: List[str] = []
    operator_contain_digit_list: List[str] = []
    operator_en_name_map: Dict[str, str] = {}
    operator_group_map: Dict[str, List[Operator]] = {}

    voice_keywords: List[str] = [
        "任命助理", "任命队长", "编入队伍", "问候", "闲置",
        "交谈1", "交谈2", "交谈3",
        "晋升后交谈1", "晋升后交谈2",
        "信赖提升后交谈1", "信赖提升后交谈2", "信赖提升后交谈3",
        "精英化晋升1", "精英化晋升2",
        "行动出发", "行动失败", "行动开始",
        "3星结束行动", "4星结束行动", "非3星结束行动",
        "选中干员1", "选中干员2",
        "部署1", "部署2",
        "作战中1", "作战中2", "作战中3", "作战中4",
        "戳一下", "信赖触摸",
        "干员报到", "进驻设施", "观看作战记录", "标题",
    ]

    _initialized: bool = False

    @classmethod
    def reset(cls):
        cls.operator_list = []
        cls.operator_one_char_list = []
        cls.operator_contain_digit_list = []
        cls.operator_en_name_map = {}
        cls.operator_group_map = {}

    @classmethod
    def set_jieba_dict(cls):
        dict_file = os.path.join(curr_dir, "..", "data", "operators.txt")
        dict_path = os.path.normpath(dict_file)

        os.makedirs(os.path.dirname(dict_path), exist_ok=True)

        with open(dict_path, mode="w", encoding="utf-8") as f:
            words = []
            for name in cls.operator_list:
                words.append(f"{name} 1 n")
                if len(name) == 1:
                    jieba.del_word(f"兔兔{name}")
            f.write("\n".join(words))

        jieba.load_userdict(dict_path)

    @classmethod
    def init_operator(cls):
        """初始化干员关键词库 — 对齐 AmiyaBot OperatorInfo.init_operator()"""
        from .game_data import ArknightsGameData

        cls.reset()

        data = ArknightsGameData()
        operators = data.operators

        from .operator_core import chinese_to_digits, is_contain_digit

        for name, op in operators.items():
            cls.operator_list.append(name)
            cls.operator_en_name_map[op.en_name] = name

            for n in [name, op.en_name]:
                n = chinese_to_digits(n)
                if n and is_contain_digit(n):
                    cls.operator_contain_digit_list.append(n)

            for group_val, group_key in [
                (op.team, "team"),
                (op.group, "group"),
                (op.nation, "nation"),
            ]:
                if group_val and group_val != "未知" and group_val != "":
                    if group_val not in cls.operator_group_map:
                        cls.operator_group_map[group_val] = []
                    cls.operator_group_map[group_val].append(op)

            if len(name) == 1:
                cls.operator_one_char_list.append(name)

        cls.set_jieba_dict()

    @classmethod
    def init_stories_keywords(cls):
        """初始化档案关键词"""
        from .operator_core import chinese_to_digits

        stories_title = {}

        for name, op in ArknightsGameData().operators.items():
            stories = op.stories()
            for s in stories:
                title = s.get("story_title", "")
                stories_title[chinese_to_digits(title)] = title

        cls.stories_keywords = list(stories_title.keys()) + [
            v for k, v in stories_title.items()
        ]

    @classmethod
    def init_skins_keywords(cls):
        """初始化皮肤关键词"""
        skins_map = {}

        for name, op in ArknightsGameData().operators.items():
            for skin in op.skins():
                skin_name = skin.get("skin_name", "")
                if skin_name in ["初始", "默认"]:
                    continue
                skins_map[skin_name] = skin

        cls.skins_map = skins_map

    @classmethod
    def ensure_initialized(cls):
        """确保已初始化（幂等）"""
        if cls._initialized:
            return
        cls._initialized = True
        cls.init_operator()
        cls.init_skins_keywords()
        cls.init_stories_keywords()
