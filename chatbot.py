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

# === 1. TÍCH HỢP REPLICATE (MỚI) ===
try:
    import replicate
except ImportError:
    # Nếu thiếu thư viện, in cảnh báo nhưng không lỗi
    print("⚠️ Thiếu thư viện 'replicate'. Tính năng tạo ảnh sẽ bị tắt.")
    replicate = None

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
    
    # 🚨 BƯỚC MỚI: KIỂM TRA API KEY NGAY LẬP TỨC
    try:
        # Thử gọi một API đơn giản để xác nhận key hợp lệ
        models = list(genai.list_models())
        print(f"✅ KIỂM TRA GEMINI API THÀNH CÔNG: Đã thấy {len(models)} mô hình.")
    except Exception as e:
        # Nếu API Key sai/bị khóa, lỗi sẽ xuất hiện TẠY ĐÂY!
        print(f"🚨🚨 LỖI NGHIÊM TRỌNG: GEMINI API KEY CÓ VẤN ĐỀ. Lỗi: {e}")
        raise RuntimeError(f"Lỗi xác thực/kết nối Gemini API: {e}")

except Exception as e:
    raise RuntimeError(f"Lỗi khởi tạo Gemini: {e}")

# === 2. CONFIG REPLICATE (ĐÃ CẬP NHẬT MODEL ID) ===
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
# ID Mô hình Anime mới (littlemonsterzhang/wai90_sdxl)
ANIME_MODEL_ID = "littlemonsterzhang/wai90_sdxl:820ce2c86370ccfac38e9126bcffc58d23348a0ab06179c4b2f49c444ef2d0a6"


# ========== CONFIG BOT ==========
BOT_NAME = "Fibi Béll 💖"
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
# Đặt flirt_enable là global để truy cập dễ hơn trong các hàm
flirt_enable_global = False 
TYPING_SPEED = 0.01

# ========== STYLE INSTRUCTIONS (Giữ nguyên) ==========
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

# ========== PROMPTS (Giữ nguyên) ==========
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

# ========== HÀM GỌI REPLICATE API (ĐÃ TỐI ƯU TOÀN DIỆN) ==========
async def generate_image_from_text(image_prompt: str, is_flirt_mode: bool) -> str | None:
    if not REPLICATE_API_TOKEN or not replicate:
        print("⚠️ LỖI: Thiếu REPLICATE_API_TOKEN hoặc thư viện replicate. Bỏ qua tạo ảnh.")
        return None

    try:
        model = ANIME_MODEL_ID 
        
        # --- BASE PROMPT: Mô tả chi tiết Phoebe (Tối ưu theo ảnh gốc) ---
        base_subject = (
            "Wuthering Waves Phoebe, official art, solo, 1girl, highly detailed, "
            "long blonde hair, wavy hair, purple eyes, pale skin, "
            "white wide-brimmed hat, blue and white dress, white high boots, "
            "blue mantle, gold accents, holding scepter, dynamic angle, "
            "masterpiece, best quality, amazing quality," 
        )
        
        # Từ khóa chung cho phong cách (Dựa trên Model ID mới)
        shared_style_tags = "chinese clothes, tassel, chinese knot, draped silk, gold trim, wind, bokeh, scattered leaves, waterfall, splashed water, looking at viewer"
        
        # --- LOGIC PHÂN LOẠI SAFE / FLIRT ---
        if is_flirt_mode:
            # === CHẾ ĐỘ GỢI CẢM (NSFW/18+) ===
            # Thay đổi trang phục và tư thế sang gợi cảm
            flirt_style = (
                "large_breasts, (upper_body,close-up:1.4), seductive pose, "
                "bare shoulders, transparent clothes, "
                "half-closed eyes, blush, wet clothes, implied nudity, **remove hat**, **remove mantle**,"
            )
            final_prompt = f"{base_subject} {flirt_style} {shared_style_tags} {image_prompt}"

            # Negative Prompt rất mạnh mẽ (từ ví dụ của anh + cấm thô tục)
            negative_prompt = (
                "bad quality, worst quality, worst detail, sketch, censor, "
                "blurry, extra limbs, bad anatomy, deformed, signature, "
                "nipples, genitals, child, loli, lowres, monochrome, ugly"
            )
            width_img = 768
            height_img = 1024 

        else:
            # === CHẾ ĐỘ BÌNH THƯỜNG (SAFE/CUTE) ===
            # Trang phục kín đáo, phong cách dễ thương
            safe_style = "cute and innocent, casual pose, happy expression, bright lighting, outdoor background, full body shot,"
            final_prompt = f"{base_subject} {safe_style} {shared_style_tags} {image_prompt}"

            # Negative Prompt cho Safe Mode
            negative_prompt = (
                "bad quality, worst quality, worst detail, sketch, censor, "
                "blurry, extra limbs, bad anatomy, deformed, signature, "
                "cleavage, seductive, nude, explicit, lewd, lowres, monochrome, ugly"
            )
            width_img = 1024
            height_img = 768 

        print(f"DEBUG: FINAL IMAGE PROMPT: {final_prompt[:100]}...")

        # Gọi API Replicate trong một luồng riêng để không chặn Discord
        output = await asyncio.to_thread(
            lambda: replicate.run(
                model,
                input={
                    "prompt": final_prompt,
                    "width": width_img,
                    "height": height_img,
                    "num_outputs": 1,
                    "negative_prompt": negative_prompt
                }
            )
        )
        
        # Trả về URL
        if output and isinstance(output, list) and len(output) > 0:
            # Lấy URL từ đối tượng file của Replicate
            return output[0].url
        return None

    except Exception as e:
        print(f"🚨 LỖI REPLICATE API: {e}")
        return None

