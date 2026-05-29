"""
ArknightsGameResource 资源管理

插件启动时检查版本，有更新则自动拉取最新的 JSON 数据文件。
图片资源按需下载（首次查询干员时下载立绘）。

目录结构:
    data/ArknightsGameResource/
    ├── gamedata/excel/   # JSON 数据文件
    ├── portrait/         # 干员立绘
    ├── item/             # 物品图标
    ├── skill/            # 技能图标
    ├── avatar/           # 头像
    └── _version.txt      # 数据版本 commit SHA
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main"
API_URL = "https://api.github.com/repos/yuanyan3060/ArknightsGameResource/commits/main"

# 核心 JSON 文件列表
DATA_FILES = [
    "gamedata/excel/character_table.json",
    "gamedata/excel/item_table.json",
    "gamedata/excel/stage_table.json",
    "gamedata/excel/gacha_table.json",
    "gamedata/excel/skill_table.json",
    "gamedata/excel/char_patch_table.json",
    "gamedata/excel/skin_table.json",
    "gamedata/excel/enemy_handbook_table.json",
    "gamedata/excel/uniequip_table.json",
    "gamedata/excel/building_data.json",
]

# 每次查询自动检查间隔
CHECK_INTERVAL = timedelta(hours=1)


def get_resource_dir() -> Path:
    """获取资源根目录"""
    return Path(__file__).resolve().parent.parent / "data" / "ArknightsGameResource"


def get_version_file() -> Path:
    return get_resource_dir() / "_version.txt"


def read_local_version() -> str:
    """读取本地数据版本"""
    vf = get_version_file()
    if vf.exists():
        return vf.read_text().strip()
    return ""


def write_local_version(sha: str):
    get_version_file().write_text(sha)


def fetch_remote_version() -> str | None:
    """从 GitHub API 获取最新 commit SHA"""
    import urllib.request
    try:
        req = urllib.request.Request(API_URL, headers={
            "User-Agent": "AstrBot-Arknights-Plugin",
            "Accept": "application/vnd.github.v3+json",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("sha", "")
    except Exception:
        return None


def needs_update() -> bool:
    """检查是否需要更新数据"""
    vf = get_version_file()
    if not vf.exists():
        return True
    last_check = datetime.fromtimestamp(vf.stat().st_mtime)
    if datetime.now() - last_check < CHECK_INTERVAL:
        return False
    remote = fetch_remote_version()
    if remote and remote != read_local_version():
        return True
    return False


def download_data_files():
    """下载所有 JSON 数据文件"""
    import urllib.request

    root = get_resource_dir()
    for f in DATA_FILES:
        dst = root / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        url = f"{BASE_URL}/{f}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AstrBot-Arknights"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                dst.write_bytes(resp.read())
        except Exception as e:
            print(f"[Arknights] 下载失败 {f}: {e}")


def download_portrait(char_id: str) -> str | None:
    """按需下载干员立绘，返回本地路径"""
    root = get_resource_dir()
    portrait_dir = root / "portrait"
    portrait_dir.mkdir(parents=True, exist_ok=True)

    import urllib.request

    for suffix in ["_2", "_1", ""]:
        filename = f"{char_id}{suffix}.png"
        dst = portrait_dir / filename
        if dst.exists() and dst.stat().st_size > 1000:
            return str(dst)

        url = f"{BASE_URL}/portrait/{filename}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AstrBot-Arknights"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                if len(data) > 1000:
                    dst.write_bytes(data)
                    return str(dst)
        except Exception:
            continue
    return None


def initialize_resource():
    """初始化/更新游戏资源（插件启动时调用）"""
    root = get_resource_dir()
    root.mkdir(parents=True, exist_ok=True)

    # 检查数据文件是否存在
    char_table = root / "gamedata" / "excel" / "character_table.json"
    if not char_table.exists():
        print("[Arknights] 首次运行，下载游戏数据...")
        download_data_files()
        remote = fetch_remote_version()
        if remote:
            write_local_version(remote)
        print("[Arknights] 数据下载完成")
        return

    # 检查更新
    if needs_update():
        print("[Arknights] 检测到数据更新，正在下载...")
        download_data_files()
        remote = fetch_remote_version()
        if remote:
            write_local_version(remote)
        print("[Arknights] 数据更新完成")
