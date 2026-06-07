"""
文本规范化模块 — 在消息路由前将昵称/别名替换为正式名

对齐 AmiyaBot amiyabot-replace-2_8 的替换策略:
- 如果正式名称已在原文中 → 不替换（避免歧义）
- 如果别名在原文中 → 替换为正式名称
- 最长匹配优先（避免短别名误匹配）

对齐 kkss-advanced-replace-2_2_1 的检查逻辑:
- 别名不能是已有正式名
- 别名不能与其他正式名冲突
"""

import re
from typing import Dict, List, Optional, Tuple
from .game_data import ArknightsGameData, remove_punctuation


# ── 别名配置表 ──────────────────────────────────────────

# 格式: {别名: 正式名, ...}
# 来源: 游戏社区约定俗成的昵称/外号/简写
OPERATOR_ALIASES: Dict[str, str] = {
    # 六星
    "阿能": "能天使",
    "小羊": "艾雅法拉",
    "羊": "艾雅法拉",
    "42": "史尔特尔",
    "42姐": "史尔特尔",
    "银老板": "银灰",
    "银灰老板": "银灰",
    "推王": "推进之王",
    "老爷子": "赫拉格",
    "赛爹": "塞雷娅",
    "赛妈": "塞雷娅",
    "龙羊": "伊芙利特",
    "小火龙": "伊芙利特",
    "小火龙儿": "伊芙利特",
    "杰哥": "安洁莉娜",
    "小杰": "安洁莉娜",
    "风笛": "风笛",
    "笛": "风笛",
    "夜莺": "夜莺",
    "铃兰": "铃兰",
    "铃兰妈": "铃兰",
    "泥岩": "泥岩",
    "山": "山",
    "温蒂": "温蒂",
    "傀影": "傀影",
    "傀": "傀影",
    "嵯峨": "嵯峨",
    "空弦": "空弦",
    "异客": "异客",
    "红蒂": "浊心斯卡蒂",
    "水月": "水月",
    "粉毛": "澄闪",
    "号角": "号角",
    "百嘉": "百炼嘉维尔",
    "叔叔": "玛恩纳",
    "玛恩纳叔叔": "玛恩纳",
    "翼德": "缄默德克萨斯",
    "异德": "缄默德克萨斯",
    "异苇": "焰影苇草",
    "大哥": "重岳",
    "重岳大哥": "重岳",
    "夜刀异格": "麒麟R夜刀",
    "伊内丝": "伊内丝",
    "缪缪": "缪尔赛思",
    "缪尔": "缪尔赛思",
    "提丰": "提丰",
    "纯艾": "纯烬艾雅法拉",
    "奶羊": "纯烬艾雅法拉",
    "锏": "锏",
    "左乐": "左乐",
    "黍": "黍",
    "黍姐": "黍",
    "艾拉": "艾拉",
    "小罗": "逻各斯",
    "logos": "逻各斯",
    "维神": "维什戴尔",
    "乌尔": "乌尔比安",
    "乌队": "乌尔比安",
    "佩佩": "佩佩",
    "佩": "佩佩",
    "马鹿": "玛露西尔",
    "拉狗": "拉普兰德",
    "拉普兰德异格": "荒芜拉普兰德",
    # 五星
    "白咕咕": "白面鸮",
    "赫默": "赫默",
    "华法琳": "华法琳",
    "ff0": "华法琳",
    "初雪": "初雪",
    "崖心": "崖心",
    "德狗": "德克萨斯",
    "德狗子": "德克萨斯",
    "德克萨斯": "德克萨斯",
    "拉普兰德": "拉普兰德",
    "幽灵鲨": "幽灵鲨",
    "蓝毒": "蓝毒",
    "白金": "白金",
    "陨星": "陨星",
    "守林人": "守林人",
    "普罗旺斯": "普罗旺斯",
    "火神": "火神",
    "可颂": "可颂",
    "雷蛇": "雷蛇",
    "临光": "临光",
    "红": "红",
    "狮蝎": "狮蝎",
    "食铁兽": "食铁兽",
    "槐琥": "槐琥",
    "梅尔": "梅尔",
    "稀音": "稀音",
    "极境": "极境",
    "鸡精": "极境",
    "蜜蜡": "蜜蜡",
    "贾维": "贾维",
    "鞭刃": "鞭刃",
    "羽毛笔": "羽毛笔",
    "龙舌兰": "龙舌兰",
    "夏栎": "夏栎",
    "但书": "但书",
    "晓歌": "晓歌",
    "洛洛": "洛洛",
    "车尔尼": "车尔尼",
    "至简": "至简",
    "明椒": "明椒",
    "和弦": "和弦",
    "截云": "截云",
    "凛视": "凛视",
    "寒檀": "寒檀",
    "青枳": "青枳",
    "苍苔": "苍苔",
    "冰酿": "冰酿",
    "杏仁": "杏仁",
    "渡桥": "渡桥",
    # 四星
    "砾": "砾",
    "末药": "末药",
    "苏苏洛": "苏苏洛",
    "调香师": "调香师",
    "清流": "清流",
    "嘉维尔": "嘉维尔",
    "缠丸": "缠丸",
    "慕斯": "慕斯",
    "杜宾": "杜宾",
    "艾斯黛尔": "艾丝黛尔",
    "霜叶": "霜叶",
    "芳烃": "芳烃",
    "杰西卡": "杰西卡",
    "流星": "流星",
    "白雪": "白雪",
    "安比尔": "安比尔",
    "酸糖": "酸糖",
    "梅": "梅",
    "松果": "松果",
    "古米": "古米",
    "角峰": "角峰",
    "蛇屠箱": "蛇屠箱",
    "泡泡": "泡泡",
    "坚雷": "坚雷",
    "地灵": "地灵",
    "深海色": "深海色",
    "波登可": "波登可",
    "豆苗": "豆苗",
    "罗比菈塔": "罗比菈塔",
    "孑": "孑",
    "伊桑": "伊桑",
    "卡达": "卡达",
    "豆苗": "豆苗",
    "刻刀": "刻刀",
    "宴": "宴",
    "杰克": "杰克",
    "休谟斯": "休谟斯",
    "铅踝": "铅踝",
    "跃跃": "跃跃",
    "深律": "深律",
    "维荻": "维荻",
    # 通用
    "驴": "阿米娅",
    "兔兔": "阿米娅",
    "阿米驴": "阿米娅",
    "阿米兔": "阿米娅",
    "星熊": "星熊",
    "闪灵": "闪灵",
    "陈": "陈",
    "老陈": "陈",
    "陈sir": "陈",
    "麦哲伦": "麦哲伦",
    "莫斯提马": "莫斯提马",
    "莫斯": "莫斯提马",
    "小莫": "莫斯提马",
    "煌": "煌",
    "年": "年",
    "阿": "阿",
    "刻俄柏": "刻俄柏",
    "小刻": "刻俄柏",
    "风笛": "风笛",
    "小风笛": "风笛",
    "W": "W",
    "温蒂": "温蒂",
    "早露": "早露",
    "森蚺": "森蚺",
    "棘刺": "棘刺",
    "史尔特尔": "史尔特尔",
    "夕": "夕",
    "凯尔希": "凯尔希",
    "凯太后": "凯尔希",
    "老太婆": "凯尔希",
    "歌蕾蒂娅": "歌蕾蒂娅",
    "蒂蒂": "斯卡蒂",
    "斯卡": "斯卡蒂",
    "帕拉斯": "帕拉斯",
    "卡涅利安": "卡涅利安",
    "远牙": "远牙",
    "灵知": "灵知",
    "老鲤": "老鲤",
    "令": "令",
    "菲亚梅塔": "菲亚梅塔",
    "肥鸭": "菲亚梅塔",
    "流明": "流明",
    "黑键": "黑键",
    "多萝西": "多萝西",
    "鸿雪": "鸿雪",
    "白铁": "白铁",
    "仇白": "仇白",
    "林": "林",
    "蛇蛇": "霍尔海雅",
    "送葬人": "送葬人",
    "圣葬": "圣约送葬人",
    "圣葬人": "圣约送葬人",
    "提丰": "提丰",
    "涤火": "涤火杰西卡",
    "dj": "涤火杰西卡",
    "赫德雷": "赫德雷",
    "止颂": "止颂",
    "黑骑士": "锏",
    "莱伊": "莱伊",
    "灰烬": "灰烬",
    "ash": "灰烬",
    "霜华": "霜华",
    "闪击": "闪击",
    "战车": "战车",
    "罗小黑": "罗小黑",
    "九色鹿": "九色鹿",
    "彩虹小队": "彩虹小队",
}

