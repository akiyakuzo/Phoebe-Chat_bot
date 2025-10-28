#!/bin/bash
# ============================================
# 🚀 Script Deploy Bot Phoebe Xinh Đẹp v6.4
# Dành cho Render + Python 3.13
# ============================================

# ==== 1️⃣ Cập nhật pip ====
echo "🔄 Updating pip..."
python -m pip install --upgrade pip setuptools wheel

# ==== 2️⃣ Cài các package cần thiết ====
echo "📦 Installing required packages..."
pip install --no-cache-dir -r requirements.txt

# ==== 3️⃣ Xoá cache pip cũ ====
echo "🧹 Clearing pip cache..."
rm -rf ~/.cache/pip

# ==== 4️⃣ Kiểm tra biến môi trường quan trọng ====
if [ -z "$TOKEN" ]; then
  echo "⚠️ ERROR: Biến môi trường TOKEN chưa được set!"
  exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
  echo "⚠️ ERROR: Biến môi trường GEMINI_API_KEY chưa được set!"
  exit 1
fi

# ==== 5️⃣ Lấy PORT từ Render, default 10000 nếu không có ====
export PORT=${PORT:-10000}
echo "🌐 Using PORT=$PORT"

# ==== 6️⃣ Chạy bot ====
echo "🤖 Starting Phoebe Xinh Đẹp bot..."
python chatbot.py
