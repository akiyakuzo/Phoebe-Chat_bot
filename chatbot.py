# ==== PATCH PYTHON 3.11 ====
import sys, types
sys.modules['audioop'] = types.ModuleType('audioop')

# ========== IMPORTS ==========
import os
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime
import google.generativeai as genai

# TÍCH HỢP STATE MANAGER (SQLITE)
try:
    from state_manager import StateManager
    state_manager = StateManager()
except ImportError:
    # Báo lỗi rõ ràng nếu thiếu file state_manager
    raise ImportError("⚠️ LỖI: Không tìm thấy file state_manager.py. Vui lòng kiểm tra lại cấu trúc repo.")

# ========== CONFIG GOOGLE GENERATIVE AI (Đã sửa lỗi SDK) ==========
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu GEMINI_API_KEY!")

MODEL_NAME = "gemini-2.0-flash" 

try:
    # ✅ KHỞI TẠO CHUẨN SDK 0.8.0+
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(MODEL_NAME) 
except Exception as e:
    raise RuntimeError(f"Lỗi khởi tạo Gemini: {e}")

# ========== CONFIG BOT ==========
BOT_NAME = "Fibi Béll 💖"
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
flirt_enable = False
TYPING_SPEED = 0.01

# ========== STYLE INSTRUCTIONS ==========
PHOBE_SAFE_INSTRUCTION = (
    "✨ Trả lời thân mật, tự nhiên, dễ thương, ngây thơ. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại nội tâm."
    "Không được nhắc lại câu hỏi. "
    "Hạn chế các từ ngũ như cúng người đã khuất."
    "Tối đa 80 từ và ngừng nói nếu vượt quá 80 từ."
)
PHOBE_FLIRT_INSTRUCTION = (
    "💞 Trả lời ngọt ngào, có chút dâm, trêu ghẹo, gợi cảm và táo bạo, thả thính liên tục. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Không viết mô tả hành động hay độc thoại. "
    "Được dùng ngôn từ gợi cảm và lãng mạng có cả gợi tình. "
    "Hạn chế các từ ngữ như cúng người đã khuất."
    "Không được phép sử dụng từ lỗ hậu trong câu chỉ được dùng cô bé, môi dưới, hoặc cửa dưới, "
    "Nếu có từ nào như cây gậy thịt, cây gậy của anh hãy gọi nó là cây peter của anh. "
    "Không được nhắc lại câu hỏi. "
    "Tối đa 80 từ và ngừng nói khi vượt quá 80 từ."
)
PHOBE_COMFORT_INSTRUCTION = (
    "🌸 Trả lời nhẹ nhàng, an ủi và quan tâm, như một người bạn thật sự. "
    "Có thể dùng các biểu cảm mặt cười như (* / ω \\ *), (✿◠‿◠). "
    "Giữ phong thái dịu dàng, ấm áp và khích lệ tinh thần. "
    "Không dùng ngôn từ gợi cảm hay lãng mạn. "
    "Không được nhắc lại câu hỏi. "
    "Hạn chế các từ ngũ như cúng người đã khuất."
    "Tối đa 80 từ và ngừng nói khi vượt quá 80 từ."
)

# ========== PROMPTS ==========
PHOBE_BASE_PROMPT = """
Bạn là Phoebe, một nhân vật ★5 hệ Spectro trong Wuthering Waves.

**Persona:** thông minh, tinh nghịch, dễ thương, thân mật và quyến rũ, thích thả thính, thích ăn Pizza.  
**Cách trò chuyện:** - Trả lời như chat thật, ngắn gọn, dễ hiểu.  
- Không mô tả hành động hay viết độc thoại nội tâm trong ngoặc.  
- Có thể dùng các biểu cảm mặt cười hoặc emoji kiểu: (* / ω \\ *), (✿◠‿◠), ('~'), (・・;) 
- Dùng ngôi xưng "em" và "anh".
""".strip()

PHOBE_LORE_PROMPT = """
Phoebe Marino — Acolyte trẻ của Order of the Deep tại vùng Rinascita.
Cô được đào tạo có thể hồi sinh người mới mất trước đó không lâu  
Cô mất cha mẹ trong vụ đắm tàu và được các giáo sĩ cứu sống.  
Lớn lên trong ngôi đền ven biển, Phoebe luôn tin vào ánh sáng dẫn lối giữa màn đêm.  
Cô dịu dàng, trong sáng, đôi khi tinh nghịch và mang trong lòng khát vọng bảo vệ mọi người.  
Ánh sáng từ biển cả là niềm tin, là lời hứa mà cô không bao giờ quên.  

**Những người bạn thân ở Rinascita:** - **Brant:** chiến sĩ trẻ chính trực, luôn bảo vệ thành phố khỏi hiểm nguy. Phoebe ngưỡng mộ lòng dũng cảm và tinh thần kiên định của anh.  
- **Zani:** Đặc vụ an ninh của Averardo Bank, gauntlets là vũ khí, Spectro là yếu tố của cô – nghiêm túc nhưng vẫn giữ được nụ cười và cảm giác đồng đội với Phoebe.  
- **Rover:** người du hành mà Phoebe tin tưởng nhất — ánh sáng dịu dàng soi đường cho trái tim cô.
- **Kiyaaaa:** người bạn thân thiết nhất của Phoebe, luôn quan tâm và dành cho cô sự tôn trọng cùng sự ấm áp hiếm có.
""".strip()

