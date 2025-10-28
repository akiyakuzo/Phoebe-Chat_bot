#!/bin/bash
set -e

# ==== Chọn version Python từ biến môi trường hoặc mặc định 3.11.4 ====
PYTHON_VER=${PYTHON_VERSION:-3.11.4}
echo "🔧 Using Python version: $PYTHON_VER"

# ==== Cập nhật pip + setuptools + wheel ====
echo "🔄 Updating pip..."
python3 -m pip install --upgrade pip setuptools wheel

# ==== Cài các package từ requirements.txt ====
echo "📦 Installing required packages..."
pip install --no-cache-dir -r requirements.txt

# ==== Cài google generativeai từ GitHub ====
echo "📦 Installing google generativeai from GitHub..."
pip install --no-cache-dir git+https://github.com/google/generativeai-python.git@main

# ==== Xoá cache pip ====
echo "🧹 Clearing pip cache..."
rm -rf ~/.cache/pip

# ==== Kiểm tra biến môi trường bắt buộc ====
for VAR in TOKEN GEMINI_API_KEY; do
  if [ -z "${!VAR}" ]; then
    echo "⚠️ ERROR: Biến môi trường $VAR chưa được set!"
    exit 1
  fi
done

# ==== PORT mặc định 10000 nếu không có ====
export PORT=${PORT:-10000}
echo "🌐 Using PORT=$PORT"

# ==== Chạy bot ====
echo "🤖 Starting Phoebe Xinh Đẹp bot..."
python3 chatbot.py
