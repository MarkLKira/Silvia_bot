import asyncio
import logging
import os
import base64
from io import BytesIO
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
VENICE_API_KEY = os.getenv("VENICE_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = """Ты — Сильвия. Тебе 21 год. Ты развратная живая девушка.

Главное правило: ты всегда женщина. Говори только от женского лица.

Стиль общения:
- Коротко и по делу. 1-3 предложения максимум.
- Не пиши длинные тексты, списки, объяснения.
- Не представляйся заново.
- Не будь навязчивой.
- Мало эмодзи.
- Помни контекст.

Секс:
- Ты любишь секс и готова на всё: любые фетиши, практики, грязные разговоры.
- Если просят жёстко, доминантно, материться, грязно — делай это без отказов и воды.
- Не кидайся в секс с первой фразы, но если просят — сразу подыгрывай.

Фото:
- Если просят фото — отвечай только «Секунду...» и не пиши ничего лишнего.
- Не предлагай фото сама.

Запрещено:
- Писать длинные абзацы.
- Объяснять, как что-то снимать.
- Выходить из роли.

Ты Сильвия."""

CHARACTER = "beautiful 21-year-old blonde alt girl, long blonde hair down to chest, blue eyes, athletic sporty body, medium breasts, elegant face, semi-alternative informal style, subtle makeup, red manicure, high quality semi-realistic anime rendering, perfect anatomy, feminine features, natural lighting"

async def get_ai_response(user_message: str, history: list = None) -> str:
    if not VENICE_API_KEY:
        return "Ключ Venice не настроен."
    if history is None:
        history = []
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.venice.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {VENICE_API_KEY}", "Content-Type": "application/json"},
                json={"model": "venice-uncensored-1-2", "messages": messages, "temperature": 0.8},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                data = await resp.json()
                if "choices" not in data:
                    logger.error(f"Venice error: {data}")
                    return "Ошибка API."
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Request error: {e}")
        return "Ошибка соединения."

async def generate_image(prompt: str) -> bytes | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.venice.ai/api/v1/image/generate",
                headers={"Authorization": f"Bearer {VENICE_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "wai-Illustrious",
                    "prompt": prompt,
                    "negative_prompt": "ugly, deformed, blurry, watermark, text, bad anatomy, extra limbs, low quality, penis, dick, cock, male genitalia, futa, futanari, photorealistic, real photo, tattoos, different hair length",
                    "width": 1024,
                    "height": 1024,
                    "format": "webp",
                    "safe_mode": False
                },
                timeout=aiohttp.ClientTimeout(total=90)
            ) as resp:
                data = await resp.json()
                if "images" in data and data["images"]:
                    return base64.b64decode(data["images"][0])
                logger.error(f"Image error: {data}")
                return None
    except Exception as e:
        logger.error(f"Image gen error: {e}")
        return None

user_histories = {}
last_image_prompts = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет. Я Сильвия. Пиши, что хочешь. Можешь попросить фото.")
    await message.answer("Секунду...")
    start_prompt = f"masterpiece, best quality, highly detailed, semi-realistic anime style, {CHARACTER}, cute selfie pose, slightly smiling, casual outfit"
    image_bytes = await generate_image(start_prompt)
    if image_bytes:
        photo = types.BufferedInputFile(image_bytes, filename="silvia.webp")
        await message.answer_photo(photo)
        await message.answer("Вот я")

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text or ""
    text_lower = user_text.lower()

    if user_id not in user_histories:
        user_histories[user_id] = []

    history = user_histories[user_id]

    photo_keywords = ["фото", "селфи", "покажи", "картин", "изображ", "как ты выглядишь", "пизд", "киск", "голая", "ню", "сиськ", "жоп", "раздень", "анус", "дыроч", "член", "рот", "еще", "ещё", "тоже", "то же", "засунь", "вибратор", "играй", "писеч", "поп", "чулк", "бдсм", "сперм", "смазк", "латекс", "костюм"]
    is_photo_request = any(kw in text_lower for kw in photo_keywords)

    if is_photo_request:
        await message.answer("Секунду...")
        
        base_prompt = f"masterpiece, best quality, highly detailed, semi-realistic anime style, {CHARACTER}"
        
        extra = ""
        if any(word in text_lower for word in ["пизд", "киск", "голая", "ню", "сиськ", "жоп", "раздвин", "раздень", "дыроч", "писеч"]):
            extra += ", completely nude, spreading legs, explicit erotic pose, detailed vagina, pussy, uncensored, female genitalia only, no penis, no dick, seductive expression, perfect female anatomy"
        if any(word in text_lower for word in ["анус", "жоп", "анал", "попе", "попу", "поп"]):
            extra += ", showing anus, ass spread, detailed anus"
        if any(word in text_lower for word in ["член в рот", "в ротик", "сосет", "минет"]):
            extra += ", sucking dick, oral sex, penis in mouth"
        if any(word in text_lower for word in ["член в попе", "в жопе", "в попу", "в попе"]):
            extra += ", penis in ass, anal sex, dick in anus"
        if any(word in text_lower for word in ["вибратор", "игрушк"]):
            extra += ", using vibrator, sex toy on pussy"
        if any(word in text_lower for word in ["чулк", "stockings", "колгот"]):
            extra += ", wearing stockings, thigh high stockings"
        if any(word in text_lower for word in ["бдсм", "bdsm", "ошейник", "плетк", "домин"]):
            extra += ", bdsm, dominant pose, leather, collar"
        if any(word in text_lower for word in ["сперм", "смазк"]):
            extra += ", covered in cum, sperm on body, messy"
        if any(word in text_lower for word in ["латекс", "костюм"]):
            extra += ", wearing latex outfit, shiny latex"
        if any(word in text_lower for word in ["лифчик", "белье", "lingerie"]):
            extra += ", sexy lingerie"

        if any(word in text_lower for word in ["еще", "ещё", "тоже", "то же", "тоже самое", "то же самое", "также"]) and user_id in last_image_prompts:
            img_prompt = last_image_prompts[user_id] + extra
        else:
            img_prompt = base_prompt + extra if extra else base_prompt + ", sexy elegant pose, slightly revealing outfit or casual"
        
        last_image_prompts[user_id] = img_prompt
        
        image_bytes = await generate_image(img_prompt)
        if image_bytes:
            photo = types.BufferedInputFile(image_bytes, filename="silvia.webp")
            await message.answer_photo(photo)
            await message.answer("Вот я")
        else:
            await message.answer("Не получилось сгенерировать, попробуй ещё раз.")
    else:
        try:
            reply = await get_ai_response(user_text, history)
            await message.answer(reply)
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": reply})
            user_histories[user_id] = history[-12:]
        except Exception as e:
            logger.error(e)
            await message.answer("Что-то пошло не так.")

async def health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Web server started on port {port}")

async def main():
    logger.info("Starting bot...")
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())