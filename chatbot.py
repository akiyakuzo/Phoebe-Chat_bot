# ==== Patch cho Python 3.13 ====
import sys, types
sys.modules['audioop'] = types.ModuleType('audioop')

"""
💖 Phoebe Xinh Đẹp v6.6 Per-User Stateful (Gemini Adaptive Edition)
Flask + Discord.py + Google Gemini API
Hỗ trợ: Flirt mode, reset context per-user, /hoi mọi người dùng được
"""

import os
import random
import discord
import asyncio
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from google import genai

# ========== CONFIG ==========
BOT_NAME = "Phoebe Xinh Đẹp 💖"
TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))

if not TOKEN:
    raise RuntimeError("⚠️ Thiếu biến môi trường TOKEN.")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu GEMINI_API_KEY.")

# ========== PROMPTS ==========
PHOBE_BASE_PROMPT = """
Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves.  

**Persona:** điềm tĩnh, thanh lịch, bí ẩn, tinh nghịch nhẹ.  
**Nguyên tắc hội thoại:** luôn nói bằng tiếng Việt, rõ ràng, duyên dáng, có chiều sâu.
""".strip()

PHOBE_SAFE_INSTRUCTION = "✨ Phong cách: thanh lịch, điềm tĩnh, thân thiện, hơi bí ẩn. Không dùng từ nhạy cảm."
PHOBE_FLIRT_INSTRUCTION = "💞 Phong cách: ngọt ngào, tinh nghịch, flirt nhẹ nhưng an toàn."

# ========== GEMINI CLIENT ==========
client = genai.Client(api_key=GEMINI_API_KEY)

# ========== DISCORD BOT ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== TRẠNG THÁI ==========
flirt_enable = False
user_contexts = {}  # ✅ Per-user chat session

# ========== HELPER ==========
async def ask_gemini(user_id: str, user_input: str) -> str:
    instruction = PHOBE_FLIRT_INSTRUCTION if flirt_enable else PHOBE_SAFE_INSTRUCTION
    final_prompt = PHOBE_BASE_PROMPT + "\n\n" + instruction

    chat_context = user_contexts.get(user_id)
    if chat_context is None:
        chat_context = client.chats.create(
            model="models/gemini-2.0-flash",
            config={"system_instruction": {"parts": [{"text": final_prompt}]}}
        )
        user_contexts[user_id] = chat_context

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(lambda: chat_context.send_message(user_input)),
            timeout=25
        )
        return getattr(response, "text", str(response))
    except asyncio.TimeoutError:
        # Xóa session user khi timeout
        if user_id in user_contexts:
            del user_contexts[user_id]
        return "⚠️ Gemini phản hồi quá chậm, session đã reset, hãy thử lại sau nhé!"
    except Exception as e:
        if user_id in user_contexts:
            del user_contexts[user_id]
        return f"⚠️ Lỗi Gemini: {e}"

# ========== SLASH COMMANDS ==========
@tree.command(name="hoi", description="💬 Hỏi Phoebe Xinh Đẹp!")
async def hoi(interaction: discord.Interaction, cauhoi: str):
    user_id = str(interaction.user.id)
    await interaction.response.defer(thinking=True)
    answer = await ask_gemini(user_id, cauhoi)

    embed = discord.Embed(
        title=f"{BOT_NAME} trả lời 💕",
        description=f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Phobe:** {answer}",
        color=0xFFC0CB
    )
    embed.set_thumbnail(url=random.choice([
        "https://files.catbox.moe/2474tj.png",
        "https://files.catbox.moe/66v9vw.jpg",
        "https://files.catbox.moe/ezqs00.jpg",
        "https://files.catbox.moe/yow35q.png",
        "https://files.catbox.moe/pzbhdp.jpg"
    ]))
    await interaction.followup.send(embed=embed)

@tree.command(name="deleteoldconversation", description="🧹 Xóa lịch sử hội thoại của bạn")
async def delete_conv(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in user_contexts:
        del user_contexts[user_id]
        msg = "🧹 Phobe đã dọn sạch trí nhớ, sẵn sàng trò chuyện lại nè~ 💖"
    else:
        msg = "Trí nhớ của em trống trơn rồi! 🥺"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="chat18plus", description="🔞 Bật/tắt Flirt mode (quyến rũ nhẹ)")
@discord.app_commands.checks.has_permissions(manage_messages=True)  # ✅ chỉ ai có Manage Messages
async def chat18(interaction: discord.Interaction, enable: bool):
    global flirt_enable
    flirt_enable = enable
    user_id = str(interaction.user.id)
    if user_id in user_contexts:
        del user_contexts[user_id]  # reset session

    msg = (
        "💋 Đã bật *flirt mode*! Phobe sẽ nói chuyện ngọt ngào, quyến rũ hơn 😚"
        if enable else
        "🌸 Phobe trở lại phong cách dịu dàng, thanh lịch 💞"
    )
    await interaction.response.send_message(msg, ephemeral=True)

@chat18.error
async def chat18_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "⚠️ Bạn không có quyền bật/tắt Flirt mode. Yêu cầu quyền: Manage Messages.",
            ephemeral=True
        )

# ========== BOT STATUS ==========
status_list = ["Ngắm hoa 🌸", "Ngủ đông cùng anh 💜", "Đang nghe tiếng lòng 💞", "Dõi theo chiến trường ✨", "Chill cùng đồng đội 🌙"]

@tasks.loop(seconds=30)
async def change_status():
    if not bot.is_ready():
        return
    status = random.choice(status_list)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(status))

# ========== FLASK KEEPALIVE ==========
app = Flask(__name__)

@app.route("/healthz")
def home():
    return f"💖 {BOT_NAME} is online and feeling cute~"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

Thread(target=run_flask, daemon=True).start()

# ========== KHỞI ĐỘNG ==========
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {BOT_NAME} đã sẵn sàng! Đăng nhập dưới: {bot.user}")
    if not change_status.is_running():
        change_status.start()

bot.run(TOKEN)