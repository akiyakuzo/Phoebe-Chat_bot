#!/bin/bash
set -e

echo "🚀 Deploying Phoebe Xinh Đẹp Bot..."

# ==== 1. Xác định Python binary ====
PYTHON_BIN=$(command -v python3)
echo "🔧 Using Python binary: $PYTHON_BIN"
"$PYTHON_BIN" --version

# --- Nâng cấp pip (có thể bỏ qua nếu môi trường luôn mới) ---
echo "🔄 Upgrading pip, setuptools, wheel..."
# Chỉ nâng cấp nếu cần thiết, tránh tốn thời gian vô ích.
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel --no-cache-dir

# ==== 2. Gỡ các version cũ của Google GenAI (NÊN GIỮ LẠI) ====
# Giữ lại bước này giúp khắc phục triệt để lỗi xung đột version nếu có.
echo "🧹 Removing old Google GenAI versions..."
"$PYTHON_BIN" -m pip uninstall -y google-genai google-generativeai || true

# ==== 3. Cài TẤT CẢ dependencies (Đã gộp bước cài google-generativeai riêng) ====
echo "📦 Installing all dependencies from requirements.txt..."
# Dùng lệnh install thông thường, nếu gói đã có sẽ bỏ qua (nhanh hơn upgrade)
"$PYTHON_BIN" -m pip install -r requirements.txt --no-cache-dir

# ==== 4. Xoá cache pip (Phòng ngừa lỗi import, nên giữ lại) ====
echo "🧹 Clearing pip cache..."
"$PYTHON_BIN" -m pip cache purge || true

# ==== 5. Kiểm tra version SDK ====
echo "🔍 Checking google-generativeai version..."
"$PYTHON_BIN" -c "import google.generativeai as genai; print('Google GenerativeAI version:', genai.__version__)"

# ==== 6. Chạy bot ====
echo "💫 Starting Phoebe..."
exec "$PYTHON_BIN" chatbot.py