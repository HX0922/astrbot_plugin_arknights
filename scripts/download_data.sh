#!/bin/bash
# 下载 ArknightsGameResource 核心 JSON 数据文件
# 
# 用法: bash scripts/download_data.sh
#
# 从 GitHub raw 下载所有必需的数据文件

set -e

DATA_DIR="$(dirname "$0")/../data/ArknightsGameResource"
BASE_URL="https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main"

# Excel 数据文件
EXCEL_FILES=(
    character_table.json
    item_table.json
    stage_table.json
    gacha_table.json
    skill_table.json
    char_patch_table.json
    skin_table.json
    enemy_handbook_table.json
    uniequip_table.json
    building_data.json
    favor_table.json
    handbook_info_table.json
    charword_table.json
    token_table.json
    range_table.json
    char_meta_table.json
    handbook_team_table.json
    battle_equip_table.json
)

EXCEL_DIR="$DATA_DIR/gamedata/excel"
mkdir -p "$EXCEL_DIR"

echo "Downloading excel data..."
for f in "${EXCEL_FILES[@]}"; do
    echo -n "  $f ... "
    curl -sL "$BASE_URL/gamedata/excel/$f" -o "$EXCEL_DIR/$f" 2>/dev/null && echo "$(wc -c < "$EXCEL_DIR/$f") bytes" || echo "SKIPPED (not found)"
done

# Enemy database
ENEMY_DIR="$DATA_DIR/gamedata/levels/enemydata"
mkdir -p "$ENEMY_DIR"
echo -n "  levels/enemydata/enemy_database.json ... "
curl -sL "$BASE_URL/gamedata/levels/enemydata/enemy_database.json" -o "$ENEMY_DIR/enemy_database.json" 2>/dev/null && echo "$(wc -c < "$ENEMY_DIR/enemy_database.json") bytes" || echo "SKIPPED"

echo ""
echo "Done. Data directory: $DATA_DIR"
du -sh "$DATA_DIR"
