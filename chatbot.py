# ==== PATCH PYTHON 3.11 (GIỮ NGUYÊN) ====
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

# === 1. TÍCH HỢP REPLICATE (MỚI) ===
try:
    import replicate
except ImportError:
    print("⚠️ Thiếu thư viện 'replicate'. Tính năng tạo ảnh sẽ bị tắt.")
    replicate = None

# TÍCH HỢP STATE MANAGER (SQLITE)
try:
    from state_manager import StateManager
    state_manager = StateManager()
except ImportError:
    raise ImportError("⚠️ LỖI: Không tìm thấy file state_manager.py. Vui lòng kiểm tra lại cấu trúc repo.")

# ========== CONFIG GOOGLE GENERATIVE AI ==========
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ Thiếu GEMINI_API_KEY!")

MODEL_NAME = "gemini-2.0-flash" 

try:
    # ✅ KHỞI TẠO CHUẨN SDK 0.8.0+
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(MODEL_NAME) 

    try:
        models = list(genai.list_models())
        print(f"✅ KIỂM TRA GEMINI API THÀNH CÔNG: Đã thấy {len(models)} mô hình.")
    except Exception as e:
        print(f"🚨🚨 LỖI NGHIÊM TRỌNG: GEMINI API KEY CÓ VẤN ĐỀ. Lỗi: {e}")
        raise RuntimeError(f"Lỗi xác thực/kết nối Gemini API: {e}")

except Exception as e:
    raise RuntimeError(f"Lỗi khởi tạo Gemini: {e}")

# === 2. CONFIG REPLICATE ===
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
ANIME_MODEL_ID = "littlemonsterzhang/wai90_sdxl:820ce2c86370ccfac38e9126bcffc58d23348a0ab06179c4b2f49c444ef2d0a6"


# ========== CONFIG BOT ==========
BOT_NAME = "Fibi Béll 💖"
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
flirt_enable_global = False 
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
    "Biết điểm dừng không đòi hỏi quá nhiều. "
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

# ========== REPLICATE IMAGE GENERATION (ĐÃ THÊM) ==========
async def generate_image_from_text(prompt: str, flirt_mode: bool = False):
    if not replicate or not REPLICATE_API_TOKEN:
        return None 

    # Xây dựng prompt cho Stable Diffusion
    base_prompt = "anime style, wuthering waves character, intricate detail, extremely high quality, best composition, professional illustration"
    
    if flirt_mode:
        style_prompt = "suggestive, very attractive, blush, skin details, hyper detailed, soft lighting, focus on body curve"
    else:
        style_prompt = "wholesome, soft shading, gentle colors, full body, beautiful face"

    final_prompt = f"{style_prompt}, {prompt}, {base_prompt}"
    
    # Negative prompt
    negative_prompt = "ugly, deformed, bad anatomy, deformed face, disfigured, poor detailing, blurry, low res, low quality, NSFW, naked"

    # Gọi Replicate API
    print(f"DEBUG_REPLICATE: Gửi prompt: {final_prompt[:80]}...")
    
    output = await asyncio.to_thread(
        lambda: replicate.run(
            ANIME_MODEL_ID,
            input={
                "prompt": final_prompt,
                "negative_prompt": negative_prompt,
                "width": 768,
                "height": 1024,
                "num_outputs": 1,
                "lora_scale": 0.8
            }
        )
    )
    
    if output and isinstance(output, list) and output[0]:
        return output[0]
    return None


