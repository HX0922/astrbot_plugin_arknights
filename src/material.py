"""
材料/物品查询模块 — 完整对齐 AmiyaBot MaterialData

提供 MaterialData 类:
- init_materials(): 初始化材料名称列表
- check_material(name): 返回材料完整信息（info/children/source/recommend）
- find_material_children(material_id): 递归构建合成树

对齐 AmiyaBot 插件 amiyabot-arknights-material-2_8/main.py
不集成 yituliu 数据库（AstrBot 无 peewee），recommend 恒返回空列表。
"""

from typing import List, Dict
from .game_data import ArknightsGameData


class MaterialData:
    """材料数据查询 — 对齐 AmiyaBot MaterialData

    用法:
        await MaterialData.init_materials()
        result = MaterialData.check_material("固源岩")
    """

    materials: List[str] = []

    @staticmethod
    async def init_materials():
        """初始化材料名称列表（从游戏数据构建）"""
        gd = ArknightsGameData()
        MaterialData.materials = list(gd.materials_map.keys())

    @classmethod
    def find_material_children(cls, material_id: str, parent_id: str = "") -> list:
        """递归查找材料的子材料（合成配方树）

        Args:
            material_id: 材料 ID
            parent_id:  父材料 ID，用于避免循环引用

        Returns:
            list of dict: 每个 child 包含 use_material_id, use_number,
                          material_name, material_icon, material_desc, rarity,
                          以及嵌套的 children
        """
        game_data = ArknightsGameData()
        children = []

        if material_id in game_data.materials_made:
            for item in game_data.materials_made[material_id]:
                child_mat = game_data.materials.get(item["use_material_id"], {})
                children.append(
                    {
                        **item,
                        **child_mat,
                        "children": (
                            cls.find_material_children(
                                item["use_material_id"], material_id
                            )
                            if item["use_material_id"] != parent_id
                            else []
                        ),
                    }
                )

        return children

    @classmethod
    def check_material(cls, name: str) -> dict | None:
        """根据材料名称查询完整信息

        Args:
            name: 材料中文名（如 "固源岩"）

        Returns:
            dict: {
                "name": str,          # 材料名
                "info": dict,         # 材料基础信息 (material_id, material_name, ...)
                "children": list,     # 合成子材料树（递归）
                "source": {           # 获取来源（按主线和活动分类）
                    "main": [{"code", "name", "rate"}, ...],
                    "act":  [{"code", "name", "rate"}, ...],
                },
                "recommend": list,    # 推荐关卡（始终为空，不集成 yituliu）
            }
            找不到材料时返回 None
        """
        game_data = ArknightsGameData()

        if name not in game_data.materials_map:
            return None

        material_id = game_data.materials_map[name]
        material = game_data.materials[material_id]

        result: dict = {
            "name": name,
            "info": material,
            "children": cls.find_material_children(material_id),
            "source": {"main": [], "act": []},
            "recommend": [],
        }

        # ── 构建来源（掉落关卡） ─────────────────────────
        if material_id in game_data.materials_source:
            source_data = game_data.materials_source[material_id]
            for code in source_data.keys():
                if code not in game_data.stages:
                    continue
                stage = game_data.stages[code]
                info = {
                    "code": stage["code"],
                    "name": stage["name"],
                    "rate": source_data[code]["source_rate"],
                }
                # 对齐 AmiyaBot 分类: stage_id 含 "main" 为主线，否则为活动
                if "main" in code:
                    result["source"]["main"].append(info)
                else:
                    result["source"]["act"].append(info)

        return result
