#!/bin/bash
# 下载干员立绘图片到本地
# AmiyaBot 方式：从 ArknightsGameResource 拉取所有 portrait 图片
#
# 用法: bash scripts/download_portraits.sh [char_id...]
# 不带参数则下载常用干员立绘

set -e

PORTRAIT_DIR="$(dirname "$0")/../data/ArknightsGameResource/portrait"
BASE_URL="https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/portrait"

# 需要下载的干员列表（常用干员 + 用户查询过的）
DEFAULT_CHARS=(
    char_002_amiya char_103_angel char_102_texas char_202_demkni
    char_134_fang char_120_hibisc char_124_kroos char_240_lancet
    char_278_orchid char_285_medic2 char_291_glacus char_112_siege
    char_147_shining char_179_nightingale char_2013_skadi
    char_203_skyr char_230_savage char_235_jesica char_240_lancet
)

mkdir -p "$PORTRAIT_DIR"
CHARS=(${@:-${DEFAULT_CHARS[@]}})

for char_id in "${CHARS[@]}"; do
    for suffix in "" "_1" "_2"; do
        filename="${char_id}${suffix}.png"
        url="$BASE_URL/$filename"
        if timeout 15 curl -sL -o "$PORTRAIT_DIR/$filename" "$url" 2>/dev/null; then
            size=$(wc -c < "$PORTRAIT_DIR/$filename")
            if [ "$size" -gt 1000 ]; then
                echo "  OK: $filename ($size bytes)"
            else
                rm -f "$PORTRAIT_DIR/$filename"
            fi
        fi
    done
done

echo "Done. Portraits in $PORTRAIT_DIR"
