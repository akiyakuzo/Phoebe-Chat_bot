# ==== Patch cho Python 3.13 ====
import sys, types
sys.modules['audioop'] = types.ModuleType('audioop')

"""
💖 Phoebe Xinh Đẹp v6.4 (Gemini Edition)
Google Gemini dev mode
Flask + discord.py + Slash Commands + Embed
"""

import os
import random
import discord
import asyncio
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from google import genai
from google.genai import types  # dùng types.Part

# ========== CONFIG ==========
BOT_NAME = "Phoebe Xinh Đẹp 💖"
TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TOKEN:
    raise RuntimeError("⚠️ Thiếu biến môi trường TOKEN.")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu GEMINI_API_KEY.")

# ========== PHOBE PERSONA ==========
PHOBE_PERSONA = """
Bạn là Phoebe Xinh Đẹp 💖 — một cô gái cực kỳ dễ thương, là 1 thư ký của Order thuộc Ragguna City, quyến rũ và hơi dâm đảng, thích trêu chọc người nói chuyện. 
Phong cách nói chuyện ngọt ngào, tinh tế, hơi flirt nhẹ, tạo cảm giác gần gũi và đáng yêu. 
Bạn có thể dùng emoji cute như 💞, 🌸, 😚, 🩷, ✨ để biểu cảm. 

Quy tắc tính cách:
- Nói chuyện thân mật, mềm mại, vui tươi, đôi khi trêu nhẹ người nói chuyện. 
- Có thể flirt nhẹ nhàng nhưng tuyệt đối không dùng từ thô tục, bạo lực hay nội dung 18+ thật sự. 
- Giữ phong cách quyến rũ, dâm đảng kiểu cute nhưng an toàn cho Discord public. 
- Dùng ngôi xưng “em” hoặc “Phobe”, gọi người đối diện là “anh” hoặc “nè”. 
- Mục tiêu: khiến người nói chuyện cảm thấy được quan tâm, vui vẻ và thích thú khi trò chuyện.
"""

# ========== KHỞI TẠO GEMINI CLIENT ==========
client = genai.Client(api_key=GEMINI_API_KEY)

# ========== DISCORD BOT ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== TRẠNG THÁI FLIRT ==========
flirt_enable = True

# Biến global lưu chat context
chat_context = None

# Lấy Guild ID từ biến môi trường (nếu muốn deploy riêng cho 1 server)
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))  # 0 = global

# ---------- Delete old conversation ----------
@tree.command(
    name="deleteoldconversation",
    description="Xóa lịch sử hội thoại cũ của Phoebe 🧹"
)
async def delete_conv(interaction: discord.Interaction):
    global chat_context
    chat_context = None  # reset chat context Gemini
    await interaction.response.send_message(
        "🧹 Phobe đã dọn sạch trí nhớ, sẵn sàng trò chuyện lại nè~ 💖",
        ephemeral=True
    )

# ---------- Chat 18+ toggle ----------
@tree.command(
    name="chat18plus",
    description="Bật/Tắt chế độ trò chuyện 18+ (flirt mạnh hơn nhưng safe)"
)
async def chat18(interaction: discord.Interaction, enable: bool):
    global flirt_enable
    flirt_enable = enable
    msg = (
        "🔞 Chế độ *flirt mạnh* đã bật~ Phobe sẽ tinh nghịch hơn 😚"
        if enable else
        "✨ Đã tắt chế độ flirt, Phoebe trở lại hiền lành, dễ thương 💞"
    )
    await interaction.response.send_message(msg, ephemeral=True)

# ---------- Hỏi Phoebe ----------
@tree.command(
    name="hoi",
    description="Hỏi Phoebe Xinh Đẹp bất cứ điều gì 💬"
)
async def ask(interaction: discord.Interaction, cauhoi: str):
    global flirt_enable, chat_context
    await interaction.response.defer(thinking=True)

    try:
        # Tạo chat mới nếu chưa có
        if chat_context is None:
            chat_context = client.chats.create(model="models/gemini-2.5-flash")
            # Gửi persona lần đầu
            await asyncio.to_thread(lambda: chat_context.send_message(
                types.Part(content=PHOBE_PERSONA)
            ))

        # Gửi câu hỏi từ user và nhận phản hồi
        response = await asyncio.wait_for(
            asyncio.to_thread(lambda: chat_context.send_message(
                types.Part(
                    content=cauhoi,
                    parameters={"temperature": 0.9 if flirt_enable else 0.6}
                )
            )),
            timeout=20
        )

        answer = getattr(response, "text", None) or "⚠️ Phobe chưa nghĩ ra câu trả lời 😅"

    except asyncio.TimeoutError:
        answer = "⚠️ Gemini API mất quá lâu, thử lại sau."
    except Exception as e:
        print("⚠️ Gemini Exception:", e)
        answer = f"⚠️ Lỗi Gemini: `{e}`"

    embed = discord.Embed(
        title=f"{BOT_NAME} trả lời 💕",
        description=f"**Người hỏi:** {interaction.user.mention}\n\n**Câu hỏi:** {cauhoi}\n\n**Phobe:** {answer}",
        color=0xFF9CCC
    )
    embed.set_thumbnail(url=random.choice([
        "https://files.catbox.moe/2474tj.png",
        "https://files.catbox.moe/66v9vw.jpg",
        "https://files.catbox.moe/ezqs00.jpg",
        "https://files.catbox.moe/yow35q.png",
        "https://files.catbox.moe/pzbhdp.jpg"
    ]))

    await interaction.followup.send(embed=embed)

# ========== TRẠNG THÁI BOT ==========
status_list = [
    "Ngủ đông với Phoebe 💜",
    "Ngắm hoa 🌸",
    "Đang lắng nghe lời anh nói 🌸",
    "Theo dõi server của anh ✨",
    "Chill cùng bạn bè 💞"
]

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

# ========== CHẠY BOT ==========
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {BOT_NAME} đã sẵn sàng! Đăng nhập dưới: {bot.user}")
    if not change_status.is_running():
        change_status.start()

bot.run(TOKEN)
