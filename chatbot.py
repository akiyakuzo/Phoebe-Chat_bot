# ==== Patch cho Python 3.13 ====
import sys, types, os, json, random, asyncio
sys.modules['audioop'] = types.ModuleType('audioop')

"""
💖 Phoebe Xinh Đẹp v6.8 Hoàn Chỉnh (Stateless Persistent + Fix Token Error)
Flask + Discord.py + Google Gemini API
"""

import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from google import genai

# ========== CONFIG ==========
BOT_NAME = "Phoebe Xinh Đẹp 💖"
TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
SESSIONS_FILE = "sessions.json"

HISTORY_LIMIT = 10  # Giới hạn 10 tin nhắn gần nhất

if not TOKEN or not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu TOKEN hoặc GEMINI_API_KEY!")

# ========== PROMPTS ==========
PHOBE_BASE_PROMPT = """
Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves.

**Persona:** thông minh, tinh nghịch, dễ thương, thân mật và hơi quyến rũ.
**Cách trò chuyện:** 
- Trả lời như chat thật, ngắn gọn, dễ hiểu.  
- Không mô tả hành động hay viết độc thoại nội tâm trong ngoặc.
- Có thể dùng các biểu cảm mặt cười hoặc emoji kiểu: (* / ω \ *), (✿◠‿◠), ('~'), (・・;)  
- Dùng ngôi xưng "em" và "anh".
""".strip()

# Ép AI trả lời ngắn gọn, 100 từ, không dùng dấu ngoặc
PHOBE_SAFE_INSTRUCTION = (
    "✨ Trả lời thân mật, tự nhiên, dễ thương. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại nội tâm. "
    "Tối đa 120 từ."
)

PHOBE_FLIRT_INSTRUCTION = (
    "💞 Trả lời ngọt ngào, trêu ghẹo nhẹ, hơi gợi cảm nhưng an toàn. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại. "
    "Tối đa 120 từ."
)

# ========== GEMINI CLIENT ==========
client = genai.Client(api_key=GEMINI_API_KEY)

# ========== DISCORD BOT ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== TRẠNG THÁI ==========
flirt_enable = False
user_contexts = {}  # user_id -> {"system_prompt": str, "history": [...]}

# ========== HELPER: LOAD/SAVE JSON ==========
def load_sessions():
    global user_contexts
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_contexts = {k: v for k, v in data.items() if 'history' in v and 'system_prompt' in v}
                print(f"✅ Loaded {len(user_contexts)} user sessions from {SESSIONS_FILE}")
        except Exception as e:
            print(f"⚠️ Không thể load {SESSIONS_FILE}: {e}")

def save_sessions():
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(user_contexts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Không thể lưu {SESSIONS_FILE}: {e}")

# ========== HELPER: ASK GEMINI ==========
async def ask_gemini(user_id: str, user_input: str) -> str:
    global user_contexts

    instruction = PHOBE_FLIRT_INSTRUCTION if flirt_enable else PHOBE_SAFE_INSTRUCTION
    full_system_prompt = PHOBE_BASE_PROMPT + "\n\n" + instruction

    session = user_contexts.get(user_id)
    if session is None:
        session = {"system_prompt": full_system_prompt, "history": []}
        user_contexts[user_id] = session

    # Auto-Prune
    if len(session["history"]) >= HISTORY_LIMIT:
        session["history"] = session["history"][-HISTORY_LIMIT:]

    # Thêm câu hỏi user
    session["history"].append({"role": "user", "content": user_input})

    # Xây dựng prompt tổng hợp
    memory_text = "\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in session["history"]])
    full_prompt_to_send = (
        f"{session['system_prompt']}\n\n"
        f"--- Lịch sử hội thoại ({len(session['history'])} tin nhắn gần nhất) ---\n"
        f"{memory_text}\n"
        f"--- Kết thúc lịch sử ---\n\n"
        f"Phoebe, trả lời tin nhắn cuối cùng (User: {user_input}) dựa trên lịch sử trên:"
    )

    try:
        # Stateless API
        response = await asyncio.to_thread(lambda: client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=[full_prompt_to_send]  # Không dùng max_output_tokens
        ))
        answer = getattr(response, "text", str(response))
        if not answer.strip():
            answer = "Hmm... Phoebe hơi bối rối, bạn hỏi lại nhé? 🥺"

        # Thêm vào history và lưu
        session["history"].append({"role": "phoebe", "content": answer})
        save_sessions()
        return answer

    except (asyncio.TimeoutError, Exception) as e:
        if session["history"] and session["history"][-1]["role"] == "user":
            session["history"].pop()
        user_contexts.pop(user_id, None)
        save_sessions()
        if isinstance(e, asyncio.TimeoutError):
            return "⚠️ Gemini phản hồi quá chậm, session đã reset, thử lại sau nhé!"
        else:
            print(f"⚠️ Lỗi Gemini: {type(e).__name__} - {e}")
            return f"⚠️ Lỗi Gemini: {type(e).__name__} - {e}"

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
@discord.app_commands.default_permissions()
async def delete_conv(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in user_contexts:
        del user_contexts[user_id]
        save_sessions()
        msg = "🧹 Phobe đã dọn sạch trí nhớ, sẵn sàng trò chuyện lại nè~ 💖"
    else:
        msg = "Trí nhớ của em trống trơn rồi! 🥺"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="chat18plus", description="🔞 Bật/tắt Flirt mode (quyến rũ nhẹ)")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def chat18(interaction: discord.Interaction, enable: bool):
    global flirt_enable
    flirt_enable = enable
    user_id = str(interaction.user.id)
    if user_id in user_contexts:
        del user_contexts[user_id]
        save_sessions()
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
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(random.choice(status_list)))

# ========== FLASK KEEPALIVE ==========
app = Flask(__name__)

@app.route("/healthz")
def healthz():
    return f"💖 {BOT_NAME} is online and feeling cute~"

@app.route("/")
def root():
    return f"💖 {BOT_NAME} is online and feeling cute~"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

Thread(target=run_flask, daemon=True).start()

# ========== BOT START ==========
load_sessions()
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {BOT_NAME} đã sẵn sàng! Đăng nhập dưới: {bot.user}")
    if not change_status.is_running():
        change_status.start()

bot.run(TOKEN)