"""
Arknights 游戏数据加载层

单例模式封装 ArknightsGameResource 的 JSON 数据。
延迟加载——首次访问属性时才读取对应 JSON 文件。

数据路径优先级:
1. AK_DATA_ROOT 环境变量
2. 项目 data/ArknightsGameResource 目录 (Git Submodule)
"""

import json
import os
from pathlib import Path


# ── 数据根目录查找 ──────────────────────────────────────

def _find_data_root() -> Path:
    """查找 ArknightsGameResource 根目录"""
    # 1. 环境变量
    env_path = os.environ.get("AK_DATA_ROOT")
    if env_path:
        return Path(env_path)

    # 2. 项目 data/ArknightsGameResource
    current = Path(__file__).resolve().parent.parent
    candidate = current / "data" / "ArknightsGameResource"
    if candidate.exists():
        return candidate

    # 3. AstrBot 插件目录
    from astrbot.core.utils.path_utils import get_plugin_data_dir
    plugin_data = Path(get_plugin_data_dir("arknights"))
    candidate = plugin_data / "ArknightsGameResource"
    if candidate.exists():
        return candidate

    raise FileNotFoundError(
        "找不到 ArknightsGameResource 数据目录。\n"
        "请设置 AK_DATA_ROOT 环境变量，或运行:\n"
        "  git submodule update --init --depth 1"
    )


# ── 单例数据类 ───────────────────────────────────────────

RARITY_STARS = {
    0: "★", 1: "★", 2: "★★", 3: "★★★",
    4: "★★★★", 5: "★★★★★", 6: "★★★★★★",
}


class ArkData:
    """Arknights 游戏数据单例

    延迟加载所有 JSON 文件，提供类型化访问接口。
    """
    _instance = None
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self._loaded = True
        self._data_root = _find_data_root()
        self._gamedata = self._data_root / "gamedata" / "excel"

        # 延迟加载缓存
        self._chars = None
        self._items = None
        self._stages = None
        self._enemies = None
        self._skins = None
        self._char_patch = None
        self._name_index = None
        self._alias_map = {}

    # ── JSON 加载 ──────────────────────────────────────

    def _load_json(self, filename: str) -> dict:
        path = self._gamedata / filename
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return {}

    # ── 属性（延迟加载）────────────────────────────────

    @property
    def chars(self) -> dict:
        if self._chars is None:
            self._chars = self._load_json("character_table.json")
            # 应用 character_patch_table 覆盖
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

    @property
    def gacha_table(self) -> dict:
        return self._load_json("gacha_table.json")

    # ── 名称索引 ──────────────────────────────────────

    @property
    def name_index(self) -> dict:
        """中文名 → [char_id, ...] 索引"""
        if self._name_index is None:
            self._name_index = {}
            for char_id, char in self.chars.items():
                name = char.get("name", "")
                if name:
                    key = name.lower()
                    self._name_index.setdefault(key, []).append(char_id)
            # 应用别名
            for alias, target in self._alias_map.items():
                key = alias.lower()
                target_key = target.lower()
                if target_key in self._name_index:
                    self._name_index[key] = self._name_index[target_key]
        return self._name_index

    def resolve_char(self, name: str) -> list[str]:
        """通过名称解析干员 ID 列表"""
        key = name.strip().lower()
        # 精确匹配
        if key in self.name_index:
            return self.name_index[key]
        # 模糊匹配
        results = []
        for index_key, char_ids in self.name_index.items():
            if key in index_key:
                results.extend(char_ids)
        return list(dict.fromkeys(results))  # 去重保序

    # ── 图片路径 ──────────────────────────────────────

    def get_char_image_path(self, char_id: str, img_type: str = "portrait") -> str:
        """获取干员图片绝对路径

        img_type: "portrait" (半身像) | "avatar" (头像) | "skin" (皮肤)
        """
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

    def get_item_image_path(self, item_id: str) -> str:
        path = self._data_root / "item" / f"{item_id}.png"
        return str(path) if path.exists() else ""

    def get_skill_image_path(self, skill_id: str) -> str:
        path = self._data_root / "skill" / f"skill_icon_{skill_id}.png"
        return str(path) if path.exists() else ""

    # ── 搜索辅助 ──────────────────────────────────────

    def search_items(self, keyword: str) -> list[dict]:
        """按名称模糊搜索物品"""
        kw = keyword.lower()
        results = []
        for item_id, item in self.items.items():
            name = item.get("name", "")
            if kw in name.lower():
                results.append({"id": item_id, **item})
        return results

    def search_stages(self, keyword: str) -> list[dict]:
        """按 ID 或名称搜索关卡"""
        kw = keyword.lower()
        results = []
        for stage_id, stage in self.stages.items():
            code = stage.get("code", "")
            name = stage.get("name", "")
            if kw in stage_id.lower() or kw in code.lower() or kw in name:
                results.append({"id": stage_id, **stage})
        return results

    def search_enemies(self, keyword: str) -> list[dict]:
        """按名称搜索敌人"""
        kw = keyword.lower()
        results = []
        for enemy_id, enemy in self.enemies.items():
            if kw in enemy.get("name", "").lower():
                results.append({"id": enemy_id, **enemy})
        return results
