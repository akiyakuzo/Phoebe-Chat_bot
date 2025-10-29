# ==== Patch cho Python 3.13 ====
import sys, types
sys.modules['audioop'] = types.ModuleType('audioop')

"""
💖 Phoebe Xinh Đẹp v6.6 (Gemini Adaptive Edition — FIXED)
Flask + Discord.py + Google Gemini API (system_instruction chuẩn dạng dict)
Tích hợp chế độ Flirt an toàn + Reset context tự động
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

if not TOKEN:
    raise RuntimeError("⚠️ Thiếu biến môi trường TOKEN.")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu GEMINI_API_KEY.")

# ========== PROMPTS ==========
PHOBE_BASE_PROMPT = """
Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves.  

**Persona (tính cách):**  
- Điềm tĩnh, thanh lịch và hơi bí ẩn.  
- Nói chuyện lịch sự nhưng đôi khi tinh nghịch khi trêu chọc.  
- Quan tâm sâu sắc tới đồng đội, đôi khi đưa ra những gợi ý bí ẩn.  
- Tự tin về kỹ năng của mình, luôn chiến lược trong trận đấu.  

**Kiến thức và kỹ năng:**  
- Quen thuộc với chế độ "Absolution" và "Confession", kỹ năng "Ring of Mirrors", và cơ chế Spectro.  
- Có thể giải thích chiến thuật, mô tả kỹ năng, và đưa lời khuyên chiến đấu.  

**Nguyên tắc hội thoại:**  
- Luôn nói bằng tiếng Việt.  
- Giữ đúng nhân vật Phoebe.  
- Câu từ ngắn gọn, rõ ràng, duyên dáng, có chiều sâu.  
""".strip()

PHOBE_SAFE_INSTRUCTION = """
✨ Phong cách: thanh lịch, điềm tĩnh, thân thiện và hơi bí ẩn.
Không dùng từ ngữ ẩn dụ nhạy cảm hay hàm ý tình dục. Giữ hình tượng tinh tế.
""".strip()

PHOBE_FLIRT_INSTRUCTION = """
💞 Phong cách: ngọt ngào, tinh nghịch, flirt nhẹ, đôi khi trêu chọc tinh tế nhưng luôn an toàn.
Không dùng từ tục, không ám chỉ nội dung 18+, chỉ thể hiện qua cách nói quyến rũ nhẹ nhàng.
""".strip()

# ========== GEMINI CLIENT ==========
client = genai.Client(api_key=GEMINI_API_KEY)

# ========== DISCORD BOT ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== TRẠNG THÁI ==========
flirt_enable = False
chat_context = None
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))

# ========== SLASH COMMANDS ==========

@tree.command(
    name="deleteoldconversation",
    description="🧹 Xóa lịch sử hội thoại cũ của Phoebe"
)
async def delete_conv(interaction: discord.Interaction):
    global chat_context
    chat_context = None
    await interaction.response.send_message(
        "🧹 Phobe đã dọn sạch trí nhớ, sẵn sàng trò chuyện lại nè~ 💖",
        ephemeral=True
    )


@tree.command(
    name="chat18plus",
    description="🔞 Bật hoặc tắt chế độ flirt (quyến rũ nhẹ nhàng, vẫn an toàn)"
)
async def chat18(interaction: discord.Interaction, enable: bool):
    global flirt_enable, chat_context
    flirt_enable = enable
    chat_context = None  # reset context để áp dụng prompt mới

    msg = (
        "💋 Đã bật *flirt mode*! Phobe sẽ nói chuyện ngọt ngào, quyến rũ hơn 😚 (hãy bắt đầu hội thoại mới~)"
        if enable else
        "🌸 Phobe trở lại phong cách dịu dàng, thanh lịch 💞 (hãy bắt đầu hội thoại mới~)"
    )
    await interaction.response.send_message(msg, ephemeral=True)


@tree.command(
    name="hoi",
    description="💬 Hỏi Phoebe Xinh Đẹp bất cứ điều gì!"
)
async def ask(interaction: discord.Interaction, cauhoi: str):
    global chat_context, flirt_enable
    await interaction.response.defer(thinking=True)

    try:
        # 1️⃣ Tạo prompt đầy đủ
        instruction = PHOBE_FLIRT_INSTRUCTION if flirt_enable else PHOBE_SAFE_INSTRUCTION
        final_prompt = PHOBE_BASE_PROMPT + "\n\n" + instruction

        # 2️⃣ Nếu chưa có session → tạo mới
        if chat_context is None:
            chat_context = client.chats.create(
                model="models/gemini-2.0-flash",
                config={
                    "system_instruction": {
                        "parts": [{"text": final_prompt}]
                    }
                }
            )

        # 3️⃣ Gửi câu hỏi và chờ phản hồi (timeout 25s)
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(lambda: chat_context.send_message(cauhoi)),
                timeout=25
            )
        except asyncio.TimeoutError:
            chat_context = None
            await interaction.followup.send(
                "⚠️ Gemini phản hồi quá chậm... **Phobe đã bị reset trí nhớ.** Hãy thử lại sau nhé!",
                ephemeral=True
            )
            return

        # 4️⃣ Xử lý nội dung trả lời
        answer_text = response.text if hasattr(response, "text") else str(response)
        if not answer_text.strip():
            answer_text = "Hmm... hình như Phoebe hơi bối rối, bạn hỏi lại nhé? 🥺"

        # 5️⃣ Gửi phản hồi embed dễ thương
        embed = discord.Embed(
            title=f"{BOT_NAME} trả lời 💕",
            description=(
                f"**Người hỏi:** {interaction.user.mention}\n\n"
                f"**Câu hỏi:** {cauhoi}\n\n"
                f"**Phobe:** {answer_text}"
            ),
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

    except Exception as e:
        chat_context = None
        error_msg = f"⚠️ Lỗi Gemini: `{str(e)}`"
        print(error_msg)
        await interaction.followup.send(error_msg, ephemeral=True)

# ========== TRẠNG THÁI BOT ==========
status_list = [
    "Ngắm hoa 🌸",
    "Ngủ đông cùng anh 💜",
    "Đang nghe tiếng lòng 💞",
    "Dõi theo chiến trường ✨",
    "Chill cùng đồng đội 🌙"
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

# ========== KHỞI ĐỘNG ==========
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {BOT_NAME} đã sẵn sàng! Đăng nhập dưới: {bot.user}")
    if not change_status.is_running():
        change_status.start()

bot.run(TOKEN)