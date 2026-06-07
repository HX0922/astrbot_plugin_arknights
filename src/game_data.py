"""
Arknights 游戏数据加载层 — 对齐 AmiyaBot core/resource/arknightsGameData

单例模式，全局访问:
- ArknightsGameData.operators: Dict[name, Operator]
- ArknightsGameData.materials: Dict[material_id, dict]

严格对齐 AmiyaBot:
- operators dict key 是中文名 (不是 char_id)
- materials dict key 是 material_id
- 所有 Operator 方法返回与 AmiyaBot 相同的数据结构
"""

import json
import re
import string
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    import orjson

    def _json_loads(data: bytes) -> dict:
        return orjson.loads(data)
except ImportError:
    orjson = None

    def _json_loads(data: bytes) -> dict:
        return json.loads(data.decode("utf-8"))
from .operator_model import Operator, parse_template


# ── 中文标点符号 ────────────────────────────────────────
_CN_PUNCTUATION = (
    '\u3001\u3002\uff0c\uff0e\u30fb\uff01\uff1f\uff1a\uff1b'
    '\u201c\u201d\u2018\u2019\uff08\uff09\u300a\u300b\u300c\u300d'
    '\u300e\u300f\u3008\u3009\u3010\u3011\uff3b\uff3d'
    '\u2014\u2015\u2026\u2025\uff5e\uffe5'
)

RARITY_STARS = {1: "★", 2: "★★", 3: "★★★", 4: "★★★★", 5: "★★★★★", 6: "★★★★★★"}


def remove_punctuation(text: str, ignore: list = None) -> str:
    """移除中英文标点符号 — 对齐 AmiyaBot remove_punctuation"""
    punc = string.punctuation + _CN_PUNCTUATION
    if ignore:
        for i in ignore:
            punc = punc.replace(i, '')
    for ch in punc:
        text = text.replace(ch, '')
    return text


# ── 数据根目录查找 ──────────────────────────────────────

def _find_data_root() -> Path:
    """查找 ArknightsGameResource 根目录"""
    import os

    env_path = os.environ.get("AK_DATA_ROOT")
    if env_path:
        return Path(env_path)

    plugin_root = Path(__file__).resolve().parent.parent
    candidate = plugin_root / "data" / "ArknightsGameResource"
    if candidate.exists():
        return candidate

    # AstrBot 安装的数据目录
    ast_data = Path(os.environ.get("ASTRBOT_DATA", ""))
    if ast_data.exists():
        candidate = ast_data / "plugins" / "data" / "ArknightsGameResource"
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "找不到 ArknightsGameResource 数据目录。"
        "请设置 AK_DATA_ROOT 环境变量。"
    )


# ── ArknightsGameResource — 资源访问 ────────────────────

class ArknightsGameResource:
    """资源管理器 — 对齐 AmiyaBot ArknightsGameResource"""
    _data_root: Optional[Path] = None

    @classmethod
    def set_data_root(cls, path: Path):
        cls._data_root = path

    @classmethod
    def get_data_root(cls) -> Path:
        if cls._data_root is None:
            cls._data_root = _find_data_root()
        return cls._data_root

    @classmethod
    def get_skin_file(
        cls, skin_item: dict, encode_url: bool = False
    ) -> str:
        """获取完整精二立绘 — PRTS Wiki 下载 + 本地缓存

        AmiyaBot 方式: 从 skinUrls.json (PRTS Wiki URL) 下载立绘，
        缓存到 data/ArknightsGameResource/skin/{skin_id}.png
        """
        if not skin_item:
            return ""

        skin_id = skin_item.get("skin_id", "")
        if not skin_id:
            return ""

        root = cls.get_data_root()
        skin_dir = root / "skin"
        skin_dir.mkdir(parents=True, exist_ok=True)
        cache_path = skin_dir / f"{skin_id}.png"

        if not cache_path.exists():
            # 从 skinUrls.json 获取 PRTS Wiki URL
            indexes_path = root / "indexes" / "skinUrls.json"
            url = None
            if indexes_path.exists():
                try:
                    import json
                    with open(indexes_path, "r", encoding="utf-8") as f:
                        indexes = json.load(f)
                    char_id = skin_id.split("#")[0].split("@")[0]
                    if char_id in indexes and skin_id in indexes[char_id]:
                        url = indexes[char_id][skin_id]
                except Exception:
                    pass
            
            if url:
                try:
                    import urllib.request
                    urllib.request.urlretrieve(url, str(cache_path))
                except Exception:
                    pass

        if cache_path.exists():
            result = f"skin/{skin_id}.png"
            if encode_url:
                result = result.replace("#", "%23")
            return result

        return ""

    @classmethod
    def parse_template(cls, blackboard: list, description: str) -> str:
        """解析 {key:value} 模板占位符"""
        return parse_template(blackboard, description)


