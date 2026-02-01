#!/bin/bash

# GitHub自动同步脚本
# 定期拉取远程更新并推送本地更改

cd /root/clawd

# 设置Git配置
git config user.email "web3traval@users.noreply.github.com"
git config user.name "web3Traval"

# 从环境变量获取GitHub token
GITHUB_TOKEN="${GITHUB_TOKEN:-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}"

# 设置远程URL（带token）
REMOTE_URL="https://${GITHUB_TOKEN}@github.com/erniucb/clawd-config.git"
git remote set-url origin "$REMOTE_URL"

# 拉取远程更新
echo "[$(date)] 拉取远程更新..."
git pull origin master --no-edit || true

# 检查是否有本地更改
if ! git diff-index --quiet HEAD --; then
    echo "[$(date)] 检测到本地更改，准备提交..."
    git add -A
    git commit -m "Auto sync: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$(date)] 推送到远程..."
    git push origin master
else
    echo "[$(date)] 没有本地更改，跳过提交"
fi

echo "[$(date)] 同步完成"
