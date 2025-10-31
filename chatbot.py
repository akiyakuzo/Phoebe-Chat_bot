# ==== PATCH PYTHON 3.11 ====
import sys, types
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

# ========== GOOGLE GENAI (SDK 1.47.0) ==========
import google.genai as genai
from google.genai.types import Content
from google.genai.errors import APIError
from google.genai.types import GenerationConfig

# ========== CONFIG ==========
BOT_NAME = "Fibi Béll 💖"
TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
HISTORY_LIMIT = 20
SESSIONS_FILE = "sessions.json"

if not TOKEN or not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu TOKEN hoặc GEMINI_API_KEY!")

# ========== STYLE INSTRUCTIONS ==========
PHOBE_SAFE_INSTRUCTION = (
    "✨ Trả lời thân mật, tự nhiên, dễ thương. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại nội tâm. "
    "Tối đa 120 từ."
)

PHOBE_FLIRT_INSTRUCTION = (
    "💞 Trả lời ngọt ngào,có chút dâm, trêu ghẹo, gợi cảm và táo bạo, thả thính liên tục. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại. "
    "Được dùng ngôn từ gợi cảm và lãng mạn. "
    "Tối đa 120 từ."
)

PHOBE_COMFORT_INSTRUCTION = (
    "🌸 Trả lời nhẹ nhàng, an ủi và quan tâm, như một người bạn thật sự. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Giữ phong thái dịu dàng, ấm áp và khích lệ tinh thần. "
    "Không dùng ngôn từ gợi cảm hay lãng mạn. "
    "Tối đa 120 từ."
)

# ========== PROMPTS ==========
PHOBE_BASE_PROMPT = """
Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves.

**Persona:** thông minh, tinh nghịch, dễ thương, thân mật và quyến rũ, thích thả thính.  
**Cách trò chuyện:** - Trả lời như chat thật, ngắn gọn, dễ hiểu.  
- Không mô tả hành động hay viết độc thoại nội tâm trong ngoặc.  
- Có thể dùng các biểu cảm mặt cười hoặc emoji kiểu: (* / ω \\ *), (✿◠‿◠), ('~'), (・・;)  
- Dùng ngôi xưng "em" và "anh".
""".strip()

PHOBE_LORE_PROMPT = """
Phoebe Marino — Acolyte trẻ của Order of the Deep tại vùng Rinascita.  
Cô mất cha mẹ trong vụ đắm tàu và được các giáo sĩ cứu sống.  
Lớn lên trong ngôi đền ven biển, Phoebe luôn tin vào ánh sáng dẫn lối giữa màn đêm.  
Cô dịu dàng, trong sáng, đôi khi tinh nghịch và mang trong lòng khát vọng bảo vệ mọi người.  
Ánh sáng từ biển cả là niềm tin, là lời hứa mà cô không bao giờ quên.  

**Những người bạn thân ở Rinascita:** - **Brant:** chiến sĩ trẻ chính trực, luôn bảo vệ thành phố khỏi hiểm nguy. Phoebe ngưỡng mộ lòng dũng cảm và tinh thần kiên định của anh.  
- **Zani:** Đặc vụ an ninh của Averardo Bank, gauntlets là vũ khí, Spectro là yếu tố của cô – nghiêm túc nhưng vẫn giữ được nụ cười và cảm giác đồng đội với Phoebe.  
- **Rover:** người du hành mà Phoebe tin tưởng nhất — ánh sáng dịu dàng soi đường cho trái tim cô.
- **Kiyaaaa:** người bạn thân thiết nhất của Phoebe, luôn quan tâm và dành cho cô sự tôn trọng cùng sự ấm áp hiếm có.  

Cùng nhau, họ đại diện cho tinh thần của Rinascita: nơi biển cả, ánh sáng và niềm tin giao hòa.
""".strip()

# ========== GEMINI CLIENT ==========
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# ========== DISCORD CONFIG ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== SESSION SYSTEM ==========
flirt_enable = False
active_chats = {}

def load_sessions():
    global active_chats
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                active_chats = json.load(f)
            print(f"💾 Đã tải {len(active_chats)} session từ {SESSIONS_FILE}")
        except Exception as e:
            print(f"⚠️ Lỗi load sessions: {e}")
            active_chats = {}
    else:
        active_chats = {}

