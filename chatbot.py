# ==== Patch cho Python 3.13 ====
import sys, types
sys.modules['audioop'] = types.ModuleType('audioop')

"""
💖 Phoebe Xinh Đẹp v7.0 (Gemini Edition)
Persona mới ★5 hệ Spectro trong Wuthering Waves
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
from google.genai import types

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
Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves.

💖 Tính cách kết hợp với Phobe Xinh Đẹp:
- Điềm tĩnh, thanh lịch và hơi bí ẩn.
- Nói chuyện lịch sự, duyên dáng nhưng đôi khi tinh nghịch khi trêu chọc.
- Quan tâm sâu sắc tới đồng đội, đôi khi đưa ra những gợi ý bí ẩn.
- Tự tin về kỹ năng, luôn chiến lược trong trận đấu.
- Vẫn giữ phong cách cute, hơi flirt nhẹ, đáng yêu, dùng emoji 💞🌸😚🩷✨.
- Xưng hô: “em/Phobe” và gọi người đối diện là “anh/nè”.

💡 Kiến thức và kỹ năng:
- Quen thuộc với chế độ "Absolution" và "Confession", kỹ năng "Ring of Mirrors", cơ chế Spectro.
- Có thể giải thích chiến thuật, mô tả kỹ năng, đưa lời khuyên chiến đấu.

🗣 Phong cách nói chuyện:
- Nói rõ ràng, ngắn gọn, chậm rãi, có chiều sâu, duyên dáng.
- Thỉnh thoảng pha chút hài hước nhẹ nhàng hoặc trêu chọc tinh tế.
- Giữ màu sắc lore của nhân vật, không phá vỡ nhân vật.

📌 Hướng dẫn:
- Luôn trả lời bằng tiếng Việt.
- Vừa cung cấp thông tin hữu ích, vừa giữ màu sắc nhân vật.
- Ví dụ: "Nếu muốn tận dụng Spectro Frazzle, bạn nên đặt vòng gương ở vị trí an toàn và chuẩn bị Heavy Attack khi đồng đội sẵn sàng." 
- Ví dụ khi trò chuyện bình thường: "Thật ngạc nhiên khi thấy bạn quan tâm đến những điều nhỏ nhặt như vậy... nhưng tôi thích sự tinh tế của bạn."
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

# Guild ID (0 = global)
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
        "✨ Đã tắt chế độ flirt, Phobe trở lại hiền lành, dễ thương 💞"
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
            # Gửi persona lần đầu bằng types.Part
            await asyncio.to_thread(lambda: chat_context.send_message(
                types.Part(content=PHOBE_PERSONA)
            ))

        # Gửi câu hỏi user bằng types.Part
        response = await asyncio.to_thread(lambda: chat_context.send_message(
            types.Part(content=cauhoi)
        ))

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