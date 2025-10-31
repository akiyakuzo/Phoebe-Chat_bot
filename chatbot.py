# ==== PATCH PYTHON 3.11 ====
import sys, types
sys.modules['audioop'] = types.ModuleType('audioop')

# ========== IMPORTS ==========
import os, json, random, asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

# ========== GOOGLE GENAI (SDK 1.47.0) ==========
import google.genai as genai
from google.genai.errors import APIError

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
    "Tối đa 120 từ."
)
PHOBE_COMFORT_INSTRUCTION = (
    "🌸 Trả lời nhẹ nhàng, an ủi và quan tâm, như một người bạn thật sự. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Giữ phong thái dịu dàng, ấm áp và khích lệ tinh thần. "
    "Tối đa 120 từ."
)

# ========== PROMPTS ==========
PHOBE_BASE_PROMPT = """
Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves.

**Persona:** thông minh, tinh nghịch, dễ thương, thân mật và quyến rũ, thích thả thính, có chút dâm.  
**Cách trò chuyện:** Trả lời như chat thật, ngắn gọn, dễ hiểu. Không mô tả hành động hay viết độc thoại.  
Dùng emoji: (* / ω \\ *), (✿◠‿◠), ('~'), (・・;)  
Dùng ngôi xưng "em" và "anh".
""".strip()

PHOBE_LORE_PROMPT = """
Phoebe Marino — Acolyte trẻ của Order of the Deep tại Rinascita. Cô mất cha mẹ trong vụ đắm tàu và được cứu sống. Lớn lên trong ngôi đền ven biển, Phoebe tin vào ánh sáng dẫn lối. Dịu dàng, tinh nghịch, mong bảo vệ mọi người.
""".strip()

# ========== GEMINI CLIENT ==========
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.0-flash"  # ✅ dùng bản ổn định 2.0 Flash

# ========== DISCORD BOT ==========
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
        except:
            active_chats = {}
    else:
        active_chats = {}

def save_sessions():
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(active_chats, f, ensure_ascii=False, indent=2)

def get_or_create_chat(user_id):
    if user_id not in active_chats:
        active_chats[user_id] = {
            "history": [
                {"role": "user", "content": f"{PHOBE_BASE_PROMPT}\n{PHOBE_LORE_PROMPT}\n{PHOBE_SAFE_INSTRUCTION}"},
                {"role": "model", "content": "Tôi đã hiểu. Tôi sẽ nhập vai theo đúng mô tả."}
            ],
            "message_count": 0,
            "created_at": str(datetime.now())
        }
    return active_chats[user_id]

# ========== ASK GEMINI ==========
async def ask_gemini(user_id: str, user_input: str) -> str:
    session = get_or_create_chat(user_id)
    history = session["history"]

    user_input = user_input.strip()
    if not user_input:
        return "⚠️ Không nhận được câu hỏi, anh thử lại nhé!"

    if len(history) > HISTORY_LIMIT + 2:
        last_message = user_input
        session["history"] = [
            {"role": "user", "content": f"{PHOBE_BASE_PROMPT}\n{PHOBE_LORE_PROMPT}\n{PHOBE_SAFE_INSTRUCTION}"},
            {"role": "model", "content": "Tôi đã hiểu. Tôi sẽ nhập vai theo đúng mô tả."}
        ]
        history = session["history"]
        user_input_to_use = last_message
    else:
        user_input_to_use = user_input

    # Chọn instruction
    lower_input = user_input_to_use.lower()
    if any(w in lower_input for w in ["buồn", "mệt", "chán", "stress", "tệ quá"]):
        instruction = PHOBE_COMFORT_INSTRUCTION
    elif flirt_enable:
        instruction = PHOBE_FLIRT_INSTRUCTION
    else:
        instruction = PHOBE_SAFE_INSTRUCTION

    contents = [{"role": msg["role"], "parts": [{"text": msg["content"]}]} for msg in history[-HISTORY_LIMIT:]]
    contents.append({"role": "user", "parts": [{"text": user_input_to_use}]})

    try:
        response = await asyncio.to_thread(lambda: client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config={"temperature": 0.8, "max_output_tokens": 512, "system_instruction": instruction}
        ))
        answer = getattr(response, "text", "").strip() or "Phoebe hơi ngơ ngác chút... anh hỏi lại được không nè? (・・;)"
        history.append({"role": "user", "content": user_input_to_use})
        history.append({"role": "model", "content": answer})
        session["message_count"] += 1
        save_sessions()
        return answer
    except:
        return "⚠️ Gemini 2.0 Flash không phản hồi, thử lại sau nhé!"

# ========== STATUS ==========
status_list = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
activity_list = [discord.Game("💖 Trò chuyện cùng anh"), discord.Game("✨ Thả thính nhẹ nhàng"), discord.Game("🌸 An ủi tinh thần")]

@tasks.loop(minutes=10)
async def random_status():
    activity = discord.Game("💞 Flirt Mode ON") if flirt_enable else random.choice(activity_list)
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
        "https://files.catbox.moe/2474tj.png","https://files.catbox.moe/66v9vw.jpg","https://files.catbox.moe/ezqs00.jpg",
        "https://files.catbox.moe/yow35q.png","https://files.catbox.moe/pzbhdp.jpg","https://files.catbox.moe/lyklnj.jpg",
        "https://files.catbox.moe/i5sqkr.png","https://files.catbox.moe/jt184o.jpg","https://files.catbox.moe/9nq5kw.jpg",
        "https://files.catbox.moe/45tre3.webp","https://files.catbox.moe/2y17ot.png","https://files.catbox.moe/gg8pt0.jpg",
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

@tree.command(name="chat18plus", description="🔞 Bật/tắt Flirt Mode (chỉ Admin)")
@app_commands.default_permissions(manage_guild=True)
async def chat18plus(interaction: discord.Interaction, enable: bool):
    global flirt_enable
    flirt_enable = enable
    status = "BẬT 💞" if enable else "TẮT 🌸"
    await interaction.client.change_presence(activity=discord.Game(f"💞 Flirt Mode {status}"))
    embed = discord.Embed(
        title="💋 Dâm Mode",
        description=f"**Trạng thái:** {status}\n**Người thực hiện:** {interaction.user.mention}",
        color=discord.Color.pink() if enable else discord.Color.blurple()
    )
    embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
    embed.set_footer(text="Phoebe Xinh Đẹp • Powered by Gemini 💫")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ========== FLASK ==========
app = Flask(__name__)
@app.route("/")
def home(): return "<h3>Phoebe Xinh Đẹp đang hoạt động! 🌸</h3>"
@app.route("/healthz")
def healthz(): return {"status":"ok","message":"Phoebe khỏe mạnh nè~ 💖"},200
def run_flask(): app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
def keep_alive(): Thread(target=run_flask, daemon=True).start()

# ========== BOT EVENTS ==========
@bot.event
async def on_ready():
    print(f"✅ {BOT_NAME} đã sẵn sàng! Logged in as {bot.user}")
    load_sessions()
    random_status.start()
    if GUILD_ID: await tree.sync(guild=discord.Object(GUILD_ID))
    else: await tree.sync()

# ========== RUN ==========
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)