# ── ArknightsGameData — 主数据类 ────────────────────────

class ArknightsGameData:
    """游戏数据单例 — 对齐 AmiyaBot ArknightsGameData

    使用方式:
        data = ArknightsGameData()
        operator = data.operators["阿米娅"]
        detail, trust = operator.detail()
    """

    _instance: Optional["ArknightsGameData"] = None
    _loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self._loaded = True

        self._data_root = ArknightsGameResource.get_data_root()
        self._gamedata = self._data_root / "gamedata" / "excel"

        # AmiyaBot 风格的单例类属性
        self.operators: Dict[str, Operator] = {}  # key = 中文名
        self.materials: Dict[str, dict] = {}      # material_id → {material_id, material_name, ...}
        self.materials_map: Dict[str, str] = {}   # material_name → material_id
        self.materials_made: Dict[str, list] = {} # material_id → [{use_material_id, use_number}]
        self.materials_source: Dict[str, dict] = {}  # material_id → {stage_id: {source_rate}}
        self.stages: Dict[str, dict] = {}         # stage_id → {stage_id, code, name, ...}
        self.stages_map: Dict[str, List[str]] = {}  # code(+difficulty) → [stage_ids]
        self.side_story_map: Dict[str, dict] = {}   # activity_name → {stage_id: stage_data}
        self.enemies: Dict[str, dict] = {}        # key = 中文名 & enemyId → {info, data}

        self._load_all()

    def _load_all(self):
        """加载所有基础数据"""
        # 1. 加载干员
        chars = self._load_json("character_table.json")
        if not chars:
            return

        # 2. 应用 char_patch_table
        patch = self._load_json("char_patch_table.json")
        patch_chars = patch.get("patchChars", {}) if patch else {}
        for k, v in patch_chars.items():
            if k in chars:
                chars[k].update(v)

        # 3. 构建 Operator 实例
        # AmiyaBot 行为: 第一个遇到的名字为准，后面的不覆盖
        # (避免 char_1037_amiya3 Guard 覆盖 char_002_amiya Caster)
        for char_id, char_data in chars.items():
            op = Operator(code=char_id, data=char_data, data_root=self._data_root)
            if op.name and op.name not in self.operators:
                self.operators[op.name] = op

        # 4. 加载材料
        items = self._load_json("item_table.json")
        actual_items = items.get("items", items)
        for item_id, item_data in actual_items.items():
            if item_data.get("classifyType") == "MATERIAL":
                material = {
                    "material_id": item_id,
                    "material_name": item_data.get("name", ""),
                    "material_icon": item_data.get("iconId", ""),
                    "material_desc": item_data.get("description", ""),
                    "rarity": item_data.get("rarity", 0),
                }
                self.materials[item_id] = material
                self.materials_map[material["material_name"]] = item_id

        # 5. 加载关卡数据 (含 stages_map + side_story_map)
        self._init_stages_data()

        # 6. 加载材料合成配方 (materials_made: 逆向索引 workshopFormulas)
        building = self._load_json("building_data.json")
        workshop_formulas = building.get("workshopFormulas", {})
        for formula_id, formula in workshop_formulas.items():
            produced_id = formula.get("itemId", "")
            if not produced_id or produced_id not in self.materials:
                continue
            costs = formula.get("costs", [])
            for cost in costs:
                cost_id = cost.get("id", "")
                cost_count = cost.get("count", 0)
                if not cost_id:
                    continue
                if produced_id not in self.materials_made:
                    self.materials_made[produced_id] = []
                self.materials_made[produced_id].append({
                    "use_material_id": cost_id,
                    "use_number": cost_count,
                })

        # 7. 加载材料掉落来源 (materials_source: 来自 item stageDropList)
        for item_id, item_data in actual_items.items():
            if item_data.get("classifyType") != "MATERIAL":
                continue
            drops = item_data.get("stageDropList", [])
            if not drops:
                continue
            source = {}
            for drop in drops:
                stage_id = drop.get("stageId", "")
                occ_per = drop.get("occPer", 0)
                if stage_id:
                    source[stage_id] = {"source_rate": occ_per}
            if source:
                self.materials_source[item_id] = source

        # 8. 加载敌人数据 (对齐 AmiyaBot init_enemies)
        enemies_info = self._load_json("enemy_handbook_table.json")
        if enemies_info:
            enemies_data = self._load_level_json(
                "levels", "enemydata", "enemy_database.json"
            )
            enemies_data_map = {}
            for item in enemies_data.get("enemies", []):
                key = item.get("Key") or item.get("key", "")
                val = item.get("Value") or item.get("value")
                if key:
                    enemies_data_map[key] = val

            from collections import Counter
            name_counter = Counter()

            for e_id, info in enemies_info.get("enemyData", {}).items():
                name = info.get("name", "")
                if name == "-":
                    continue
                if name in name_counter:
                    name_counter[name] += 1
                    name += f"（{name_counter[name]}）"
                else:
                    name_counter[name] = 1
                item = {"info": info, "data": enemies_data_map.get(e_id)}
                self.enemies[name] = item
                self.enemies[info["enemyId"]] = item

    def _load_json(self, filename: str) -> dict:
        path = self._gamedata / filename
        if not path.exists():
            return {}
        try:
            with open(path, "rb") as f:
                return _json_loads(f.read())
        except Exception:
            return {}

    def _load_level_json(self, *subdirs: str) -> dict:
        """加载 gamedata 下的非 excel 子目录 JSON（如 levels/enemydata/）"""
        path = Path(self._gamedata).parent.joinpath(*subdirs)
        if not path.exists():
            return {}
        try:
            with open(path, "rb") as f:
                return _json_loads(f.read())
        except Exception:
            return {}

    def _init_stages_data(self):
        """构建 stages / stages_map / side_story_map — 对齐 AmiyaBot init_stages()"""
        stage_table = self._load_json("stage_table.json")
        stages_raw = stage_table.get("stages", stage_table)

        # 加载活动表 (可能不存在)
        activity_table = self._load_json("activity_table.json")
        activity_info = activity_table.get("basicInfo", activity_table)

        # 筛选插曲/别传
        def _is_ss(key, item):
            if item.get("isReplicate"):
                return False
            if item.get("type") == "MINISTORY":
                return True
            return item.get("type", "").endswith("SIDE") or item.get("displayType") == "SIDESTORY"

        side_story = [
            item for key, item in activity_info.items()
            if isinstance(item, dict) and _is_ss(key, item)
        ]
        side_story.sort(key=lambda n: n.get("startTime", 0), reverse=True)

        side_story_map: Dict[str, dict] = {n["name"]: {} for n in side_story if n.get("name")}
        stages: Dict[str, dict] = {}
        stages_map: Dict[str, List[str]] = {}

        for stage_id, item in stages_raw.items():
            if not item.get("name"):
                continue

            # 难度后缀
            level = ""
            if "#f#" in stage_id:
                level = "_hard"
            if "easy" in stage_id:
                level = "_easy"
            if "tough" in stage_id:
                level = "_tough"
            if "#s" in stage_id:
                level = "_sixstar"

            stage_key = item["code"] + level
            stage_key_name = remove_punctuation(item["name"].strip()) + level

            # 存入 stages
            stages[stage_id] = {**item, "levelData": None, "activity": ""}

            # 匹配活动
            code = item.get("code", "")
            if code.startswith("GT"):
                if "骑兵与猎人" in side_story_map:
                    side_story_map["骑兵与猎人"][stage_id] = stages[stage_id]
            elif code.startswith("OF"):
                if "火蓝之心" in side_story_map:
                    side_story_map["火蓝之心"][stage_id] = stages[stage_id]
            else:
                for ss_item in side_story:
                    ss_code = ss_item.get("id", "")
                    ss_name = ss_item.get("name", "")
                    if ss_code and ss_code in stage_id:
                        if ss_name in side_story_map:
                            side_story_map[ss_name][stage_id] = stages[stage_id]

            # 构建 stages_map (双向索引)
            for key in [stage_key, stage_key_name]:
                if key not in stages_map:
                    stages_map[key] = []
                if stage_id not in stages_map[key]:
                    stages_map[key].append(stage_id)

        self.stages = stages
        self.stages_map = stages_map
        self.side_story_map = side_story_map

    # ── 搜索辅助 ──────────────────────────────────────

    def search_items(self, keyword: str) -> list:
        kw = keyword.lower()
        results = []
        for mid, mat in self.materials.items():
            if kw in mat["material_name"].lower():
                results.append(mat)
        return results


