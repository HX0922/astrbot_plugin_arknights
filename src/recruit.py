"""
公开招募标签计算模块

根据用户选择的招募标签组合，计算可能招募到的干员列表。

数据源:
  - character_table.json: 每个干员的 tagList (公招可用标签)
  - gacha_table.json: recruitRarityTable (稀有度权重)
"""

from dataclasses import dataclass
from .game_data import ArkData


@dataclass
class RecruitResult:
    char_id: str
    name: str
    rarity: int  # 0-5 (游戏内显示 1-6 星)
    tags: list[str]
    profession: str


# 用户输入 → 游戏内标签名映射
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

# 位置标签反向映射
POS_REVERSE = {"MELEE": "近战位", "RANGED": "远程位"}


class RecruitCalculator:
    """公开招募计算器"""

    def __init__(self):
        self.data = ArkData()
        self._pool = None

    @property
    def pool(self) -> list[RecruitResult]:
        if self._pool is None:
            self._load_pool()
        return self._pool

    def _load_pool(self):
        """从 character_table 提取所有可公招的干员"""
        self._pool = []
        for char_id, char in self.data.chars.items():
            rarity = char.get("rarity", 0)
            # 公招只包含 1-5 星干员（游戏内 rarity 0-4）
            if rarity > 4:
                continue

            tags = self._char_tags(char)
            if not tags:
                continue

            self._pool.append(RecruitResult(
                char_id=char_id,
                name=char.get("name", "未知"),
                rarity=rarity,
                tags=tags,
                profession=char.get("profession", ""),
            ))

        self._pool.sort(key=lambda x: -x.rarity)

    def _char_tags(self, char: dict) -> list[str]:
        """提取干员的公招标签"""
        tags = []
        # 职业
        prof = char.get("profession", "")
        if prof:
            tags.append(prof)
        # 位置
        pos = char.get("position", "")
        if pos:
            tags.append(pos)
            tags.append(POS_REVERSE.get(pos, pos))
        # tagList
        for t in char.get("tagList", []):
            tags.append(t)
        return tags

    def calculate(self, tags: list[str]) -> list[tuple[RecruitResult, list[str]]]:
        """根据标签组合计算匹配干员"""
        if not self.pool or not tags:
            return []

        # 将用户标签映射到游戏标签
        search_tags = set()
        for tag in tags:
            tag = tag.strip()
            mapped = TAG_MAP.get(tag, tag)
            search_tags.add(mapped)

        results = []
        for char in self.pool:
            char_tags = set(char.tags)
            matched = search_tags & char_tags
            if matched:
                results.append((char, list(matched)))

        results.sort(key=lambda x: (-x[0].rarity, -len(x[1])))
        return results

    def get_all_tags(self) -> list[str]:
        return list(TAG_MAP.keys())