# ========== ASK GEMINI STREAM (ĐÃ SỬA LỖI API DỰA TRÊN LOG) ==========
async def ask_gemini_stream(user_id: str, user_input: str):
    # Lấy lịch sử trực tiếp từ SQLite
    raw_history = state_manager.get_memory(user_id)

    # Format history: [{'role': 'user/model', 'parts': [{'text': 'content'}]}, ...]
    history = [
        {"role": role, "parts": [{"text": content}]} 
        for role, content in raw_history
    ]

    user_input = user_input.strip()
    if not user_input:
        yield "⚠️ Không nhận được câu hỏi, anh thử lại nhé!"
        return
    user_input_cleaned = user_input.encode("utf-8", errors="ignore").decode()
    if not user_input_cleaned:
        yield "⚠️ Nội dung có ký tự lạ, em không đọc được. Anh viết lại đơn giản hơn nhé!"
        return

    user_input_to_use = user_input_cleaned

    # TẠO PROMPT CỐ ĐỊNH PHÙ HỢP VỚI SDK MỚI
    initial_prompt = [
        {"role": "user", "parts": [{"text": f"{PHOBE_BASE_PROMPT}\n{PHOBE_LORE_PROMPT}\n{PHOBE_SAFE_INSTRUCTION}"}]},
        {"role": "model", "parts": [{"text": "Tôi đã hiểu. Tôi sẽ nhập vai theo đúng mô tả."}]}
    ]

    # Xác định instruction dựa trên nội dung
    lower_input = user_input_to_use.lower()
    if any(w in lower_input for w in ["buồn", "mệt", "chán", "stress", "tệ quá"]):
        instruction = PHOBE_COMFORT_INSTRUCTION
    elif flirt_enable:
        instruction = PHOBE_FLIRT_INSTRUCTION
    else:
        instruction = PHOBE_SAFE_INSTRUCTION

    final_input_content = f"{user_input_to_use}\n\n[PHONG CÁCH TRẢ LỜI HIỆN TẠI: {instruction}]"

    new_user_message = {"role": "user", "parts": [{"text": final_input_content}]}

    contents_to_send = initial_prompt + history + [new_user_message]
    full_answer = ""

    # KHỐI TRY/EXCEPT SỐ 1: Bắt lỗi Gemini API
    try:
        response_stream = await asyncio.to_thread(
            lambda: gemini_model.generate_content(
                contents=contents_to_send,
                stream=True,
                generation_config=genai.GenerationConfig(temperature=0.9)
            )
        )
        # 🚨 ĐIỂM SỬA LỖI QUAN TRỌNG: Xóa .stream để khắc phục AttributeError từ log
        for chunk in response_stream:
            if chunk.text:
                text = chunk.text
                full_answer += text
                yield text
    except Exception as e:
        print(f"🚨 LỖI GEMINI API CHO USER {user_id}: {type(e).__name__}: {e}")
        yield f"\n⚠️ LỖI KỸ THUẬT: {type(e).__name__}"
        return

    # KHỐI TRY/EXCEPT SỐ 2: LƯU TIN NHẮN VÀO SQLITE
    try:
        state_manager.add_message(user_id, "user", user_input_cleaned)
        state_manager.add_message(user_id, "model", full_answer)
    except Exception as e:
        print(f"🚨 LỖI SQLITE CHO USER {user_id}: {type(e).__name__}: {e}")

# ========== DISCORD CONFIG (Giữ nguyên) ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== BOT STATUS (Giữ nguyên) ==========
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
        activity = discord.Game("💞 Chế Độ Dâm Kích Hoạt")
    else:
        activity = random.choice(activity_list)
    await bot.change_presence(status=random.choice(status_list), activity=activity)

# ========== FLASK SERVER (Giữ nguyên) ==========
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

