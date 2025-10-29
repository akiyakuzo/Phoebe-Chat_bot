#!/bin/bash
set -e

# ==== Chọn version Python từ biến môi trường hoặc mặc định 3.13 ====
PYTHON_VER=${PYTHON_VERSION:-3.13}
echo "🔧 Using Python version: $PYTHON_VER"

# ==== Cập nhật pip + setuptools + wheel ====
echo "🔄 Updating pip..."
python3 -m pip install --upgrade pip setuptools wheel

# ==== Cài các package từ requirements.txt ====
if [ -f requirements.txt ]; then
  echo "📦 Installing required packages..."
  pip install --no-cache-dir -r requirements.txt
else
  echo "⚠️ Không tìm thấy requirements.txt, bỏ qua bước này."
fi

# ==== Cài google-genai (phiên bản mới nhất, tương thích script Phoebe) ====
echo "📦 Installing google-genai (latest stable)..."
pip install --no-cache-dir "google-genai>=1.46.0"

# ==== Xóa cache pip để giảm dung lượng ====
echo "🧹 Clearing pip cache..."
rm -rf ~/.cache/pip

# ==== Kiểm tra biến môi trường bắt buộc ====
for VAR in TOKEN GEMINI_API_KEY; do
  if [ -z "${!VAR}" ]; then
    echo "❌ ERROR: Biến môi trường $VAR chưa được set!"
    exit 1
  fi
done

# ==== PORT mặc định 10000 nếu không có ====
export PORT=${PORT:-10000}
echo "🌐 Using PORT=$PORT"

# ==== Chạy bot ====
echo "🤖 Starting Phoebe Xinh Đẹp bot..."
exec python3 chatbot.py