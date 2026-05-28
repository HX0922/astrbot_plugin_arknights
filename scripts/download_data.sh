#!/bin/bash
# 下载 ArknightsGameResource 核心 JSON 数据文件
# 
# 用法: bash scripts/download_data.sh
#
# 从 GitHub raw 下载 gamedata/excel/*.json 文件，
# 避免 clone 整个 5GB+ 仓库。

set -e

DATA_DIR="$(dirname "$0")/../data/ArknightsGameResource/gamedata/excel"
BASE_URL="https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/gamedata/excel"

FILES=(
    character_table.json
    item_table.json
    stage_table.json
    gacha_table.json
    skill_table.json
    char_patch_table.json
    skin_table.json
    enemy_handbook_table.json
    uniequip_table.json
)

mkdir -p "$DATA_DIR"

echo "Downloading Arknights game data..."
for f in "${FILES[@]}"; do
    echo -n "  $f ... "
    curl -sL "$BASE_URL/$f" -o "$DATA_DIR/$f"
    echo "$(wc -c < "$DATA_DIR/$f") bytes"
done

echo ""
echo "Done. Data directory: $DATA_DIR"
du -sh "$(dirname "$DATA_DIR")"
