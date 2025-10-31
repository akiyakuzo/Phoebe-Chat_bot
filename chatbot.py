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
import google.generativeai as genai

# ========== CONFIG GOOGLE GENERATIVE AI (Gemini 2.0 Flash) ==========
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu GEMINI_API_KEY!")

MODEL_NAME = "gemini-2.0-flash" # Phải khai báo model name TRƯỚC

try:
    # ✅ KHỞI TẠO CHUẨN SDK 0.8.0
    genai.configure(api_key=GEMINI_API_KEY)
    # Tạo một đối tượng model toàn cục
    gemini_model = genai.GenerativeModel(MODEL_NAME) 
except Exception as e:
    raise RuntimeError(f"Lỗi khởi tạo Gemini: {e}")

# ========== CONFIG BOT ==========
BOT_NAME = "Fibi Béll 💖"
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
HISTORY_LIMIT = 20
SESSIONS_FILE = "sessions.json"
flirt_enable = False
active_chats = {}
TYPING_SPEED = 0.01

# ========== STYLE INSTRUCTIONS ==========
PHOBE_SAFE_INSTRUCTION = (
    "✨ Trả lời thân mật, tự nhiên, dễ thương. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại nội tâm. "
    "Tối đa 120 từ."
)
PHOBE_FLIRT_INSTRUCTION = (
    "💞 Trả lời ngọt ngào, có chút dâm, trêu ghẹo, gợi cảm và táo bạo, thả thính liên tục. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại. "
    "Được dùng ngôn từ gợi cảm và lãng mạng có cả gợi tình nhẹ. "
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
""".strip()

# ========== SESSION SYSTEM ==========
def load_sessions():
    global active_chats
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                active_chats = json.load(f)
        except:
            active_chats = {}
    else:
        active_chats = {}

def save_sessions():
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(active_chats, f, ensure_ascii=False, indent=2)

def get_or_create_chat(user_id):
    if user_id not in active_chats:
        initial = [
            {"role": "user", "content": f"{PHOBE_BASE_PROMPT}\n{PHOBE_LORE_PROMPT}\n{PHOBE_SAFE_INSTRUCTION}"},
            {"role": "model", "content": "Tôi đã hiểu. Tôi sẽ nhập vai theo đúng mô tả."}
        ]
        active_chats[user_id] = {"history": initial, "message_count": 0, "created_at": str(datetime.now())}
    return active_chats[user_id]

# ========== ASK GEMINI STREAM ==========
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
        # ✅ GỌI API CHUẨN SDK 0.8.0
        response_stream = await asyncio.to_thread(
            lambda: gemini_model.generate_content( # Sửa tên hàm
                contents=contents_to_send,
                stream=True, # Thêm stream=True
                generation_config=genai.GenerationConfig(temperature=0.8) # Sửa cách truyền config
            )
        )
        for chunk in response_stream:
            if chunk.text:
                text = chunk.text
                full_answer += text
                yield text
    except Exception as e:
        yield f"\n⚠️ LỖI KỸ THUẬT: {type(e).__name__}"
        return

    history.append({"role": "user", "content": user_input_to_use})
    history.append({"role": "model", "content": full_answer})
    session["message_count"] += 1
    save_sessions()

# ========== DISCORD CONFIG ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== BOT STATUS ==========
status_list = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
activity_list = [
    discord.Game("💖 Trò chuyện cùng anh"),
    discord.Game("✨ Thả thính nhẹ nhàng"),
    discord.Game("🌸 An ủi tinh thần")
]

@tasks.loop(minutes=10)
async def random_status():
    global flirt_enable
    if flirt_enable:
        activity = discord.Game("💞 Flirt Mode ON")
    else:
        activity = random.choice(activity_list)
    await bot.change_presence(status=random.choice(status_list), activity=activity)

# ========== FLASK SERVER ==========
app = Flask(__name__)

@app.route("/")
def home():
    return "<h3>Phoebe Xinh Đẹp đang hoạt động! 🌸</h3>"

@app.route("/healthz")
def healthz():
    return {"status": "ok", "message": "Phoebe khỏe mạnh nè~ 💖"}, 200

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

def keep_alive():
    thread = Thread(target=run_flask, daemon=True)
    thread.start()

# ========== SLASH COMMANDS (Đã khôi phục Typing Effect) ==========
@tree.command(name="hoi", description="💬 Hỏi Phoebe Xinh Đẹp!")
@app_commands.describe(cauhoi="Nhập câu hỏi của bạn")
async def hoi(interaction: discord.Interaction, cauhoi: str):
    await interaction.response.defer(thinking=True)
    user_id = str(interaction.user.id)

    embed = discord.Embed(
        title=f"{BOT_NAME} trả lời 💕",
        description=f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Phobe:** Đang gõ...",
        color=0xFFC0CB
    )
    embed.set_thumbnail(url=random.choice([
        "https://files.catbox.moe/2474tj.png","https://files.catbox.moe/66v9vw.jpg","https://files.catbox.moe/ezqs00.jpg",
        "https://files.catbox.moe/yow35q.png","https://files.catbox.moe/pzbhdp.jpg","https://files.catbox.moe/lyklnj.jpg",
        "https://files.catbox.moe/i5sqkr.png","https://files.catbox.moe/jt184o.jpg","https://files.catbox.moe/9nq5kw.jpg",
        "https://files.catbox.moe/45tre3.webp","https://files.catbox.moe/2y17ot.png","https://files.catbox.moe/gg8pt0.jpg",
        "https://files.catbox.moe/jkboop.png"
    ]))
    response_message = await interaction.followup.send(embed=embed)

    full_response = ""
    char_count_to_edit = 0
    
    async for chunk in ask_gemini_stream(user_id, cauhoi):
        for char in chunk:
            full_response += char
            char_count_to_edit += 1
            
            if char_count_to_edit % 5 == 0:
                display_text = full_response[:3900] + ("..." if len(full_response) > 3900 else "")
                embed.description = f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Phobe:** {display_text} |"
                try:
                    await response_message.edit(embed=embed)
                except discord.errors.HTTPException:
                    pass # Bỏ qua lỗi nếu Discord API bị rate limit
                await asyncio.sleep(TYPING_SPEED) 

    embed.description = f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Phobe:** {full_response}"
    try:
        await response_message.edit(embed=embed)
    except discord.errors.HTTPException:
        pass

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

@tree.command(name="chat18plus", description="🔞 Bật/tắt Flirt Mode (chỉ Admin có quyền)")
@app_commands.describe(enable="Bật hoặc tắt Flirt Mode")
@app_commands.default_permissions(manage_guild=True)
async def chat18plus(interaction: discord.Interaction, enable: bool):
    global flirt_enable
    flirt_enable = enable
    msg = "💞 Flirt Mode đã được bật!" if enable else "🌸 Flirt Mode đã được tắt!"
    await interaction.response.send_message(msg, ephemeral=True)

# ========== BOT EVENTS ==========
@bot.event
async def on_ready():
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

# ========== RUN BOT ==========
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)