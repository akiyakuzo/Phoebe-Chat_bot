#!/bin/bash
set -e

echo "🚀 Deploying Phoebe Xinh Đẹp Bot..."

# ==== 1. Hiển thị version Python ====
PYTHON_BIN=$(command -v python3)
echo "🔧 Using Python binary: $PYTHON_BIN"
"$PYTHON_BIN" --version

# ==== 2. Cập nhật pip & setuptools ====
echo "🔄 Updating pip..."
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

# ==== 3. Cài đặt các thư viện từ requirements.txt ====
echo "📦 Installing dependencies..."
"$PYTHON_BIN" -m pip install -r requirements.txt

# ==== 4. Chạy bot ====
echo "💫 Starting Phoebe..."
exec python3 chatbot.py