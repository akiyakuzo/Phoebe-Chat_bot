#!/bin/bash
set -e

echo "🚀 Deploying Phoebe Xinh Đẹp Bot..."

# ==== 1. Xác định Python binary ====
PYTHON_BIN=$(command -v python3)
echo "🔧 Using Python binary: $PYTHON_BIN"
"$PYTHON_BIN" --version

# ==== 2. Cập nhật pip, setuptools, wheel ====
echo "🔄 Upgrading pip, setuptools, wheel..."
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

# ==== 3. Cài đặt dependencies từ requirements.txt ====
echo "📦 Installing dependencies..."
"$PYTHON_BIN" -m pip install --upgrade -r requirements.txt

# ==== 4. Xoá cache cũ (Render đôi khi còn giữ các module cũ) ====
echo "🧹 Clearing pip cache..."
"$PYTHON_BIN" -m pip cache purge || true

# ==== 5. Kiểm tra version google-generativeai ====
echo "🔍 Checking google-generativeai version..."
"$PYTHON_BIN" -c "import google.generativeai as genai; print('Google GenerativeAI version:', genai.__version__)"

# ==== 6. Chạy bot ====
echo "💫 Starting Phoebe..."
exec "$PYTHON_BIN" chatbot.py