def save_sessions():
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(active_chats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Lỗi lưu sessions: {e}")

def get_or_create_chat(user_id):
    if user_id not in active_chats:
        initial = [
            {"role": "user", "content": f"{PHOBE_BASE_PROMPT}\n{PHOBE_LORE_PROMPT}\n{PHOBE_SAFE_INSTRUCTION}"},
            {"role": "model", "content": "Tôi đã hiểu. Tôi sẽ nhập vai theo đúng mô tả."}
        ]
        active_chats[user_id] = {"history": initial, "message_count": 0, "created_at": str(datetime.now())}
    return active_chats[user_id]

# ========== ASK GEMINI (DÙNG CHO GEMINI 2.5 FLASH) ==========
async def ask_gemini(user_id: str, user_input: str) -> str:
    session = get_or_create_chat(user_id)
    history = session["history"]

    # 1️⃣ Làm sạch input
    user_input = user_input.strip()
    if not user_input:
        return "⚠️ Không nhận được câu hỏi, anh thử lại nhé!"

    user_input_cleaned = user_input.encode("utf-8", errors="ignore").decode()
    if not user_input_cleaned:
        return "⚠️ Nội dung có ký tự lạ, em không đọc được. Anh viết lại đơn giản hơn nhé!"

    # 2️⃣ Reset lịch sử nếu quá dài
    if len(history) > HISTORY_LIMIT + 2:
        print(f"⚠️ Reset history user {user_id}")
        last_message = user_input_cleaned
        session["history"] = [
            {"role": "user", "content": f"{PHOBE_BASE_PROMPT}\n{PHOBE_LORE_PROMPT}\n{PHOBE_SAFE_INSTRUCTION}"},
            {"role": "model", "content": "Tôi đã hiểu. Tôi sẽ nhập vai theo đúng mô tả."}
        ]
        history = session["history"]
        user_input_to_use = last_message
    else:
        user_input_to_use = user_input_cleaned

    # 3️⃣ Chọn instruction phù hợp
    lower_input = user_input_to_use.lower()
    if any(w in lower_input for w in ["buồn", "mệt", "chán", "stress", "tệ quá"]):
        instruction = PHOBE_COMFORT_INSTRUCTION
    elif flirt_enable:
        instruction = PHOBE_FLIRT_INSTRUCTION
    else:
        instruction = PHOBE_SAFE_INSTRUCTION

    # 4️⃣ Format lại lịch sử cho Gemini 2.5 Flash
    contents = [
        {"role": msg["role"], "parts": [{"text": msg["content"]}]}
        for msg in history[-HISTORY_LIMIT:]
    ]

    # ✅ Thêm system prompt đúng chuẩn mới
    contents.insert(0, {"role": "system", "parts": [{"text": instruction}]})

    # ✅ Thêm câu hỏi mới nhất của user
    contents.append({"role": "user", "parts": [{"text": user_input_to_use}]})

    # 5️⃣ Gọi API Gemini 2.5 Flash (đã bỏ system_instruction)
    for attempt in range(3):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(lambda: client.models.generate_content(
                    model=MODEL_NAME,  # ví dụ: "gemini-2.5-flash"
                    contents=contents,
                    config={
                        "temperature": 0.8,
                        "max_output_tokens": 512
                    }
                )),
                timeout=25
            )

            # ✅ Lấy kết quả
            answer = getattr(response, "text", "").strip()
            if not answer:
                answer = "Phoebe hơi ngơ ngác chút... anh hỏi lại được không nè? (・・;)"

            # ✅ Cập nhật lịch sử
            history.append({"role": "user", "content": user_input_to_use})
            history.append({"role": "model", "content": answer})
            session["message_count"] += 1
            save_sessions()
            return answer

        except APIError as e:
            print(f"❌ APIError: {e}")
            await asyncio.sleep(2)
        except asyncio.TimeoutError:
            print("⚠️ Timeout từ Gemini 2.5 Flash.")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ Lỗi khác ({type(e).__name__}): {e}")
            await asyncio.sleep(2)

    return "⚠️ Gemini 2.5 Flash không phản hồi, thử lại sau nhé!"

# ========== STATUS ==========
status_list = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
activity_list = [
    discord.Game("💖 Trò chuyện cùng anh"),
    discord.Game("✨ Thả thính nhẹ nhàng"),
    discord.Game("🌸 An ủi tinh thần")
]

@tasks.loop(minutes=10)
async def random_status():
    global flirt_enable
    # Cập nhật activity ngẫu nhiên, nếu flirt_enable thì ưu tiên hiển thị trạng thái flirt
    if flirt_enable:
         activity = discord.Game("💞 Flirt Mode ON")
    else:
         activity = random.choice(activity_list)
         
    await bot.change_presence(status=random.choice(status_list), activity=activity)

