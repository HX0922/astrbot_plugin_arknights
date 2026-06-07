"""
明日方舟干员模型 — 严格对齐 AmiyaBot builder/operatorBuilder.py OperatorImpl

所有方法签名、返回格式、数据解析逻辑与 AmiyaBot 完全一致。
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

try:
    import orjson as _orjson
    def _json_loads(data): return _orjson.loads(data)
except ImportError:
    _orjson = None
    def _json_loads(data): return json.loads(data.decode("utf-8"))

_JSON_CACHE = {}

STR_DICT = Dict[str, Any]
LIST_STR_DICT = List[STR_DICT]

# ── 常量（对齐 common.py）────────────────────────────

CLASSES = {
    "CASTER": "术师", "MEDIC": "医疗", "PIONEER": "先锋",
    "SNIPER": "狙击", "SPECIAL": "特种", "SUPPORT": "辅助",
    "TANK": "重装", "WARRIOR": "近卫",
}

TOKEN_CLASSES: dict[str, str] = {"TOKEN": "召唤物", "TRAP": "装置"}

HIGH_STAR = {"5": "资深干员", "6": "高级资深干员"}

TYPES = {"ALL": "不限部署位", "MELEE": "近战位", "RANGED": "远程位"}

HTML_SYMBOL = {"<替身>": "&lt;替身&gt;", "<支援装置>": "&lt;支援装置&gt;"}


def integer(value):
    if isinstance(value, float) and int(value) == value:
        return int(value)
    return value


def snake_case_to_pascal_case(snake_case: str):
    """将 snake_case 转为 camelCase"""
    words = snake_case.split('_')
    return ''.join(word.title() if i > 0 else word.lower() for i, word in enumerate(words))


def remove_xml_tag(text: str) -> str:
    if not text:
        return ""
    return re.compile(r"<[^>]+>", re.S).sub("", text)


def html_tag_format(text: str) -> str:
    if text is None:
        return ""
    for o, f in HTML_SYMBOL.items():
        text = text.replace(o, f)
    return remove_xml_tag(text)


def parse_template(blackboard: list, description: str) -> str:
    """对齐 AmiyaBot parse_template — 生成 [cl value@#174CC6 cle] 格式"""
    if not description or not blackboard:
        return html_tag_format(description or "")

    formatter = {"0%": lambda v: f"{round(v * 100)}%"}
    data_dict = {
        item["key"]: item.get("valueStr") or item.get("value")
        for item in blackboard
    }

    desc = html_tag_format(description.replace(">-{", ">{"))
    format_str = re.findall(r"({([^}]+)})", desc)
    if format_str:
        for desc_item in format_str:
            key = desc_item[1].split(":")
            fd = key[0].lower().strip("-")
            if fd in data_dict:
                value = integer(data_dict[fd])
                if len(key) >= 2 and key[1] in formatter and value:
                    value = formatter[key[1]](value)
                desc = desc.replace(
                    desc_item[0], f" [cl {value}@#174CC6 cle] "
                )
    return desc


def build_range(grids: list) -> str:
    """对齐 AmiyaBot build_range — 返回 □■ 格式的文本"""
    if not grids:
        return "无范围"

    _max = [0, 0, 0, 0]
    for item in [{"row": 0, "col": 0}] + grids:
        row, col = item["row"], item["col"]
        if row <= _max[0]:
            _max[0] = row
        if row >= _max[1]:
            _max[1] = row
        if col <= _max[2]:
            _max[2] = col
        if col >= _max[3]:
            _max[3] = col

    width = abs(_max[2]) + _max[3] + 1
    height = abs(_max[0]) + _max[1] + 1

    empty, block, origin = "　", "□", "■"
    range_map = []
    for h in range(height):
        range_map.append([empty for _ in range(width)])

    for item in grids:
        x = abs(_max[0]) + item["row"]
        y = abs(_max[2]) + item["col"]
        range_map[x][y] = block
    range_map[abs(_max[0])][abs(_max[2])] = origin

    return "".join(["".join(item) + "\n" for item in range_map])


# ── Operator 类（对齐 OperatorImpl）─────────────────

class Operator:
    """干员数据对象 — 严格对齐 AmiyaBot builder/operatorBuilder.OperatorImpl"""

    def __init__(
        self,
        code: str,
        data: dict,
        is_recruit: bool = False,
        data_root: Optional[Path] = None,
    ):
        self.data = data
        self._data_root = data_root or Path(".")
        self._gamedata = self._data_root / "gamedata" / "excel"

        # ── 加载子数据表 ──
        sub_prof_dict = self._load_json("uniequip_table.json").get("subProfDict", {})
        character_table = self._load_json("character_table.json")
        team_table = self._load_json("handbook_team_table.json")
        item_table = self._load_json("item_table.json").get("items", {})
        range_table = self._load_json("range_table.json")

        data["name"] = data.get("name", "").strip()

        # ── 基础标识 ──
        self.id = code
        self.cv = {}

        # ── 星级 ──
        if isinstance(data.get("rarity"), str):
            self.rarity = int(data["rarity"].split("_")[-1])  # "TIER_5" → 5
        else:
            self.rarity = data.get("rarity", 0) + 1  # int 0-index → 1-index

        self.type = TYPES.get(data.get("position", ""), "")
        self.tags: List[str] = []
        self.range = "无范围"
        self.number = data.get("displayNumber", "")

        self.name = data["name"]
        self.en_name = data.get("appellation", "")
        self.wiki_name = data["name"]
        self.index_name = re.sub(r"[^\w]", "", data["name"])  # remove_punctuation

        # ── 职业 ──
        self.classes = CLASSES.get(data.get("profession", ""), data.get("profession", ""))
        self.classes_sub = sub_prof_dict.get(
            data.get("subProfessionId", ""), {}
        ).get("subProfessionName", data.get("subProfessionId", ""))
        self.classes_code = data.get("profession", "")

        # ── 种族/画师 ──
        self.sex = "未知"
        self.race = "未知"
        self.drawer = "未知"

        # ── 阵营/势力/队伍 (来自 handbook_team_table) ──
        self.team_id = data.get("teamId", "")
        self.team = team_table.get(self.team_id, {}).get("powerName", "未知") if self.team_id else "未知"
        self.group_id = data.get("groupId", "")
        self.group = team_table.get(self.group_id, {}).get("powerName", "未知") if self.group_id else "未知"
        self.nation_id = character_table.get(code, {}).get("nationId", data.get("nationId", ""))
        self.nation = team_table.get(self.nation_id, {}).get("powerName", "未知") if self.nation_id else "未知"

        self.birthday = "未知"
        self.origin_name = "未知"

        self.profile = data.get("itemUsage") or "无"
        self.impression = data.get("itemDesc") or "无"

        # 信物
        self.potential_item = ""
        if data.get("potentialItemId") in item_table:
            self.potential_item = item_table[data["potentialItemId"]].get("description", "")

        self.limit = False
        self.unavailable = False
        self.is_recruit = is_recruit
        self.is_classic = "classicPotentialItemId" in data and bool(data.get("classicPotentialItemId"))
        self.is_sp = data.get("isSpChar", False)

        # ── tags（对齐 __tags） ──
        tags = [self.classes, self.type]
        if str(self.rarity) in HIGH_STAR:
            tags.append(HIGH_STAR[str(self.rarity)])
        self.tags = (data.get("tagList") or []) + tags

        # ── CV ──
        word_data = self._load_json("charword_table.json")
        if code in word_data.get("voiceLangDict", {}):
            voice_lang = word_data["voiceLangDict"][code].get("dict", {})
            self.cv = {
                word_data.get("voiceLangTypeDict", {}).get(name, {}).get("name", name): item.get("cvName", "")
                for name, item in voice_lang.items()
            }

        # ── 范围 ──
        phases = data.get("phases", [])
        if phases:
            range_id = phases[-1].get("rangeId")
            if range_id and range_id in range_table:
                self.range = build_range(range_table[range_id].get("grids", []))

        # ── 种族（从档案提取） ──
        for story in self._raw_stories():
            if story.get("story_title") == "基础档案":
                r = re.search(r"\n【种族】.*?(\S+).*?\n", story.get("story_text", ""))
                if r:
                    self.race = str(r.group(1))
                r = re.search(r"【生日】(\S+)", story.get("story_text", ""))
                if r:
                    self.birthday = str(r.group(1))
                break

        # ── 画师（从皮肤提取） ──
        skins = self._raw_skins_list()
        if skins:
            first_skin = skins[0]
            display = first_skin.get("displaySkin", {})
            drawers = display.get("drawerList", [])
            if drawers:
                self.drawer = drawers[-1]

        # ── 真名（从 char_meta_table 异格组提取） ──
        sp_char = self._load_json("char_meta_table.json").get("spCharGroups", {})
        for oid, group in sp_char.items():
            if code in group:
                self.origin_name = character_table.get(oid, {}).get("name", "未知")

        # ── 异格名称处理 ──
        if code in ["char_1001_amiya2", "char_1037_amiya3"]:
            self.name = f"阿米娅{self.classes}"
            self.en_name = "Amiya" + data.get("profession", "").title()
            self.wiki_name = f"阿米娅({self.classes})"
            self.origin_name = "阿米娅"

        # ── 语音列表 ──
        self._voice_list = self._build_voice_list(code)

    # ════════════════════════════════════════════════════
    # 数据层方法
    # ════════════════════════════════════════════════════

    def _load_json(self, filename: str) -> dict:
        if filename in _JSON_CACHE:
            return _JSON_CACHE[filename]
        path = self._gamedata / filename
        if not path.exists():
            _JSON_CACHE[filename] = {}
            return {}
        try:
            with open(path, "rb") as f:
                data = _json_loads(f.read())
        except Exception:
            data = {}
        _JSON_CACHE[filename] = data
        return data

    def _raw_stories(self) -> list:
        """从 handbook_info_table 获取原始档案"""
        stories_data = self._load_json("handbook_info_table.json").get("handbookDict", {})
        if self.id in stories_data:
            result = []
            for item in stories_data[self.id].get("storyTextAudio", []):
                stories = item.get("stories", [])
                if stories:
                    result.append({
                        "story_title": item.get("storyTitle", ""),
                        "story_text": stories[0].get("storyText", ""),
                    })
            return result
        return []

    def _raw_skins_list(self) -> list:
        """从 skin_table 获取原始皮肤列表"""
        skin_table = self._load_json("skin_table.json")
        all_skins = skin_table.get("charSkins", {})
        result = []
        for skin_id, skin_data in all_skins.items():
            if skin_data.get("charId") == self.id or skin_id.startswith(self.id):
                result.append(skin_data)
        return sorted(result, key=lambda n: n.get("displaySkin", {}).get("getTime", 0))

    def _build_voice_list(self, code: str) -> list:
        """构建语音列表"""
        cw = self._load_json("charword_table.json").get("charWords", {})
        result = []
        for wid, wd in cw.items():
            if wd.get("charId") == code:
                result.append({
                    "voice_title": wd.get("voiceTitle", ""),
                    "voice_text": wd.get("voiceText", ""),
                    "voice_no": wd.get("voiceAsset", ""),
                })
        return result

    # ════════════════════════════════════════════════════
    # 公开方法（对齐 AmiyaBot Operator 抽象类）
    # ════════════════════════════════════════════════════

    def dict(self) -> STR_DICT:
        return {
            "name": self.name, "en_name": self.en_name,
            "rarity": self.rarity, "classes": self.classes,
            "classes_sub": self.classes_sub, "classes_code": self.classes_code,
            "type": self.type,
        }

    def detail(self) -> Tuple[STR_DICT, STR_DICT]:
        """对齐 AmiyaBot detail() — 返回 (属性, favorKeyFrames 信赖加成)"""
        items = self._load_json("item_table.json").get("items", {})

        token_id = "p_" + self.id
        token = items.get(token_id, {})

        phases = self.data.get("phases", [])
        if not phases:
            return {}, {}

        max_phases = phases[-1]
        max_attr = max_phases.get("attributesKeyFrames", [{}])[-1].get("data", {})

        trait = html_tag_format(self.data.get("description", ""))
        if self.data.get("trait"):
            candidates = self.data["trait"].get("candidates", [])
            if candidates:
                max_trait = candidates[-1]
                trait = parse_template(
                    max_trait.get("blackboard", []),
                    max_trait.get("overrideDescripton") or trait,
                )

        detail = {
            "operator_trait": trait.replace("\\\\n", "\\n"),
            "operator_usage": self.data.get("itemUsage") or "",
            "operator_quote": self.data.get("itemDesc") or "",
            "operator_token": token.get("description", ""),
            "max_level": f"{len(phases) - 1} - {max_phases.get('maxLevel', 0)}",
        }
        detail.update(max_attr)

        trust = self.data.get("favorKeyFrames", [{}])[-1].get("data", {})

        return detail, trust

    def talents(self) -> LIST_STR_DICT:
        """对齐 AmiyaBot — 取最后一个 candidate"""
        talents = []
        if self.data.get("talents"):
            for item in self.data["talents"]:
                max_item = item["candidates"][-1]
                talents.append({
                    "talents_name": max_item["name"],
                    "talents_desc": html_tag_format(max_item.get("description", "")),
                })
        return talents

    def potential(self) -> LIST_STR_DICT:
        potential = []
        if self.data.get("potentialRanks"):
            for index, item in enumerate(self.data["potentialRanks"]):
                potential.append({
                    "potential_desc": item.get("description", ""),
                    "potential_rank": index + 1,  # 1-indexed
                })
        return potential

    def evolve_costs(self) -> LIST_STR_DICT:
        evolve_cost = []
        for index, phases in enumerate(self.data.get("phases", [])):
            if phases.get("evolveCost"):
                for item in phases["evolveCost"]:
                    evolve_cost.append({
                        "evolve_level": index,
                        "use_material_id": item.get("id", ""),
                        "use_number": item.get("count", 0),
                    })
        return evolve_cost

    def skills(
        self,
    ) -> Tuple[LIST_STR_DICT, List[str], LIST_STR_DICT, Dict[str, LIST_STR_DICT]]:
        """对齐 AmiyaBot skills()"""
        skill_data = self._load_json("skill_table.json")
        range_data = self._load_json("range_table.json")

        skills: LIST_STR_DICT = []
        skills_id: List[str] = []
        skills_cost: LIST_STR_DICT = []
        skills_desc: Dict[str, LIST_STR_DICT] = {}

        # 技能等级升级消耗
        skill_level_up = self.data.get("allSkillLvlup", [])
        if skill_level_up:
            for index, item in enumerate(skill_level_up):
                if item.get("lvlUpCost"):
                    for cost in item["lvlUpCost"]:
                        skills_cost.append({
                            "skill_no": None,
                            "level": index + 2,
                            "mastery_level": 0,
                            "use_material_id": cost.get("id", ""),
                            "use_number": cost.get("count", 0),
                        })

        for index, item in enumerate(self.data.get("skills", [])):
            code = item.get("skillId", "")
            if code not in skill_data:
                continue

            detail = skill_data[code]
            icon = detail.get("iconId") or detail.get("skillId") or code

            if not detail:
                continue

            skills_id.append(code)

            if code not in skills_desc:
                skills_desc[code] = []

            for lev, desc in enumerate(detail.get("levels", [])):
                description = parse_template(
                    desc.get("blackboard", []), desc.get("description", "")
                )

                skill_range = self.range
                if desc.get("rangeId") in range_data:
                    skill_range = build_range(
                        range_data[desc["rangeId"]].get("grids", [])
                    )

                sp_data = desc.get("spData", {})
                skills_desc[code].append({
                    "skill_level": lev + 1,
                    "skill_type": desc.get("skillType", 0),
                    "sp_type": sp_data.get("spType", 1),
                    "sp_init": sp_data.get("initSp", 0),
                    "sp_cost": sp_data.get("spCost", 0),
                    "duration": integer(desc.get("duration", 0)),
                    "description": description.replace("\\\\n", "\\n"),
                    "max_charge": sp_data.get("maxChargeTime", 0),
                    "range": skill_range,
                })

            # 专精消耗
            level_up_data = item.get("specializeLevelUpData") or item.get("levelUpCostCond") or []
            for lev, cond in enumerate(level_up_data):
                if not cond.get("levelUpCost"):
                    continue
                for cost in cond["levelUpCost"]:
                    skills_cost.append({
                        "skill_no": code,
                        "level": lev + 8,
                        "mastery_level": lev + 1,
                        "use_material_id": cost.get("id", ""),
                        "use_number": cost.get("count", 0),
                    })

            skills.append({
                "skill_no": code,
                "skill_index": index + 1,
                "skill_name": detail["levels"][0].get("name", f"技能{code}"),
                "skill_icon": icon,
            })

        return skills, skills_id, skills_cost, skills_desc

    def building_skills(self) -> LIST_STR_DICT:
        """对齐 AmiyaBot building_skills()"""
        building_data = self._load_json("building_data.json")
        building_skills = building_data.get("buffs", {})

        skills = []
        if self.id in building_data.get("chars", {}):
            char_buff = building_data["chars"][self.id]
            for buff in char_buff.get("buffChar", []):
                for item in buff.get("buffData", []):
                    buff_id = item.get("buffId", "")
                    if buff_id in building_skills:
                        skill = building_skills[buff_id]
                        skills.append({
                            "bs_unlocked": item.get("cond", {}).get("phase", ""),
                            "bs_icon": skill.get("skillIcon", ""),
                            "bs_name": skill.get("buffName", ""),
                            "bs_desc": html_tag_format(skill.get("description", "")),
                        })
        return skills

    def voices(self) -> LIST_STR_DICT:
        return [
            {
                "voice_title": item.get("voice_title", ""),
                "voice_text": item.get("voice_text", ""),
                "voice_no": item.get("voice_no", ""),
            }
            for item in self._voice_list
        ]

    def stories(self) -> LIST_STR_DICT:
        return self._raw_stories()

    def skins(self) -> LIST_STR_DICT:
        skins = []
        skin_sort = 0
        skin_lvl = {
            "1": ("初始", "stage0"),
            "1+": ("精英一", "stage1"),
            "2": ("精英二", "stage2"),
        }

        for item in self._raw_skins_list():
            skin_data = item.get("displaySkin", {})
            skin_id = item.get("skinId", "")

            skin_info = skin_id.split("#")
            skin_index = skin_info[1] if len(skin_info) > 1 else ""

            skin_name = ""
            if "@" not in skin_id and skin_index in skin_lvl:
                skin_name, skin_key = skin_lvl[skin_index]
            else:
                skin_sort += 1
                skin_key = f"skin{skin_sort}"

            skins.append({
                "char_name": self.name,
                "skin_id": skin_id,
                "skin_key": skin_key,
                "skin_name": skin_data.get("skinName") or skin_name,
                "skin_drawer": (skin_data.get("drawerList") or [""])[-1],
                "skin_group": skin_data.get("skinGroupName") or "",
                "skin_content": skin_data.get("dialog") or "",
                "skin_usage": skin_data.get("usage") or f"{skin_name}立绘",
                "skin_desc": skin_data.get("description") or "",
                "skin_source": skin_data.get("obtainApproach") or "",
                "skin_voice": item.get("voiceId", ""),
                "skin_voice_type": item.get("voiceType", ""),
            })

        return skins

    def modules(self) -> LIST_STR_DICT:
        """对齐 AmiyaBot modules()"""
        equips = self._load_json("uniequip_table.json")
        equips_battle = self._load_json("battle_equip_table.json")

        equips_rel = equips.get("charEquip", {})
        modules_list = equips.get("equipDict", {})
        mission_list = equips.get("missionList", {})

        modules = []
        if self.id in equips_rel:
            for m_id in equips_rel[self.id]:
                module = modules_list.get(m_id, {})
                if not module:
                    continue

                module = dict(module)  # shallow copy
                module["missions"] = []
                module["detail"] = equips_battle.get(m_id)

                for mission in module.get("missionList", []):
                    module["missions"].append(mission_list.get(mission, {}))

                modules.append(module)

        return modules

    def tokens(self) -> dict:
        """对齐 AmiyaBot tokens() — 返回 {id: detail_dict}"""
        skill_table = self._load_json("skill_table.json")
        character_table = self._load_json("character_table.json")

        token_list = {}

        def token_detail(tok: "Operator"):
            data = character_table.get(tok.id, {})
            skills = {}
            for sk in data.get("skills", []):
                sid = sk.get("skillId")
                if not sid or sid in skills:
                    continue
                if sid in skill_table:
                    sk_data = skill_table[sid]
                    skills[sid] = {
                        **sk_data,
                        "levels": [
                            {
                                **nn,
                                "description": parse_template(
                                    nn.get("blackboard", []),
                                    nn.get("description", "")
                                ) if nn.get("description") else "",
                            }
                            for nn in sk_data.get("levels", [])
                        ],
                    }

            return {
                "id": tok.id, "type": tok.type,
                "name": tok.name, "en_name": tok.en_name,
                "description": tok.description, "attr": tok.attr,
                "talents": data.get("talents", []),
                "skills": skills, "data": data,
            }

        if self.data.get("displayTokenDict"):
            for key in self.data["displayTokenDict"].keys():
                if key in _tokens_map:
                    token = _tokens_map[key]
                    token_list[token.id] = token_detail(token)

        if self.data.get("skills"):
            for skill in self.data["skills"]:
                otk = skill.get("overrideTokenKey")
                if otk and otk in _tokens_map:
                    token = _tokens_map[otk]
                    if token.id not in token_list:
                        token_list[token.id] = token_detail(token)

        return token_list

    def __repr__(self) -> str:
        stars = "★" * self.rarity
        return f"Operator({stars} {self.name} [{self.classes}])"

    def __str__(self) -> str:
        return f"{self.id}_{self.name}"


# ── 全局 Token 注册表 ───────────────────────────────

_tokens_map: Dict[str, Any] = {}
