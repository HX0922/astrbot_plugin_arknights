#!/bin/bash
# 同步插件到 AstrBot 插件目录
# 用法: bash sync_to_astrbot.sh

SRC="/mnt/d/Documents/projects/astrbot_arknights"
DST="/mnt/c/Users/HX/.astrbot/data/plugins/astrbot_plugin_arknights"

# Clean destination first to avoid nested copies
rm -rf "$DST"
mkdir -p "$DST"

rsync -a \
    --exclude='.venv' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    "$SRC/" "$DST/"

echo "[$(date '+%H:%M:%S')] Synced to AstrBot plugins"