# ========== ASK GEMINI STREAM (Giữ nguyên) ==========
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
    global flirt_enable_global # Cập nhật sử dụng biến global
    if any(w in lower_input for w in ["buồn", "mệt", "chán", "stress", "tệ quá"]):
        instruction = PHOBE_COMFORT_INSTRUCTION
    elif flirt_enable_global:
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
    global flirt_enable_global # Dùng biến global
    if flirt_enable_global:
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

# ========== SLASH COMMANDS (ĐÃ SỬA LỖI NAME ERROR & DEFER) ==========
@bot.tree.command(name="hoi", description="Hỏi Fibi bất cứ điều gì!")
async def hoi_command(interaction: discord.Interaction, prompt: str):
    # 🚨 DEBUG LOG
    print(f"DEBUG_START_HOI: Nhận lệnh /hoi từ {interaction.user.name} với prompt: {prompt[:30]}...") 
    user_id = str(interaction.user.id)

    # Lấy trạng thái flirt_enable_global và BOT_NAME
    global flirt_enable_global, BOT_NAME, TYPING_SPEED 
    current_flirt_enable = flirt_enable_global

    image_and_gif_choices = [
        # ... (Danh sách URL ảnh/GIF giữ nguyên) ...
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

@bot.tree.command(name="deleteoldconversation", description="🧹 Xóa lịch sử hội thoại của bạn")
async def delete_conv(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    state_manager.clear_memory(user_id)

    msg = "🧹 Phoebe đã dọn sạch trí nhớ, sẵn sàng nói chuyện lại nè~ 💖"
    await interaction.response.send_message(msg, ephemeral=True)

# ⚠️ SỬA LỖI CẮT CODE TẠI ĐÂY - THÊM PHẦN CÒN THIẾU CỦA HÀM NÀY
@bot.tree.command(name="chat18plus", description="🔞 Bật/tắt Flirt Mode (chỉ Admin có quyền)")
@app_commands.describe(enable="Bật hoặc tắt Flirt Mode")
@app_commands.default_permissions(administrator=True) # Chỉ Admin mới có quyền
async def flirt_mode_command(interaction: discord.Interaction, enable: bool):
    global flirt_enable_global
    
    # Kiểm tra quyền Admin (Discord tự động kiểm tra, nhưng thêm check code cho chắc)
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Anh không phải Admin, em không thể làm theo lệnh này~", ephemeral=True)
        return

    flirt_enable_global = enable
    if enable:
        msg = "💞 Chế Độ **Flirt Mode (18+)** đã được kích hoạt! Phoebe giờ sẽ siêu táo bạo đấy~"
        await bot.change_presence(activity=discord.Game("💞 Chế Độ Dâm Kích Hoạt"))
    else:
        msg = "🌸 Chế Độ **Bình Thường** đã được kích hoạt. Phoebe sẽ lại ngoan ngoãn nè~"
        # Trả lại trạng thái ngẫu nhiên ngay lập tức
        await random_status() 

    await interaction.response.send_message(msg, ephemeral=True)

# ========== EVENT HANDLERS VÀ KHỞI CHẠY BOT (CẦN THIẾT) ==========

# ĐỒNG BỘ LỆNH SAU KHI BOT KẾT NỐI
@bot.event
async def on_ready():
    # Kiểm tra xem có Guild ID (Server ID) được config không
    if GUILD_ID:
        # Đồng bộ lệnh cho Server cụ thể (nhanh hơn)
        guild = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild)
        print(f"✅ Đã đồng bộ lệnh Slash cho Guild ID: {GUILD_ID}")
    else:
        # Đồng bộ toàn cục (chậm hơn, có thể mất đến 1 giờ)
        await bot.tree.sync()
        print("✅ Đã đồng bộ lệnh Slash toàn cục.")

    print(f"💫 Bắt đầu Phoebe Xinh Đẹp: {bot.user.name} (ID: {bot.user.id})")

    # Khởi chạy status loop
    if not random_status.is_running():
        random_status.start()

# ========== RUN BOT ==========
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)