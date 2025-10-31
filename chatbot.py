# ==== PATCH PYTHON 3.11 ====
import sys, types
# Vá lỗi audioop trên môi trường Render/Linux, thường gặp khi dùng discord.py
sys.modules['audioop'] = types.ModuleType('audioop')

# ========== IMPORTS ==========
import os
import json
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime
import google.generativeai as genai

# ========== CONFIG GOOGLE GENERATIVE AI (Gemini 2.0 Flash) ==========
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu GEMINI_API_KEY!")

# Khởi tạo Client: Đây là cách chuẩn cho SDK 0.8.0. Cần phải cố gắng khởi tạo thành công.
try:
    # 1. Khởi tạo Client: Cách chuẩn cho SDK 0.8.0+
    client = genai.Client(api_key=GEMINI_API_KEY)
except AttributeError as e:
    # 2. Xử lý lỗi nếu genai.Client không tồn tại (lỗi môi trường/cache)
    print("🚨 LỖI NGHIÊM TRỌNG: genai.Client không tồn tại. Đã cài 0.8.0 chưa?")
    raise RuntimeError(f"Lỗi khởi tạo Gemini Client: {e}. Vui lòng kiểm tra lại quá trình cài đặt SDK (Sử dụng --no-cache-dir)")

MODEL_NAME = "gemini-2.0-flash" 

# ========== CONFIG BOT ==========
BOT_NAME = "Fibi Béll 💖"
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
HISTORY_LIMIT = 20
SESSIONS_FILE = "sessions.json"
flirt_enable = False
active_chats = {}
TYPING_SPEED = 0.02 # Độ trễ (giây) giữa mỗi ký tự

# ... (PHOBE_SAFE_INSTRUCTION, PROMPTS, DISCORD CONFIG, SESSION SYSTEM giữ nguyên) ...

# PHOBE_SAFE_INSTRUCTION, PHOBE_FLIRT_INSTRUCTION, PHOBE_COMFORT_INSTRUCTION
# PHOBE_BASE_PROMPT, PHOBE_LORE_PROMPT
# DISCORD CONFIG
# SESSION SYSTEM
# ... (Giữ nguyên từ code trước đó) ...

# ========== ASK GEMINI STREAM (Sử dụng đối tượng Client) ==========
async def ask_gemini_stream(user_id: str, user_input: str):
    session = get_or_create_chat(user_id)
    history = session["history"]

    user_input = user_input.strip()
    if not user_input:
        yield "⚠️ Không nhận được câu hỏi, anh thử lại nhé!"
        return

    user_input_cleaned = user_input.encode("utf-8", errors="ignore").decode()
    if not user_input_cleaned:
        yield "⚠️ Nội dung có ký tự lạ, em không đọc được. Anh viết lại đơn giản hơn nhé!"
        return

    if len(history) > HISTORY_LIMIT + 2:
        print(f"⚠️ Reset history user {user_id}")
        last_message = user_input_cleaned
        session["history"] = history[:2] 
        history = session["history"]
        user_input_to_use = last_message
    else:
        user_input_to_use = user_input_cleaned

    lower_input = user_input_to_use.lower()
    if any(w in lower_input for w in ["buồn", "mệt", "chán", "stress", "tệ quá"]):
        instruction = PHOBE_COMFORT_INSTRUCTION
    elif flirt_enable:
        instruction = PHOBE_FLIRT_INSTRUCTION
    else:
        instruction = PHOBE_SAFE_INSTRUCTION

    final_input_content = f"{user_input_to_use}\n\n[PHONG CÁCH TRẢ LỜI HIỆN TẠI: {instruction}]"
    contents_to_send = history + [{"role": "user", "content": final_input_content}]
    full_answer = ""

    try:
        # ✅ SỬ DỤNG client.generate_content_stream: Cách gọi chuẩn cho 0.8.0
        response_stream = await asyncio.to_thread(
            lambda: client.models.generate_content_stream( # Dùng client.models cho SDK 0.8.0 (để tránh nhầm lẫn)
                model=MODEL_NAME,
                contents=contents_to_send,
                temperature=0.8
            )
        )
        for chunk in response_stream:
            if chunk.text:
                text = chunk.text
                full_answer += text
                yield text
    except Exception as e:
        # Nếu đã là 0.8.0 mà vẫn lỗi này, nó là lỗi môi trường hoặc lỗi logic phức tạp
        yield f"\n⚠️ **LỖI KỸ THUẬT NGHIÊM TRỌNG:** {type(e).__name__} - Dù SDK là 0.8.0, Python vẫn không tìm thấy hàm. Vui lòng **Clear cache & rebuild** Render."
        return

    # Lưu history
    history.append({"role": "user", "content": user_input_to_use})
    history.append({"role": "model", "content": full_answer})
    session["message_count"] += 1
    save_sessions()

# ... (STATUS LOOP, SLASH COMMANDS, FLASK, BOT EVENTS, RUN giữ nguyên) ...

# ========== BOT EVENTS (CÓ THÊM KIỂM TRA PHIÊN BẢN) ==========
@bot.event
async def on_ready():
    # Kiểm tra version SDK sau khi bot khởi động
    print("⚡ Gemini SDK version:", genai.__version__) 
    print(f"✅ {BOT_NAME} đã sẵn sàng! Logged in as {bot.user}")
    load_sessions()
    random_status.start()
    if GUILD_ID:
        await tree.sync(guild=discord.Object(GUILD_ID))
        print(f"🔄 Slash commands đã sync cho guild {GUILD_ID}")
    else:
        await tree.sync()
        print("🔄 Slash commands đã sync toàn cầu")

# ========== RUN (Giữ nguyên) ==========
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)