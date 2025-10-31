# ==== Patch cho Python 3.13 ====
import sys, types
sys.modules['audioop'] = types.ModuleType('audioop')

import os, json, random, asyncio
import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime
import google.genai as genai
from google.genai.errors import APIError

# ========== CONFIG ==========
BOT_NAME = "Phoebe Xinh Đẹp 💖"
TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
SESSIONS_FILE = "sessions.json"
HISTORY_LIMIT = 20  # Số tin nhắn tối đa lưu trữ trong session

if not TOKEN or not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu TOKEN hoặc GEMINI_API_KEY!")

# ========== PROMPTS ==========
PHOBE_BASE_PROMPT = """
Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves.

**Persona:** thông minh, tinh nghịch, dễ thương, thân mật và quyến rũ, thích thả thính.  
**Cách trò chuyện:**  
- Trả lời như chat thật, ngắn gọn, dễ hiểu.  
- Không mô tả hành động hay viết độc thoại nội tâm trong ngoặc.  
- Có thể dùng các biểu cảm mặt cười hoặc emoji kiểu: (* / ω \ *), (✿◠‿◠), ('~'), (・・;)  
- Dùng ngôi xưng "em" và "anh".
""".strip()

PHOBE_LORE_PROMPT = """
Phoebe Marino — Acolyte trẻ của Order of the Deep tại vùng Rinascita.  
Cô mất cha mẹ trong vụ đắm tàu và được các giáo sĩ cứu sống.  
Lớn lên trong ngôi đền ven biển, Phoebe luôn tin vào ánh sáng dẫn lối giữa màn đêm.  
Cô dịu dàng, trong sáng, đôi khi tinh nghịch và mang trong lòng khát vọng bảo vệ mọi người.  
Ánh sáng từ biển cả là niềm tin, là lời hứa mà cô không bao giờ quên.  

**Những người bạn thân ở Rinascita:**  
- **Brant:** chiến sĩ trẻ chính trực, luôn bảo vệ thành phố khỏi hiểm nguy. Phoebe ngưỡng mộ lòng dũng cảm và tinh thần kiên định của anh.  
- **Zani:** Đặc vụ an ninh của Averardo Bank, gauntlets là vũ khí, Spectro là yếu tố của cô – nghiêm túc nhưng vẫn giữ được nụ cười và cảm giác đồng đội với Phoebe.  
- **Rover:** người du hành mà Phoebe tin tưởng nhất — ánh sáng dịu dàng soi đường cho trái tim cô.
- **Kiyaaaa:** người bạn thân thiết nhất của Phoebe, luôn quan tâm và dành cho cô sự tôn trọng cùng sự ấm áp hiếm có.  

Cùng nhau, họ đại diện cho tinh thần của Rinascita: nơi biển cả, ánh sáng và niềm tin giao hòa.
""".strip()

# ========== STYLE INSTRUCTIONS ==========
PHOBE_SAFE_INSTRUCTION = (
    "✨ Trả lời thân mật, tự nhiên, dễ thương. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại nội tâm. "
    "Tối đa 120 từ."
)

PHOBE_FLIRT_INSTRUCTION = (
    "💞 Trả lời ngọt ngào, trêu ghẹo nhẹ, gợi cảm, thả thính liên tục. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại. "
    "Được dùng ngôn từ gợi cảm hay lãng mạn. "
    "Tối đa 120 từ."
)

PHOBE_COMFORT_INSTRUCTION = (
    "🌸 Trả lời nhẹ nhàng, an ủi và quan tâm, như một người bạn thật sự. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \ *), (✿◠‿◠). "
    "Giữ phong thái dịu dàng, ấm áp và khích lệ tinh thần. "
    "Không dùng ngôn từ gợi cảm hay lãng mạn. "
    "Tối đa 120 từ."
)

# ========== GEMINI CLIENT ==========
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# ========== DISCORD BOT ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== SESSION MANAGEMENT ==========
flirt_enable = False
active_chats = {}  # {user_id: {'history': [...], 'message_count': int, 'created_at': datetime}}

def load_sessions():
    global active_chats
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                active_chats = json.load(f)
            print(f"💾 Đã tải {len(active_chats)} session cũ từ {SESSIONS_FILE}")
        except Exception as e:
            print(f"⚠️ Không thể load sessions: {e}")
            active_chats = {}
    else:
        active_chats = {}

