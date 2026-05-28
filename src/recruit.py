"""
公开招募标签计算模块

根据用户选择的招募标签组合，计算可能招募到的干员列表。
支持高稀有标签识别（资深干员、高级资深干员）。

数据源: gacha_table.json (公招池) + character_table.json (干员信息)
"""

from dataclasses import dataclass, field
from .game_data import ArkData


@dataclass
class RecruitResult:
    """招募结果"""
    char_id: str
    name: str
    rarity: int  # 0-5 (游戏内显示为 1-6 星)
    tags: list[str]
    profession: str


class RecruitCalculator:
    """公开招募计算器"""

    # 标签 → 游戏数据 tag 映射
    TAG_MAP = {
        "狙击": "狙击", "术师": "术师", "近卫": "近卫",
        "重装": "重装", "辅助": "辅助", "特种": "特种",
        "医疗": "医疗", "先锋": "先锋",
        "近战位": "近战位", "远程位": "远程位",
        "输出": "输出", "防护": "防护", "生存": "生存",
        "治疗": "治疗", "费用回复": "费用回复",
        "支援": "支援", "削弱": "削弱",
        "控场": "控场", "爆发": "爆发",
        "召唤": "召唤", "快速复活": "快速复活",
        "位移": "位移", "减速": "减速",
        "资深干员": "资深干员", "高级资深干员": "高级资深干员",
    }

    def __init__(self):
        self.data = ArkData()
        self._pool = None

    @property
    def pool(self) -> list[RecruitResult]:
        """公招干员池"""
        if self._pool is None:
            self._load_pool()
        return self._pool

    def _load_pool(self):
        """从 gacha_table.json 加载公招池"""
        gacha = self.data.gacha_table
        recruit_detail = gacha.get("recruitDetail", {})
        avail_chars = recruit_detail.get("availChars", {})

        # 解析可用干员
        self._pool = []
        for rarity, char_list in avail_chars.items():
            try:
                rarity_int = int(rarity)
            except ValueError:
                continue
            for char_id in char_list:
                char = self.data.chars.get(char_id, {})
                if not char:
                    continue
                tags = self._get_char_tags(char)
                self._pool.append(RecruitResult(
                    char_id=char_id,
                    name=char.get("name", "未知"),
                    rarity=rarity_int,
                    tags=tags,
                    profession=char.get("profession", ""),
                ))

        # 按稀有度降序
        self._pool.sort(key=lambda x: -x.rarity)

    def _get_char_tags(self, char: dict) -> list[str]:
        """从干员数据提取公招标签"""
        tags = [
            # 职业
            char.get("profession", ""),
            char.get("position", ""),  # MELEE / RANGED
        ]
        # 词缀标签 (tagList)
        tags.extend(char.get("tagList", []))
        return [t for t in tags if t]

    def calculate(self, tags: list[str]) -> list[tuple[RecruitResult, list[str]]]:
        """根据标签组合计算匹配干员

        Args:
            tags: 用户输入的标签列表

        Returns:
            [(干员, [匹配标签]), ...] 按稀有度降序
        """
        if not self.pool:
            return []

        # 翻译标签
        mapped_tags = set()
        for tag in tags:
            tag = tag.strip()
            if tag in self.TAG_MAP:
                mapped_tags.add(self.TAG_MAP[tag])
            elif tag in self.POS_MAP:
                mapped_tags.add(self.POS_MAP[tag])
            else:
                mapped_tags.add(tag)

        results = []
        for char in self.pool:
            char_tags = set(char.tags)
            matched = mapped_tags & char_tags
            if matched:
                results.append((char, list(matched)))

        # 排序: 稀有度降序 → 匹配标签数量降序
        results.sort(key=lambda x: (-x[0].rarity, -len(x[1])))
        return results

    # 位置映射
    POS_MAP = {
        "近战": "MELEE",
        "远程": "RANGED",
    }

    def get_all_tags(self) -> list[str]:
        """返回所有可用标签"""
        return list(self.TAG_MAP.keys())