# ========== ASK GEMINI STREAM (Đã cập nhật cho SDK 0.8.0+) ==========
async def ask_gemini_stream(user_id: str, user_input: str):
    raw_history = state_manager.get_memory(user_id)

    # Format history cho SDK 0.8.0+
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
    full_answer = ""

    # TẠO SYSTEM INSTRUCTION KẾT HỢP
    base_instruction = f"{PHOBE_BASE_PROMPT}\n{PHOBE_LORE_PROMPT}"
    lower_input = user_input_to_use.lower()
    global flirt_enable_global 

    if any(w in lower_input for w in ["buồn", "mệt", "chán", "stress", "tệ quá"]):
        instruction = PHOBE_COMFORT_INSTRUCTION
    elif flirt_enable_global:
        instruction = PHOBE_FLIRT_INSTRUCTION
    else:
        instruction = PHOBE_SAFE_INSTRUCTION

    final_system_instruction = f"{base_instruction}\n\n{instruction}"

    # Thêm câu hỏi hiện tại vào lịch sử để gửi đi
    new_user_message = {"role": "user", "parts": [{"text": user_input_to_use}]}
    contents_to_send = history + [new_user_message]

    # KHỐI TRY/EXCEPT SỐ 1: Bắt lỗi Gemini API
    try:
        response_stream = await asyncio.to_thread(
            lambda: gemini_model.generate_content(
                contents=contents_to_send,
                stream=True,
                config=genai.GenerationConfig(
                    temperature=1.0,
                    system_instruction=final_system_instruction 
                )
            )
        )
        for chunk in response_stream:
            if chunk.text:
                text = chunk.text
                full_answer += text
                yield text
    except Exception as e:
        print(f"🚨 LỖI GEMINI API CHO USER {user_id}: {type(e).__name__}: {e}")
        yield f"\n⚠️ LỖỖI KỸ THUẬT: {type(e).__name__}"
        return

    # KHỐI TRY/EXCEPT SỐ 2: LƯU TIN NHẮN VÀO SQLITE
    try:
        state_manager.add_message(user_id, "user", user_input_cleaned)
        state_manager.add_message(user_id, "model", full_answer)
    except Exception as e:
        print(f"🚨 LỖI SQLITE CHO USER {user_id}: {type(e).__name__}: {e}")

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
    global flirt_enable_global
    if flirt_enable_global:
        activity = discord.Game("💞 Chế Độ Dâm Kích Hoạt")
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

# ========== SLASH COMMANDS (ĐÃ SỬA LỖI DEFER VÀ TRÙNG LẶP) ==========

