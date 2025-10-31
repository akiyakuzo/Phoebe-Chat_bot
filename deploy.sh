#!/bin/bash
set -e

echo "🚀 Deploying Phoebe Xinh Đẹp Bot with Auto-Retry..."

PYTHON_BIN=$(command -v python3)
echo "🔧 Using Python binary: $PYTHON_BIN"
"$PYTHON_BIN" --version

echo "🔄 Upgrading pip, setuptools, wheel..."
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

echo "🧹 Clearing pip cache..."
"$PYTHON_BIN" -m pip cache purge || true

TARGET_VERSION="0.8.0"
MAX_RETRIES=3
RETRY=0
SUCCESS=false

while [ $RETRY -lt $MAX_RETRIES ]; do
    echo "⚡ Attempt $(($RETRY + 1)) to install Google GenerativeAI v$TARGET_VERSION..."
    "$PYTHON_BIN" -m pip uninstall google-generativeai -y || true
    "$PYTHON_BIN" -m pip install google-generativeai==$TARGET_VERSION --no-cache-dir

    INSTALLED_VERSION=$("$PYTHON_BIN" -c "import google.generativeai as genai; print(getattr(genai, '__version__', 'Unknown'))")
    echo "🔍 Installed version: $INSTALLED_VERSION"

    if [ "$INSTALLED_VERSION" == "$TARGET_VERSION" ]; then
        SUCCESS=true
        break
    else
        echo "⚠️ Version mismatch, retrying..."
        RETRY=$(($RETRY + 1))
    fi
done

if [ "$SUCCESS" != true ]; then
    echo "❌ Failed to install correct Google GenerativeAI version after $MAX_RETRIES attempts. Exiting."
    exit 1
fi

echo "📦 Installing other dependencies from requirements.txt..."
"$PYTHON_BIN" -m pip install --upgrade -r requirements.txt

echo "💫 Starting Phoebe..."
exec "$PYTHON_BIN" chatbot.py