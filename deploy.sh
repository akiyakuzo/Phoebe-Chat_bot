#!/bin/bash
set -e

# ==== Trap để in thông báo khi script exit ====
trap 'echo "❌ Bot exited with code $?."' EXIT

# ==== Chọn version Python từ biến môi trường hoặc mặc định ====
PYTHON_VER=${PYTHON_VERSION:-3.13}
echo "🔧 Using Python version: $PYTHON_VER"

# ==== Kiểm tra Python ====
if ! command -v python$PYTHON_VER &>/dev/null; then
  echo "❌ Python $PYTHON_VER không được cài đặt!"
  exit 1
fi

PYTHON_BIN=python$PYTHON_VER

# ==== Cập nhật pip + setuptools + wheel ====
echo "🔄 Updating pip..."
$PYTHON_BIN -m pip install --upgrade pip setuptools wheel

# ==== Cài đặt dependencies từ requirements.txt nếu có ====
if [ -f requirements.txt ]; then
  echo "📦 Installing dependencies..."
  $PYTHON_BIN -m pip install --no-cache-dir -r requirements.txt || echo "⚠️ Có lỗi khi cài dependencies."
else
  echo "⚠️ Không tìm thấy file requirements.txt — bỏ qua bước cài đặt gói."
fi

# ==== Xoá cache pip để giảm dung lượng ====
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

# ==== Hàm restart bot nếu crash ====
function start_bot {
  while true; do
    echo "🤖 Starting Phoebe Xinh Đẹp bot..."
    $PYTHON_BIN -u chatbot.py
    echo "⚠️ Bot crashed. Restarting in 5s..."
    sleep 5
  done
}

start_bot