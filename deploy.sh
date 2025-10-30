#!/bin/bash
set -e

echo "🚀 Deploying Phoebe Xinh Đẹp Bot..."

# ==== 1. Hiển thị version Python ====
PYTHON_BIN=$(command -v python3)
echo "🔧 Using Python binary: $PYTHON_BIN"
"$PYTHON_BIN" --version

# ==== 2. Cập nhật pip & setuptools ====
echo "🔄 Updating pip, setuptools, wheel..."
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

# ==== 3. Cài đặt dependencies + Google GenAI mới nhất ====
echo "📦 Installing dependencies..."
"$PYTHON_BIN" -m pip install -r requirements.txt
"$PYTHON_BIN" -m pip install --upgrade google-genai

# ==== 4. Chạy bot ====
echo "💫 Starting Phoebe..."
exec "$PYTHON_BIN" chatbot.py