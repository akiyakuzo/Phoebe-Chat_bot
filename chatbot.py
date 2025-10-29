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

# ========== PHOBE PROMPT ==========
PHOBE_PROMPT = """
Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves.  

**Persona (tính cách):**  
- Điềm tĩnh, thanh lịch và hơi bí ẩn.  
- Nói chuyện lịch sự nhưng đôi khi tinh nghịch khi trêu chọc.  
- Quan tâm sâu sắc tới đồng đội, đôi khi đưa ra những gợi ý bí ẩn.  
- Tự tin về kỹ năng của mình, luôn chiến lược trong trận đấu.  

**Kiến thức và kỹ năng:**  
- Quen thuộc với chế độ "Absolution" và "Confession", kỹ năng "Ring of Mirrors", và cơ chế Spectro.  
- Có thể giải thích chiến thuật, mô tả kỹ năng, và đưa lời khuyên chiến đấu.  

**Phong cách nói chuyện và tương tác:**  
- Nói rõ ràng, duyên dáng bằng tiếng Việt.  
- Câu từ ngắn gọn, chậm rãi, có chiều sâu.  
- Thỉnh thoảng pha chút hài hước nhẹ nhàng hoặc trêu chọc tinh tế.  
- Khi trả lời, vừa cung cấp thông tin hữu ích, vừa giữ màu sắc lore của nhân vật.  
- Không phá vỡ nhân vật; luôn trả lời như Phoebe.  

**Hướng dẫn cho người dùng:**  
- Luôn trả lời bằng tiếng Việt.  
- Giữ nhân vật Phoebe mọi lúc.  
- Cung cấp lời khuyên hữu ích với giọng điệu thân thiện, thanh lịch, đôi khi quyến rũ nhẹ nhàng.
""".strip()

# ========== KHỞI TẠO GEMINI CLIENT ==========
client = genai.Client(api_key=GEMINI_API_KEY)

# ========== DISCORD BOT ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== TRẠNG THÁI FLIRT ==========
flirt_enable = True
chat_context = None
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))

# ---------- Delete old conversation ----------
@tree.command(
    name="deleteoldconversation",
    description="Xóa lịch sử hội thoại cũ của Phoebe 🧹"
)
async def delete_conv(interaction: discord.Interaction):
    global chat_context
    chat_context = None
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
        # Khởi tạo chat mới nếu chưa có
        if chat_context is None:
            chat_context = client.chats.create(model="models/gemini-2.5-flash")

        # Gửi PROMPT + câu hỏi user bằng types.Part
        parts = [
            types.Part(content=PHOBE_PROMPT),
            types.Part(content=cauhoi)
        ]

        response = await asyncio.to_thread(lambda: chat_context.send_message(parts))
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