@bot.tree.command(name="hoi", description="Hỏi Fibi bất cứ điều gì!")
async def hoi_command(interaction: discord.Interaction, prompt: str):
    print(f"DEBUG_START_HOI: Nhận lệnh /hoi từ {interaction.user.name} với prompt: {prompt[:30]}...") 
    user_id = str(interaction.user.id)

    global flirt_enable_global, BOT_NAME, TYPING_SPEED 
    current_flirt_enable = flirt_enable_global

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
    thumbnail_url = random.choice(image_and_gif_choices)

    # 1. GỬI LỆNH DEFER ĐỂ TRÁNH DISCORD TIMEOUT (RẤT QUAN TRỌNG)
    try:
        await interaction.response.defer(thinking=True)
    except Exception as e:
        print(f"🚨 LỖI DEFER: {e}")
        return

    embed = discord.Embed(
        title=f"{BOT_NAME} trả lời 💕",
        description=f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {prompt}\n**Fibi:** Đang nói...",
        color=0xFFC0CB
    )
    embed.set_thumbnail(url=thumbnail_url)

    # 2. GỬI TIN NHẮN THEO DÕI
    try:
        response_message = await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"🚨 LỖI FOLLOWUP.SEND: {e}")
        return

    full_response = ""
    char_count_to_edit = 0
    typing_cursors = ['**|**', ' ', '**|**', ' ', '...'] 

    # 3. LẤY VÀ HIỂN THỊ CÂU TRẢ LỜI (STREAM)
    try:
        async for chunk in ask_gemini_stream(user_id, prompt): 
            for char in chunk:
                full_response += char
                char_count_to_edit += 1

                # Cập nhật tin nhắn 5 ký tự một lần
                if char_count_to_edit % 5 == 0:
                    cursor_index = (char_count_to_edit // 5) % len(typing_cursors)
                    current_cursor = typing_cursors[cursor_index]

                    display_text = full_response[:3900] + ("..." if len(full_response) > 3900 else "")
                    embed.description = f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {prompt}\n**Fibi:** {display_text} {current_cursor}" 
                    try:
                        await response_message.edit(embed=embed)
                    except (discord.errors.HTTPException, discord.errors.NotFound):
                        pass
                    await asyncio.sleep(TYPING_SPEED) 

        if not full_response:
            full_response = "❌ LỖI GEMINI API NGHIÊM TRỌNG: API key có thể bị khóa (403 Forbidden) hoặc có lỗi kết nối."

    except Exception as e:
        full_response = f"⚠️ LỖI CHAT API: {type(e).__name__} - Vui lòng kiểm tra Log Render để biết thêm chi tiết!"
        print(f"🚨🚨 LỖI GEMINI CHÍNH: {type(e).__name__} - {e}")

    # 4. LOGIC TẠO VÀ GẮN ẢNH
    generated_image_url = None
    if ("vẽ" in prompt.lower() or "ảnh" in prompt.lower() or "image" in prompt.lower() or "draw" in prompt.lower()) and replicate:
        print("DEBUG: Kích hoạt tạo ảnh.")

        embed.description = f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {prompt}\n**Fibi:** {full_response}\n\n*Phoebe đang vẽ một bức tranh đẹp cho anh nè... 🎨 (Đang gọi Stable Diffusion API)*"
        try:
            await response_message.edit(embed=embed)
        except:
            pass

        try:
            image_context = f"Question: {prompt}. Answer: {full_response[:int(len(full_response)*0.8)]}" 
            generated_image_url = await generate_image_from_text(image_context, current_flirt_enable)
        except Exception as e:
            print(f"🚨🚨 LỖI REPLICATE CHÍNH: {type(e).__name__} - {e}")
            full_response += "\n\n**[LỖI TẠO ẢNH: Vui lòng kiểm tra Log Render]**"


    # 5. CẬP NHẬT CUỐI CÙNG
    embed.description = f"**Người hỏi:** {interaction.user.mention}\n**Câu hỏi:** {prompt}\n**Fibi:** {full_response}" 

    if generated_image_url:
        embed.set_image(url=generated_image_url)
        embed.set_thumbnail(url=thumbnail_url) 

    try:
        await response_message.edit(embed=embed)
    except (discord.errors.HTTPException, discord.errors.NotFound) as e:
        print(f"🚨 LỖI CHỈNH SỬA CUỐI CÙNG: {type(e).__name__}")
        pass

# 🚨 CHỈ GIỮ LẠI MỘT LẦN ĐỊNH NGHĨA LỆNH CHAT18PLUS NÀY
@bot.tree.command(name="chat18plus", description="🔞 Bật/tắt Flirt Mode (chỉ Admin có quyền)")
@app_commands.describe(enable="Bật hoặc tắt Flirt Mode")
@app_commands.default_permissions(administrator=True) 
async def flirt_mode_command(interaction: discord.Interaction, enable: bool):
    global flirt_enable_global

    # Đảm bảo lệnh không bị timeout
    await interaction.response.defer(ephemeral=True, thinking=True)
    
    flirt_enable_global = enable
    if enable:
        msg = "💞 Chế Độ **Flirt Mode (18+)** đã được kích hoạt! Phoebe giờ sẽ siêu táo bạo đấy~"
        # Đảm bảo bot thay đổi status ngay lập tức
        await bot.change_presence(activity=discord.Game("💞 Chế Độ Dâm Kích Hoạt"))
    else:
        msg = "🌸 Chế Độ **Bình Thường** đã được kích hoạt. Phoebe sẽ lại ngoan ngoãn nè~"
        # Trả lại trạng thái ngẫu nhiên ngay lập tức
        await random_status() 

    await interaction.followup.send(msg, ephemeral=True)

# ========== EVENT HANDLERS VÀ KHỞI CHẠY BOT (CẦN THIẾT) ==========

@bot.event
async def on_ready():
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild)
        print(f"✅ Đã đồng bộ lệnh Slash cho Guild ID: {GUILD_ID}")
    else:
        await bot.tree.sync()
        print("✅ Đã đồng bộ lệnh Slash toàn cục.")

    print(f"💫 Bắt đầu Phoebe Xinh Đẹp: {bot.user.name} (ID: {bot.user.id})")

    if not random_status.is_running():
        random_status.start()

# RUN BOT VÀ FLASK
if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("⚠️ Thiếu TOKEN! Vui lòng kiểm tra biến môi trường DISCORD_TOKEN.")

    # Bắt đầu Flask server
    keep_alive()

    # Bắt đầu Discord bot
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"🚨 LỖI KHỞI CHẠY DISCORD BOT: {e}")