# 自定义替换表（用户可通过命令添加）
_custom_aliases: Dict[str, str] = {}

# 快速索引缓存
_alias_index: Dict[str, str] = {}  # 全小写去标点 → 正式名
_reverse_index: Dict[str, set] = {}  # 正式名(小写去标点) → {别名, ...}


def _load_alias_index():
    """构建快速查找索引（去标点小写化）"""
    global _alias_index, _reverse_index
    if _alias_index:
        return

    all_map = {**OPERATOR_ALIASES, **_custom_aliases}

    # 正向: 别名 → 正式名
    for alias, formal in all_map.items():
        key = remove_punctuation(alias).lower()
        if not key:
            continue
        # 最长优先覆盖（保留长别名）
        if key not in _alias_index or len(alias) > len(
            next(k for k, v in {k: v for k, v in all_map.items()
                                if remove_punctuation(k).lower() == key}.items())
        ):
            _alias_index[key] = formal

    # 反向: 正式名 → 所有别名集合
    for alias, formal in all_map.items():
        f_key = remove_punctuation(formal).lower()
        if f_key not in _reverse_index:
            _reverse_index[f_key] = set()
        _reverse_index[f_key].add(alias)


def normalize_text(text: str) -> Tuple[str, List[str]]:
    """规范化消息文本 — 将别名替换为正式名

    完全对齐 AmiyaBot replace message_created 钩子策略 (main.py:99-113):
    ```python
    for item in reversed(list(replace)):
        if item.origin in text:    # 原名已存在 → 跳过
            continue
        if item.replace in text:   # 别名存在 → 替换为原名
            text = text.replace(item.replace, item.origin)
    ```

    在此基础上增强:
    - 按别名长度降序排列（避免 "阿" 短路匹配 "阿米娅"）
    - 标记已替换的别名用于日志

    Args:
        text: 用户原始消息

    Returns:
        (normalized_text, applied_aliases): 规范化文本 + 应用的别名列表
    """
    _load_alias_index()

    result = text
    applied: List[str] = []

    # 按别名长度降序（长匹配优先，防止 "阿" → 误触发）
    # 收集所有 source_alias → formal_name 对，按 alias 长度降序
    sorted_pairs = sorted(
        _alias_index.items(),
        key=lambda x: -len(x[0]),
    )

    # 阶段1: 构建原始文本中的 alias 集合
    for alias_key, formal_name in sorted_pairs:
        # AmiyaBot 检查: 原名是否已在文本中
        if formal_name in result:
            continue

        # 别名在文本中 → 替换（简单 str.replace）
        if alias_key in result:
            result = result.replace(alias_key, formal_name)
            applied.append(alias_key)

    return result, applied


