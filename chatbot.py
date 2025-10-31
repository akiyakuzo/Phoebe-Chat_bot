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

# ✅ Chuẩn SDK 0.3.0
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# ========== CONFIG BOT ==========
BOT_NAME = "Fibi Béll 💖"
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
HISTORY_LIMIT = 20
SESSIONS_FILE = "sessions.json"
flirt_enable = False
active_chats = {}

# ========== STYLE INSTRUCTIONS (Giữ nguyên) ==========
PHOBE_SAFE_INSTRUCTION = (
    "✨ Trả lời thân mật, tự nhiên, dễ thương. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại nội tâm. "
    "Tối đa 120 từ."
)

PHOBE_FLIRT_INSTRUCTION = (
    "💞 Trả lời ngọt ngào, trêu ghẹo, gợi cảm và táo bạo, thả thính liên tục. "
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

# ========== PROMPTS (Giữ nguyên) ==========
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
""".strip()

# ========== DISCORD CONFIG ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== SESSION SYSTEM ==========
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
            {"role": "model", "content": "Em đây, anh muốn hỏi gì nè? (* / ω \\ *)"}
        ]
        active_chats[user_id] = {"history": initial, "message_count": 0, "created_at": str(datetime.now())}
    return active_chats[user_id]

# ========== ASK GEMINI (STREAMING) ==========
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
        print(f"⚠️ Reset history user {user_id}")
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
        # ✅ DÙNG generate_content_stream CHUẨN SDK 0.3.0
        response_stream = await asyncio.to_thread(
            lambda: genai.models.generate_content_stream(
                model=MODEL_NAME,
                contents=contents_to_send,
                temperature=0.8
            )
        )
        for chunk in response_stream:
            if chunk.text:
                text = chunk.text
                full_answer += text
                yield text
                
    except Exception as e:
        error_type = type(e).__name__
        print(f"❌ Lỗi Gemini: {error_type} - {e}")
        yield f"\n\n⚠️ Gemini đang lỗi: {error_type} - {str(e)[:60]}..."
        return # Ngừng stream khi có lỗi

    # 💾 Lưu lịch sử sau khi stream xong
    history.append({"role": "user", "content": user_input_to_use})
    history.append({"role": "model", "content": full_answer}) 
    session["message_count"] += 1
    save_sessions()

# ========== STATUS LOOP ==========
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
        activity = discord.Game("💞 Phoebe Quyến Rũ ON")
    else:
        activity = random.choice(activity_list)
    await bot.change_presence(status=random.choice(status_list), activity=activity)

# ========== SLASH COMMANDS (Cập nhật cho Streaming) ==========
@tree.command(name="hoi", description="💬 Hỏi Phoebe Xinh Đẹp!")
async def hoi(interaction: discord.Interaction, cauhoi: str):
    # Trì hoãn phản hồi để có thời gian stream
    await interaction.response.defer(thinking=True)
    user_id = str(interaction.user.id)
    
    # Khởi tạo embed ban đầu
    embed = discord.Embed(
        title=f"{BOT_NAME} trả lời 💕",
        description=f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Phobe:** Đang gõ...",
        color=0xFFC0CB
    )
    embed.set_thumbnail(url=random.choice([
        "https://files.catbox.moe/2474tj.png","https://files.catbox.moe/66v9vw.jpg",
        "https://files.catbox.moe/ezqs00.jpg","https://files.catbox.moe/yow35q.png",
        "https://files.catbox.moe/pzbhdp.jpg","https://files.catbox.moe/lyklnj.jpg",
        "https://files.catbox.moe/i5sqkr.png","https://files.catbox.moe/jt184o.jpg",
        "https://files.catbox.moe/9nq5kw.jpg","https://files.catbox.moe/45tre3.webp",
        "https://files.catbox.moe/2y17ot.png","https://files.catbox.moe/gg8pt0.jpg",
        "https://files.catbox.moe/jkboop.png"
    ]))
    
    # Gửi tin nhắn ban đầu và lưu tham chiếu
    response_message = await interaction.followup.send(embed=embed)
    
    full_response = ""
    chunk_count = 0
    async for chunk in ask_gemini_stream(user_id, cauhoi):
        full_response += chunk
        chunk_count += 1
        
        # Cập nhật embed sau mỗi 5 chunk hoặc khi hoàn tất chunk đầu tiên
        if chunk_count % 5 == 0 or chunk_count == 1:
            # Tránh lỗi Discord max length (2000 ký tự cho tin nhắn thường, 4096 cho embed)
            display_text = full_response
            if len(full_response) > 3900:
                display_text = full_response[:3900] + "..."

            # Cập nhật embed
            embed.description = f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Phobe:** {display_text}"
            await response_message.edit(embed=embed)

    # Gửi kết quả cuối cùng (đã lưu lịch sử)
    embed.description = f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Phobe:** {full_response}"
    await response_message.edit(embed=embed)

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
@app_commands.default_permissions(manage_guild=True)
async def chat18plus(interaction: discord.Interaction, enable: bool):
    global flirt_enable
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "❌ Lệnh này chỉ dùng được trong server, không phải tin nhắn riêng nha~ 💌",
            ephemeral=True
        )
        return
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ Anh không có quyền **Quản lý máy chủ** để bật/tắt Flirt Mode đâu nè~ 🥺",
            ephemeral=True
        )
        return
    flirt_enable = enable
    status = "BẬT 💞" if enable else "TẮT 🌸"
    new_activity = discord.Game(f"💞 Flirt Mode {status}")
    await interaction.client.change_presence(activity=new_activity)
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
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

def keep_alive():
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
    keep_alive()
    bot.run(TOKEN)