# AstrBot Plugin: Arknights (明日方舟)

> 从 [AmiyaBot V6](https://github.com/AmiyaBot/Amiya-Bot) 迁移至 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 的明日方舟游戏数据查询插件。

## 功能

| 命令 | 说明 | 示例 |
|------|------|------|
| `/角色 <名称>` | 查询干员信息（星级/属性/天赋/技能） | `/角色 阿米娅` |
| `/公招 <标签...>` | 公开招募标签组合计算 | `/公招 狙击 输出 高级资深干员` |
| `/抽卡 [十连]` | 模拟标准寻访卡池 | `/抽卡 十连` |
| `/材料 <名称>` | 查询材料/物品信息 | `/材料 固源岩` |
| `/关卡 <编号>` | 查询关卡掉落和消耗 | `/关卡 1-7` |
| `/arkhelp` | 显示插件帮助 | `/arkhelp` |

## 安装

### 1. 获取插件

```bash
git clone https://github.com/HX0922/astrbot_plugin_arknights.git
```

### 2. 下载游戏数据

```bash
# 方式 A: 运行脚本（推荐，约 53MB）
bash scripts/download_data.sh

# 方式 B: 手动 clone 完整数据仓库（约 5GB+）
git submodule add --depth 1 https://github.com/yuanyan3060/ArknightsGameResource.git data/ArknightsGameResource
```

### 3. 加载到 AstrBot

将插件目录复制或软链接到 AstrBot 的插件目录，通过 WebUI 启用即可。

```bash
# 示例
ln -s /path/to/astrbot_plugin_arknights /path/to/AstrBot/data/plugins/arknights
```

## 开发

### 环境

- Python >= 3.12
- uv（推荐）或 pip

```bash
# 创建虚拟环境
uv venv --python 3.12
source .venv/bin/activate

# 安装 AstrBot（开发模式）
uv pip install -e /path/to/AstrBot

# 国内用户换源
pip install --proxy "" -i https://pypi.tuna.tsinghua.edu.cn/simple -e /path/to/AstrBot
```

### 运行测试

```bash
pytest tests/ -v
```

### 项目结构

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

## 数据源

游戏数据来自 [ArknightsGameResource](https://github.com/yuanyan3060/ArknightsGameResource)，使用 `scripts/download_data.sh` 从 GitHub Raw 下载核心 JSON 文件，无需 clone 完整仓库。

### 更新数据

```bash
bash scripts/download_data.sh
```

## 许可

本项目代码部分基于 [AmiyaBot](https://github.com/AmiyaBot/Amiya-Bot) (MIT) 的架构思想重写，采用 **MIT License**。

游戏数据来自 [ArknightsGameResource](https://github.com/yuanyan3060/ArknightsGameResource)，遵循其原始许可。

本插件目标平台 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 采用 AGPL-3.0。合并分发时请遵守相应条款。

## 致谢

- [AmiyaBot](https://github.com/AmiyaBot/Amiya-Bot) — 原始明日方舟 Bot 实现
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) — 目标平台框架
- [ArknightsGameResource](https://github.com/yuanyan3060/ArknightsGameResource) — 游戏数据维护
