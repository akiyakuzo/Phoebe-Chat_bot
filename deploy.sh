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

# ==== 4. Kiểm tra version google-genai ====
echo "🔍 Checking google-genai version..."
"$PYTHON_BIN" -c "import google.genai; print('Google GenAI version:', google.genai.__version__)"

# ==== 5. Chạy bot ====
echo "💫 Starting Phoebe..."
"$PYTHON_BIN" chatbot.py