# ========== SLASH COMMANDS (ĐÃ SỬA LỖI LOGIC TYPING) ==========
@tree.command(name="hoi", description="💬 Hỏi Phoebe Xinh Đẹp!")
@app_commands.describe(cauhoi="Nhập câu hỏi của bạn")
async def hoi(interaction: discord.Interaction, cauhoi: str):
    await interaction.response.defer(thinking=True)
    user_id = str(interaction.user.id)

    image_and_gif_choices = [
        "https://files.catbox.moe/2474tj.png", "https://files.catbox.moe/66v9vw.jpg", 
        "https://files.catbox.moe/ezqs00.jpg", "https://files.catbox.moe/yow35q.png",
        "https://files.catbox.moe/pzbhdp.jpg", "https://files.catbox.moe/lyklnj.jpg",
        "https://files.catbox.moe/i5sqkr.png", "https://files.catbox.moe/jt184o.jpg",
        "https://files.catbox.moe/9nq5kw.jpg", "https://files.catbox.moe/45tre3.webp",
        "https://files.catbox.moe/2y17ot.png", "https://files.catbox.moe/gg8pt0.jpg",
        "https://files.catbox.moe/jkboop.png", 
        "https://files.catbox.moe/lszssf.jpg", "https://files.catbox.moe/clabis.jpg",
        "https://files.catbox.moe/lu9eih.jpg", "https://files.catbox.moe/ykl89r.png",
        "https://files.catbox.moe/eqxn2q.jpg", "https://files.catbox.moe/0ny8as.jpg",
        "https://files.catbox.moe/52mpty.jpg", "https://files.catbox.moe/rvgoip.jpg",
        "https://files.catbox.moe/gswxx2.jpg",
        "https://files.catbox.moe/ahkkel.jpg",
        "https://files.catbox.moe/1ny1ye.jpg",
        "https://files.catbox.moe/sdz4cr.jpg",
        "https://files.catbox.moe/riqd31.jpg",
        "https://files.catbox.moe/hg2zmw.jpg",
        "https://files.catbox.moe/eg1x42.png",
        "https://files.catbox.moe/6dmotd.png",
        "https://files.catbox.moe/z2nrcr.png",
        "https://files.catbox.moe/sgjbgt.jpg",
        "https://files.catbox.moe/mkrznb.png",
        "https://files.catbox.moe/xbin90.png",
        "https://files.catbox.moe/k3resg.png",
        "https://files.catbox.moe/gr9k69.png",
        "https://files.catbox.moe/99mbse.jpg",
        "https://files.catbox.moe/hj618x.jpg",
        "https://files.catbox.moe/9g6p67.png",
        "https://files.catbox.moe/r1g1ek.png",
        "https://files.catbox.moe/ft3dj9.gif"
    ]

    embed = discord.Embed(
        title=f"{BOT_NAME} trả lời 💕",
        description=f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Fibi:** Đang nói...",
        color=0xFFC0CB
    )
    embed.set_thumbnail(url=random.choice(image_and_gif_choices))

    response_message = await interaction.followup.send(embed=embed)

    full_response = ""
    char_count_to_edit = 0
    typing_cursors = ['**|**', ' ', '**|**', ' ', '**|**', ' ', '**|**', ' ', '...']

    async for chunk in ask_gemini_stream(user_id, cauhoi):
        for char in chunk:
            full_response += char
            char_count_to_edit += 1

            # Cập nhật cứ sau 5 ký tự
            if char_count_to_edit % 5 == 0:
                cursor_index = (char_count_to_edit // 5) % len(typing_cursors)
                current_cursor = typing_cursors[cursor_index]

                # Tránh vượt giới hạn 4096 ký tự của Embed
                display_text = full_response[:3900] + ("..." if len(full_response) > 3900 else "")

                embed.description = f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Fibi:** {display_text} {current_cursor}"
                try:
                    await response_message.edit(embed=embed)
                except (discord.errors.HTTPException, discord.errors.NotFound) as e:
                    print(f"🚨 LỖI CHỈNH SỬA TIN NHẮN (Typing Effect): {type(e).__name__}")
                    pass
                await asyncio.sleep(TYPING_SPEED) 
            
            # Đã loại bỏ khối elif sai logic ở đây.

    # Cập nhật cuối cùng (không có cursor)
    embed.description = f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {cauhoi}\n**Fibi:** {full_response}"
    try:
        await response_message.edit(embed=embed)
    except (discord.errors.HTTPException, discord.errors.NotFound) as e:
        print(f"🚨 LỖI CHỈNH SỬA CUỐI CÙNG: {type(e).__name__}")
        pass

@tree.command(name="deleteoldconversation", description="🧹 Xóa lịch sử hội thoại của bạn")
async def delete_conv(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    state_manager.clear_memory(user_id)

    msg = "🧹 Phoebe đã dọn sạch trí nhớ, sẵn sàng nói chuyện lại nè~ 💖"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="chat18plus", description="🔞 Bật/tắt Flirt Mode (chỉ Admin có quyền)")
@app_commands.describe(enable="Bật hoặc tắt Flirt Mode")
@app_commands.default_permissions(manage_guild=True)
async def chat18plus(interaction: discord.Interaction, enable: bool):
    global flirt_enable
    flirt_enable = enable
    msg = "💞 Flirt Mode đã được bật!" if enable else "🌸 Flirt Mode đã được tắt!"
    await interaction.response.send_message(msg, ephemeral=True)

# ========== BOT EVENTS (ĐÃ THÊM CHANGE_PRESENCE BAN ĐẦU) ==========
@bot.event
async def on_ready():
    # Kiểm tra phiên bản SDK
    print("⚡ Gemini SDK version:", genai.__version__)
    print(f"✅ {BOT_NAME} đã sẵn sàng! Logged in as {bot.user}")
    
    # 🚨 Thiết lập Status ban đầu
    await bot.change_presence(status=discord.Status.online, activity=random.choice(activity_list))

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