def normalize_name(name: str) -> str:
    """简化版: 仅规范化单个名称（用于 /角色 命令的参数）

    返回规范化后的名称，如果别名表中有匹配则返回正式名，否则返回原名。
    """
    _load_alias_index()

    key = remove_punctuation(name).lower()

    # 精确匹配别名
    if key in _alias_index:
        return _alias_index[key]

    # 模糊匹配（别名是 name 的子串）
    # 按别名长度降序
    for alias_key in sorted(_alias_index, key=lambda k: -len(k)):
        if alias_key in key:
            return _alias_index[alias_key]

    return name


def add_alias(alias: str, formal: str) -> bool:
    """添加自定义别名

    Returns:
        True 如果添加成功, False 如果别名已被占用
    """
    _load_alias_index()

    alias_key = remove_punctuation(alias).lower()
    formal_key = remove_punctuation(formal).lower()

    # 检查别名是否已是正式名
    if alias_key in _reverse_index:
        return False

    # 检查正式名是否已经有这个别名
    if formal_key in _reverse_index and alias in _reverse_index[formal_key]:
        return False

    _custom_aliases[alias] = formal

    # 更新索引
    if alias_key in _alias_index and len(_alias_index[alias_key]) >= len(formal):
        # 保留更长的替代
        pass
    else:
        _alias_index[alias_key] = formal

    if formal_key not in _reverse_index:
        _reverse_index[formal_key] = set()
    _reverse_index[formal_key].add(alias)

    return True


def remove_alias(alias: str) -> bool:
    """删除自定义别名"""
    global _alias_index

    alias_key = remove_punctuation(alias).lower()

    if alias in _custom_aliases:
        formal = _custom_aliases.pop(alias)
        # 重建索引
        _alias_index = {}
        _load_alias_index()
        return True

    return False


def list_aliases(formal_name: Optional[str] = None) -> Dict[str, str]:
    """列出别名

    Args:
        formal_name: 指定正式名则只返回其别名，None 返回全部

    Returns:
        {alias: formal, ...}
    """
    _load_alias_index()

    if formal_name:
        formal_key = remove_punctuation(formal_name).lower()
        result = {}
        for alias, formal in {**OPERATOR_ALIASES, **_custom_aliases}.items():
            if remove_punctuation(formal).lower() == formal_key:
                result[alias] = formal
        return result

    return {**OPERATOR_ALIASES, **_custom_aliases}
