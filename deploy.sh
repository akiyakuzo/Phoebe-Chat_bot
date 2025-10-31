#!/bin/bash
set -e

echo "🚀 Deploying Phoebe Xinh Đẹp Bot..."

# ==== 1. Xác định Python binary ====
PYTHON_BIN=$(command -v python3)
echo "🔧 Using Python binary: $PYTHON_BIN"
"$PYTHON_BIN" --version

# ==== 2. Cập nhật pip, setuptools, wheel ====
echo "🔄 Upgrading pip, setuptools, wheel..."
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel --no-cache-dir

# ==== 3. Gỡ các version cũ của Google GenAI (nếu có) ====
echo "🧹 Removing old Google GenAI versions..."
"$PYTHON_BIN" -m pip uninstall -y google-genai google-generativeai || true

# ==== 4. Cài SDK mới 0.8.0 ====
echo "📦 Installing google-generativeai 0.8.0..."
"$PYTHON_BIN" -m pip install google-generativeai==0.8.0 --no-cache-dir

# ==== 5. Cài các dependencies khác từ requirements.txt ====
echo "📦 Installing other dependencies..."
"$PYTHON_BIN" -m pip install --upgrade -r requirements.txt --no-cache-dir

# ==== 6. Xoá cache pip (phòng ngừa lỗi import) ====
echo "🧹 Clearing pip cache..."
"$PYTHON_BIN" -m pip cache purge || true

# ==== 7. Kiểm tra version SDK ====
echo "🔍 Checking google-generativeai version..."
"$PYTHON_BIN" -c "import google.generativeai as genai; print('Google GenerativeAI version:', genai.__version__)"

# ==== 8. Chạy bot ====
echo "💫 Starting Phoebe..."
exec "$PYTHON_BIN" chatbot.py