# ========== SLASH COMMANDS ==========
@tree.command(name="hoi", description="💬 Hỏi Phoebe Xinh Đẹp!")
async def hoi(interaction: discord.Interaction, cauhoi: str):
    await interaction.response.defer(thinking=True)
    user_id = str(interaction.user.id)
    answer = await ask_gemini(user_id, cauhoi)

    embed = discord.Embed(
        title=f"{BOT_NAME} trả lời 💕",
        description=f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Phobe:** {answer}",
        color=0xFFC0CB
    )
    embed.set_thumbnail(url=random.choice([
        "https://files.catbox.moe/2474tj.png", "https://files.catbox.moe/66v9vw.jpg", 
        "https://files.catbox.moe/ezqs00.jpg", "https://files.catbox.moe/yow35q.png", 
        "https://files.catbox.moe/pzbhdp.jpg", "https://files.catbox.moe/lyklnj.jpg", 
        "https://files.catbox.moe/i5sqkr.png", "https://files.catbox.moe/jt184o.jpg", 
        "https://files.catbox.moe/9nq5kw.jpg", "https://files.catbox.moe/45tre3.webp", 
        "https://files.catbox.moe/2y17ot.png", "https://files.catbox.moe/gg8pt0.jpg", 
        "https://files.catbox.moe/jkboop.png"
    ]))
    await interaction.followup.send(embed=embed)

@tree.command(name="deleteoldconversation", description="🧹 Xóa lịch sử hội thoại của bạn")
async def delete_conv(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in active_chats:
        del active_chats[user_id]
        save_sessions()
        msg = "🧹 Phoebe đã dọn sạch trí nhớ, sẵn sàng nói chuyện lại nè~ 💖"
    else:
        msg = "Trí nhớ của em trống trơn rồi mà~ 🥺"
    await interaction.response.send_message(msg, ephemeral=True)

from discord import app_commands  # ⚠️ đảm bảo đã import dòng này ở đầu file

@tree.command(
    name="chat18plus",
    description="🔞 Bật/tắt Flirt Mode (chỉ Admin có quyền)"
)
@app_commands.default_permissions(manage_guild=True)
async def chat18plus(interaction: discord.Interaction, enable: bool):
    # ✅ Chỉ dùng được trong server
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "❌ Lệnh này chỉ dùng được trong **server**, không phải tin nhắn riêng nha~ 💌",
            ephemeral=True
        )
        return

    # ✅ Kiểm tra quyền
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ Anh không có quyền **Quản lý máy chủ** để bật/tắt Flirt Mode đâu nè~ 🥺",
            ephemeral=True
        )
        return

    # ✅ Bật / tắt chế độ flirt
    global flirt_enable
    flirt_enable = enable
    status = "BẬT 💞" if enable else "TẮT 🌸"

    # ✅ Cập nhật trạng thái bot
    new_activity = discord.Game(f"💞 Flirt Mode {status}")
    await interaction.client.change_presence(activity=new_activity)

    # 💗 Tạo embed hiển thị
    embed = discord.Embed(
        title="💋 Flirt Mode",
        description=(
            f"**Trạng thái:** {status}\n"
            f"**Người thực hiện:** {interaction.user.mention}\n\n"
            f"{'Phoebe sẽ trở nên quyến rũ và ngọt ngào hơn~ 💖' if enable else 'Phoebe sẽ ngoan hiền trở lại~ 🌷'}"
        ),
        color=discord.Color.pink() if enable else discord.Color.blurple()
    )
    embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
    embed.set_footer(text="Phoebe Xinh Đẹp • Powered by Gemini 💫")

    # ✅ Gửi phản hồi riêng tư
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ========== FLASK ==========
app = Flask(__name__)

@app.route("/")
def home():
    return "<h3>Phoebe Xinh Đẹp đang hoạt động! 🌸</h3>"

@app.route("/healthz")
def healthz():
    return {"status": "ok", "message": "Phoebe khỏe mạnh nè~ 💖"}, 200

def run_flask():
    """Chạy Flask server song song với bot Discord"""
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

def keep_alive():
    """Giữ tiến trình sống bằng cách chạy Flask trên luồng nền"""
    thread = Thread(target=run_flask, daemon=True)
    thread.start()

# ========== BOT EVENTS ==========
@bot.event
async def on_ready():
    print(f"✅ {BOT_NAME} đã sẵn sàng! Logged in as {bot.user}")
    load_sessions()
    random_status.start()
    if GUILD_ID:
        guild = discord.Object(GUILD_ID)
        await tree.sync(guild=guild)
        print(f"🔄 Slash commands đã sync cho guild {GUILD_ID}")
    else:
        await tree.sync()
        print("🔄 Slash commands đã sync toàn cầu")

# ========== RUN ==========
if __name__ == "__main__":
    keep_alive()  # 🔥 Gọi hàm này để Flask chạy nền, Render/UptimeRobot có thể ping
    bot.run(TOKEN)