# ── 向后兼容的简化接口 ────────────────────────────────

class ArkData:
    """向后兼容简化数据接口（提供 raw dict 访问给不需要 Operator 对象的模块）"""
    _instance: Optional["ArkData"] = None
    _loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self._loaded = True
        self._data_root = ArknightsGameResource.get_data_root()
        self._gamedata = self._data_root / "gamedata" / "excel"
        self._chars = None
        self._items = None
        self._stages = None
        self._enemies = None
        self._skins = None
        self._name_index = None

    @property
    def chars(self) -> dict:
        if self._chars is None:
            self._chars = self._load_json("character_table.json")
            patch = self._load_json("char_patch_table.json")
            if patch:
                for k, v in patch.get("patchChars", {}).items():
                    if k in self._chars:
                        self._chars[k].update(v)
        return self._chars

    @property
    def items(self) -> dict:
        if self._items is None:
            raw = self._load_json("item_table.json")
            self._items = raw.get("items", raw)
        return self._items

    @property
    def stages(self) -> dict:
        if self._stages is None:
            raw = self._load_json("stage_table.json")
            self._stages = raw.get("stages", raw)
        return self._stages

    @property
    def enemies(self) -> dict:
        if self._enemies is None:
            data = self._load_json("enemy_handbook_table.json")
            self._enemies = data.get("enemyData", {}) if data else {}
        return self._enemies

    @property
    def skins(self) -> dict:
        if self._skins is None:
            data = self._load_json("skin_table.json")
            self._skins = data.get("charSkins", {}) if data else {}
        return self._skins

    def _load_json(self, filename: str) -> dict:
        path = self._gamedata / filename
        if not path.exists():
            return {}
        try:
            with open(path, "rb") as f:
                return _json_loads(f.read())
        except Exception:
            return {}

    @property
    def name_index(self) -> dict:
        if self._name_index is None:
            self._name_index = {}
            for char_id, char in self.chars.items():
                name = char.get("name", "")
                if name:
                    key = name.lower()
                    self._name_index.setdefault(key, []).append(char_id)
        return self._name_index

    def resolve_char(self, name: str) -> list:
        key = name.strip().lower()
        if key in self.name_index:
            return self.name_index[key]
        results = []
        for index_key, char_ids in self.name_index.items():
            if key in index_key:
                results.extend(char_ids)
        return list(dict.fromkeys(results))

    def get_char_image_path(self, char_id: str, img_type: str = "portrait") -> str:
        base = self._data_root
        if img_type == "portrait":
            for suffix in ["", "_1", "_2"]:
                path = base / "portrait" / f"{char_id}{suffix}.png"
                if path.exists():
                    return str(path)
        elif img_type == "avatar":
            path = base / "avatar" / f"{char_id}.png"
            if path.exists():
                return str(path)
        return ""
