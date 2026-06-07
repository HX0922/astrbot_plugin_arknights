"""
干员数据组装 — 严格对齐 AmiyaBot operatorData.py

OperatorData 类提供:
- get_operator_detail() → 渲染用完整数据
- get_level_up_cost() → 精英化/专精材料
- get_skills_detail() → 技能详情
- find_operator_module() → 模组信息
"""

import copy
from typing import Optional, Dict, List, Tuple

from .game_data import ArknightsGameData, ArknightsGameResource
from .operator_model import Operator, integer, snake_case_to_pascal_case, parse_template
from .operator_core import OperatorSearchInfo


class OperatorData:
    """干员数据组装 — 严格对齐 AmiyaBot OperatorData"""

    @classmethod
    async def get_operator_detail(
        cls, info: OperatorSearchInfo
    ) -> Tuple[Optional[dict], Optional[dict]]:
        """获取干员完整详情数据

        Returns:
            (operator_info, tokens) — 与 AmiyaBot operatorData.get_operator_detail() 一致
        """
        data = ArknightsGameData()
        operators = data.operators

        if not info.name or info.name not in operators:
            return None, None

        operator = operators[info.name]

        # 真名（AmiyaBot 从远程获取，这里跳过）
        real_name = []

        # detail: (属性, 信赖加成)
        detail, trust = operator.detail()

        # 模组
        modules_raw = operator.modules()
        module_attrs = []
        if modules_raw:
            for module in modules_raw:
                module_attr = {}
                if module.get("detail"):
                    phases = module["detail"].get("phases", [])
                    if phases:
                        attrs = phases[-1].get("attributeBlackboard", [])
                        for attr in attrs:
                            key = snake_case_to_pascal_case(attr.get("key", ""))
                            module_attr[key] = integer(attr.get("value", 0))

                module_attrs.append({**module, "attrs": module_attr})

        # 技能
        skills, skills_id, skills_cost, skills_desc = operator.skills()

        # 皮肤
        skins = operator.skins()

        # info 字段列表（与 AmiyaBot operatorData 中的 infos 列表完全一致）
        infos = [
            "id",
            "cv",
            "type",
            "tags",
            "range",
            "rarity",
            "number",
            "name",
            "en_name",
            "wiki_name",
            "index_name",
            "origin_name",
            "classes",
            "classes_sub",
            "classes_code",
            "race",
            "drawer",
            "team",
            "group",
            "nation",
            "birthday",
            "profile",
            "impression",
            "limit",
            "unavailable",
            "potential_item",
            "is_recruit",
            "is_sp",
        ]

        operator_info = {
            "info": {
                "real_name": real_name,
                **{n: getattr(operator, n, "") for n in infos},
            },
            "skin": "",
            "trust": trust,
            "detail": detail,
            "modules": module_attrs,
            "talents": operator.talents(),
            "potential": operator.potential(),
            "building_skills": operator.building_skills(),
            "skill_list": skills,
            "skills_cost": skills_cost,
            "skills_desc": skills_desc,
        }

        # skin 路径
        if skins:
            operator_info["skin"] = ArknightsGameResource.get_skin_file(skins[0], encode_url=True)

        tokens = {
            "id": operator.id,
            "name": operator.name,
            "tokens": operator.tokens(),
        }

        return operator_info, tokens

    @classmethod
    async def get_level_up_cost(
        cls, info: OperatorSearchInfo
    ) -> Optional[dict]:
        """获取精英化/专精材料 — 对齐 AmiyaBot get_level_up_cost()"""
        data = ArknightsGameData()
        operators = data.operators
        materials = data.materials

        if not info.name or info.name not in operators:
            return None

        operator = operators[info.name]
        evolve_costs = operator.evolve_costs()

        # 精英化材料
        evolve_costs_list: Dict[int, list] = {}
        for item in evolve_costs:
            mat_id = item.get("use_material_id", "")
            material = materials.get(mat_id, {})
            level = item.get("evolve_level", 0)

            evolve_costs_list.setdefault(level, []).append({
                "material_name": material.get("material_name", ""),
                "material_icon": material.get("material_icon", ""),
                "use_number": item.get("use_number", 0),
            })

        # 技能专精材料
        skills, skills_id, skills_cost, skills_desc = operator.skills()
        skills_cost_list: Dict[str, Dict[int, list]] = {}

        for item in skills_cost:
            mat_id = item.get("use_material_id", "")
            material = materials.get(mat_id, {})
            skill_no = item.get("skill_no") or "common"

            skills_cost_list.setdefault(skill_no, {}).setdefault(
                item.get("level", 0), []
            ).append({
                "material_name": material.get("material_name", ""),
                "material_icon": material.get("material_icon", ""),
                "use_number": item.get("use_number", 0),
            })

        # 皮肤
        skins = operator.skins()
        skin = ""
        if skins:
            skin = ArknightsGameResource.get_skin_file(
                skins[1] if len(skins) > 1 else skins[0], encode_url=True
            )

        return {
            "skin": skin,
            "evolve_costs": evolve_costs_list,
            "skills": skills,
            "skills_cost": skills_cost_list,
        }

    @classmethod
    async def get_skills_detail(
        cls, info: OperatorSearchInfo
    ) -> Optional[dict]:
        """获取技能详情"""
        operators = ArknightsGameData().operators
        if not info.name or info.name not in operators:
            return None

        operator = operators[info.name]
        skills, skills_id, skills_cost, skills_desc = operator.skills()

        return {"skills": skills, "skills_desc": skills_desc}

    @classmethod
    def find_operator_module(
        cls, info: OperatorSearchInfo, is_story: bool = False
    ) -> Optional[list]:
        """查找干员模组 — 对齐 AmiyaBot find_operator_module()"""
        data = ArknightsGameData()
        operators = data.operators
        materials = data.materials

        if not info.name or info.name not in operators:
            return None

        operator = operators[info.name]
        modules = copy.deepcopy(operator.modules())

        if not modules:
            return None

        if is_story:
            return cls.find_operator_module_story(modules)

        # 解析模组的 trait 和 talent 数据
        def parse_trait_data(data):
            if data is None:
                return
            for candidate in data:
                blackboard = candidate.get("blackboard", [])
                if candidate.get("additionalDescription"):
                    candidate["additionalDescription"] = parse_template(
                        blackboard, candidate["additionalDescription"]
                    )
                if candidate.get("overrideDescripton"):
                    candidate["overrideDescripton"] = parse_template(
                        blackboard, candidate["overrideDescripton"]
                    )

        def parse_talent_data(data):
            if data is None:
                return
            for candidate in data:
                blackboard = candidate.get("blackboard", [])
                if candidate.get("upgradeDescription"):
                    candidate["upgradeDescription"] = parse_template(
                        blackboard, candidate["upgradeDescription"]
                    )

        for item in modules:
            # 解析材料消耗
            if item.get("itemCost"):
                for lvl, item_cost in item["itemCost"].items():
                    for i, cost in enumerate(item_cost):
                        material = materials.get(cost.get("id", ""), {})
                        item_cost[i] = {
                            **cost,
                            "info": {
                                "material_name": material.get("material_name", ""),
                                "material_icon": material.get("material_icon", ""),
                            },
                        }

            # 解析模组详情
            if item.get("detail"):
                for stage in item["detail"].get("phases", []):
                    for part in stage.get("parts", []):
                        parse_trait_data(
                            part.get("overrideTraitDataBundle", {}).get("candidates")
                        )
                        parse_talent_data(
                            part.get("addOrOverrideTalentDataBundle", {}).get("candidates")
                        )

        return modules

    @staticmethod
    def find_operator_module_story(modules: list) -> str:
        text = ""
        for item in modules:
            text += f"\n\n## {item.get('uniEquipName', '')}\n\n"
            text += item.get("uniEquipDesc", "").replace("\n", "<br>")
        return text