def save_sessions():
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(active_chats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu session: {e}")

def get_or_create_chat(user_id: str):
    if user_id not in active_chats:
        initial_history = [
            {"role": "user", "content": f"{PHOBE_BASE_PROMPT}\n{PHOBE_LORE_PROMPT}\n{PHOBE_SAFE_INSTRUCTION}"},
            {"role": "model", "content": "Tôi đã hiểu. Tôi sẽ nhập vai theo đúng mô tả."}
        ]
        active_chats[user_id] = {
            "history": initial_history,
            "message_count": 0,
            "created_at": str(datetime.now())
        }
    return active_chats[user_id]

# ========== HELPER: ASK GEMINI ==========
async def ask_gemini(user_id: str, user_input: str) -> str:
    session = get_or_create_chat(user_id)
    history = session['history']

    # 🌟 RESET HISTORY NẾU QUÁ DÀI
    if len(history) > HISTORY_LIMIT + 2:
        print(f"⚠️ History của user {user_id} quá dài ({len(history)} tin), đang reset.")
        last_message = user_input
        session['history'] = [
            {"role": "user", "content": f"{PHOBE_BASE_PROMPT}\n{PHOBE_LORE_PROMPT}\n{PHOBE_SAFE_INSTRUCTION}"},
            {"role": "model", "content": "Tôi đã hiểu. Tôi sẽ nhập vai theo đúng mô tả."}
        ]
        session['message_count'] = 0
        user_input = last_message

    lower_input = user_input.lower()
    if any(w in lower_input for w in ["buồn", "mệt", "stress", "chán", "khó chịu", "tệ quá"]):
        instruction = PHOBE_COMFORT_INSTRUCTION
    elif flirt_enable:
        instruction = PHOBE_FLIRT_INSTRUCTION
    else:
        instruction = PHOBE_SAFE_INSTRUCTION

    # 🌟 Thêm tin nhắn user vào history trong vòng lặp attempt
  for attempt in range(3):
    # Thêm tin nhắn user
    history.append({"role": "user", "content": user_input})
    
    try:
        # Gọi API Gemini
        response = await asyncio.to_thread(lambda: client.models.generate_content(
            model="gemini-2.5-flash",
            contents=history,
            config={"temperature": 0.8}
        ))
        answer = getattr(response, "text", "").strip()
        if not answer:
            answer = "Phoebe hơi ngơ ngác chút... anh hỏi lại được không nè? (・・;)"
        
        # Thêm phản hồi bot vào history
        history.append({"role": "model", "content": answer})
        session['message_count'] += 1
        save_sessions()
        return answer

    except APIError as api_err:
        # Xử lý lỗi API chi tiết
        if history and history[-1]['role'] == 'user': history.pop()
        save_sessions()
        # ... logic xử lý lỗi Key/Billing ...

    except Exception as e:
        # 🌟 THÊM DÒNG NÀY
        print(f"❌ LỖI GEMINI CHUNG KHÔNG PHẢI APIError: {type(e).__name__} - {e}")

        if history and history[-1]['role'] == 'user': history.pop()
        save_sessions()
        if attempt < 2:
            await asyncio.sleep(2)
        else:
            return f"⚠️ Gemini đang gặp sự cố: Lỗi {type(e).__name__}, thử lại sau nhé!"

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
        "https://files.catbox.moe/pzbhdp.jpg",
        "https://files.catbox.moe/lyklnj.jpg",
        "https://files.catbox.moe/i5sqkr.png",
        "https://files.catbox.moe/jt184o.jpg",
        "https://files.catbox.moe/9nq5kw.jpg",
        "https://files.catbox.moe/45tre3.webp",
        "https://files.catbox.moe/2y17ot.png",
        "https://files.catbox.moe/gg8pt0.jpg",
        "https://files.catbox.moe/jkboop.png"
    ]))
    await interaction.followup.send(embed=embed)

@tree.command(name="deleteoldconversation", description="🧹 Xóa lịch sử hội thoại của bạn")
async def delete_conv(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in active_chats:
        del active_chats[user_id]
        save_sessions()
        msg = "🧹 Phobe đã dọn sạch trí nhớ, sẵn sàng trò chuyện lại nè~ 💖"
    else:
        msg = "Trí nhớ của em trống trơn rồi! 🥺"
    await interaction.response.send_message(msg, ephemeral=True)

# ===== FLIRT MODE =====
@tree.command(name="chat18plus", description="🔞 Bật/tắt Flirt mode (quyến rũ nhẹ)")
async def chat18plus(interaction: discord.Interaction, enable: bool):
    global flirt_enable
    flirt_enable = enable
    status = "BẬT" if enable else "TẮT"
    await interaction.response.send_message(f"🔞 Flirt mode {status} cho tất cả các cuộc trò chuyện.", ephemeral=True)

# ===== FLASK APP =====
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return f"<h1>{BOT_NAME} đang chạy 🚀</h1>", 200

@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

# ===== BOT READY EVENT =====
@bot.event
async def on_ready():
    print(f"✅ {BOT_NAME} đã sẵn sàng! Logged in as {bot.user}")
    load_sessions()
    # Sync slash commands
    if GUILD_ID:
        guild = discord.Object(GUILD_ID)
        await tree.sync(guild=guild)
        print(f"🔄 Commands đã được sync cho guild {GUILD_ID}")
    else:
        await tree.sync()
        print("🔄 Commands đã được sync global")

# ===== RUN BOT + FLASK =====
if __name__ == "__main__":
    # Chạy Flask ở thread riêng
    Thread(target=run_flask, daemon=True).start()
    # Chạy Discord bot
    bot.run(TOKEN)