#!/bin/bash
set -e

echo "🔄 Updating pip..."
python3 -m pip install --upgrade pip setuptools wheel

echo "📦 Installing required packages..."
pip install --no-cache-dir -r requirements.txt

echo "📦 Installing google generativeai from GitHub..."
pip install --no-cache-dir git+https://github.com/google/generativeai-python.git@main

echo "🧹 Clearing pip cache..."
rm -rf ~/.cache/pip

# ==== Kiểm tra biến môi trường ====
for VAR in TOKEN GEMINI_API_KEY; do
  if [ -z "${!VAR}" ]; then
    echo "⚠️ ERROR: Biến môi trường $VAR chưa được set!"
    exit 1
  fi
done

export PORT=${PORT:-10000}
echo "🌐 Using PORT=$PORT"

echo "🤖 Starting Phoebe Xinh Đẹp bot..."
python3 chatbot.py
