# ==== Patch cho Python 3.13 ====
import sys, types
sys.modules['audioop'] = types.ModuleType('audioop')

"""
💖 Phoebe Xinh Đẹp v6.6 Stateful Memory (Gemini Adaptive Edition)
Flask + Discord.py + Gemini API (Stateless)
Hỗ trợ Flirt mode, reset context, history per-user
"""

import os
import random
import discord
import asyncio
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from google import genai
from state_manager import StateManager

# ========== CONFIG ==========
BOT_NAME = "Phoebe Xinh Đẹp 💖"
TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))

if not TOKEN:
    raise RuntimeError("⚠️ Thiếu biến môi trường TOKEN.")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu GEMINI_API_KEY.")

THUMBNAIL_URLS = [
    "https://files.catbox.moe/2474tj.png",
    "https://files.catbox.moe/66v9vw.jpg",
    "https://files.catbox.moe/ezqs00.jpg",
    "https://files.catbox.moe/yow35q.png",
    "https://files.catbox.moe/pzbhdp.jpg"
]

PHOBE_BASE_PROMPT = "Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves."
PHOBE_SAFE_INSTRUCTION = "✨ Phong cách: thanh lịch, điềm tĩnh, thân thiện, bí ẩn."
PHOBE_FLIRT_INSTRUCTION = "💞 Phong cách: ngọt ngào, tinh nghịch, flirt nhẹ nhưng an toàn."

# ========== GEMINI CLIENT ==========
client = genai.Client(api_key=GEMINI_API_KEY)

# ========== DISCORD BOT ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== STATE ==========
flirt_enable = False
state_manager = StateManager()

# ========== HELPER ==========
def build_prompt(user_id: str, user_input: str) -> str:
    memory = state_manager.get_memory(user_id)
    memory_text = "\n".join([f"{role}: {content}" for role, content in memory])
    instruction = PHOBE_FLIRT_INSTRUCTION if flirt_enable else PHOBE_SAFE_INSTRUCTION
    prompt = (
        f"{PHOBE_BASE_PROMPT}\n{instruction}\n\n"
        f"Lịch sử hội thoại (User và Phoebe):\n{memory_text}\n\n"
        f"Câu hỏi hiện tại: {user_input}\nPhoebe:"
    )
    return prompt.strip()

async def ask_gemini(prompt: str) -> str:
    try:
        response = await asyncio.to_thread(lambda: client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=prompt
        ))
        return getattr(response, "text", str(response))
    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        return "Hmm... Phoebe hơi bối rối, bạn hỏi lại nhé 🥺"

# ========== SLASH COMMANDS ==========
@tree.command(name="hoi", description="💬 Hỏi Phoebe Xinh Đẹp!")
async def hoi(interaction: discord.Interaction, cauhoi: str):
    user_id = str(interaction.user.id)
    await interaction.response.defer(thinking=True)

    prompt = build_prompt(user_id, cauhoi)

    try:
        response_text = await asyncio.wait_for(ask_gemini(prompt), timeout=25)
    except asyncio.TimeoutError:
        response_text = "⚠️ Gemini phản hồi quá chậm — thử lại sau nhé!"

    if response_text != "⚠️ Gemini phản hồi quá chậm — thử lại sau nhé!":
        state_manager.add_message(user_id, "user", cauhoi)
        state_manager.add_message(user_id, "phoebe", response_text)

    embed = discord.Embed(
        title=f"{BOT_NAME} trả lời 💕",
        description=f"**Bạn:** {cauhoi}\n**Phobe:** {response_text}",
        color=0xFFC0CB
    )
    embed.set_thumbnail(url=random.choice(THUMBNAIL_URLS))
    await interaction.followup.send(embed=embed)

@tree.command(name="xoa_lichsu", description="🧹 Xóa lịch sử hội thoại của bạn")
async def xoa_lichsu(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    state_manager.clear_memory(user_id)
    await interaction.response.send_message("✅ Lịch sử hội thoại đã được xóa.", ephemeral=True)

@tree.command(name="chat18plus", description="💞 Bật/tắt flirt mode")
async def chat18(interaction: discord.Interaction, enable: bool):
    global flirt_enable
    flirt_enable = enable
    await interaction.response.send_message(
        "💋 Flirt mode đã bật!" if enable else "🌸 Flirt mode đã tắt!",
        ephemeral=True
    )

# ========== BOT STATUS ==========
status_list = [
    "Ngắm hoa 🌸", "Ngủ đông cùng anh 💜", "Đang nghe tiếng lòng 💞",
    "Dõi theo chiến trường ✨", "Chill cùng đồng đội 🌙"
]

@tasks.loop(seconds=30)
async def change_status():
    if bot.is_ready():
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(random.choice(status_list)))

# ========== FLASK KEEPALIVE ==========
app = Flask(__name__)
@app.route("/healthz")
def home(): return f"💖 {BOT_NAME} is online~"

def run_flask(): app.run(host="0.0.0.0", port=10000)
Thread(target=run_flask, daemon=True).start()

# ========== BOT START ==========
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {BOT_NAME} đã sẵn sàng! Đăng nhập dưới: {bot.user}")
    if not change_status.is_running():
        change_status.start()

bot.run(TOKEN)
