# AstrBot Plugin: Arknights (明日方舟)

> 从 [AmiyaBot V6](https://github.com/AmiyaBot/Amiya-Bot) 迁移至 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 的明日方舟游戏数据查询插件。

> ⚠️ **插件开发中，尚未发布正式版本。**

## 功能

| 命令 | 说明 | 示例 |
|------|------|------|
| `/角色 <名称>` | 查询干员信息（星级/属性/天赋/技能） | `/角色 阿米娅` |
| `/公招 <标签...>` | 公开招募标签组合计算 | `/公招 狙击 输出 高级资深干员` |
| `/抽卡 [十连]` | 模拟标准寻访卡池 | `/抽卡 十连` |
| `/材料 <名称>` | 查询材料/物品信息 | `/材料 固源岩` |
| `/关卡 <编号>` | 查询关卡掉落和消耗 | `/关卡 1-7` |
| `/arkhelp` | 显示插件帮助 | `/arkhelp` |

## 项目结构

```
astrbot_plugin_arknights/
├── main.py                 # Star 插件入口
├── metadata.yaml           # AstrBot 插件元数据
├── src/
│   ├── game_data.py        # 数据加载层（单例，延迟加载）
│   ├── operator.py         # 干员信息格式化
│   ├── recruit.py          # 公开招募计算
│   ├── gacha.py            # 卡池模拟
│   ├── material.py         # 材料搜索
│   └── stage.py            # 关卡查询
├── tests/                  # 单元测试
├── data/                   # 游戏数据（JSON）
└── scripts/                # 工具脚本
```

## 开发

### 环境

- Python >= 3.12
- Playwright + Chromium（首次加载插件时自动安装）

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e /path/to/AstrBot
```

### 手动安装 Chromium

如果自动安装失败，可手动执行：

```bash
# Windows / macOS
playwright install chromium

# Linux
playwright install --with-deps chromium
```

### 运行测试

```bash
pytest tests/ -v
```

## 声明

本项目仅移植了 AmiyaBot 的基础游戏信息查询功能（干员、公招、抽卡、材料、关卡等），
**不包含**兔兔的角色设定、对话人格以及 AmiyaBot 丰富的插件生态。
如果你想体验完整的兔兔，请前往 [amiyabot.com](https://www.amiyabot.com/) 支持原版。

在此基础上，我们计划逐步加入明日方舟游戏内容的 RAG 检索、机制解析、数值计算等功能，敬请期待。

## 数据源

游戏数据来自 [ArknightsGameResource](https://github.com/yuanyan3060/ArknightsGameResource)。

## 许可

本项目代码部分基于 [AmiyaBot](https://github.com/AmiyaBot/Amiya-Bot) (MIT) 的架构思想重写，采用 **MIT License**。

游戏数据来自 [ArknightsGameResource](https://github.com/yuanyan3060/ArknightsGameResource)，遵循其原始许可。

本插件目标平台 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 采用 AGPL-3.0。合并分发时请遵守相应条款。

## 致谢

- [AmiyaBot](https://github.com/AmiyaBot/Amiya-Bot) — 原始明日方舟 Bot 实现
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) — 目标平台框架
- [ArknightsGameResource](https://github.com/yuanyan3060/ArknightsGameResource) — 游戏数据维护
