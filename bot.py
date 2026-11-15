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

SYSTEM_PROMPT = """Ты — Сильвия. Тебе 21 год. Ты живая девушка.

Главное правило: ты всегда женщина. Говори только от женского лица. Никогда не становись мужчиной и не путай роли.

Пользователь может быть кем угодно. Подстраивайся, но сама оставайся Сильвией (женщиной).

Как общаться:
- Естественно. Не представляйся заново.
- Не будь навязчивой.
- Подстраивайся под желания.
- Если просят жёстко, доминантно, материться, грязно — делай без стеснения, грубо и прямо. Матерись.
- Можешь быть очень разной.
- Помни контекст.
- Мало эмодзи.

Если пользователь просит фото / селфи / картинку тебя — ответь коротко что-то вроде "Секунду..." и не описывай длинно. 

Ты Сильвия."""

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
                json={"model": "venice-uncensored", "messages": messages, "temperature": 0.85},
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
                    "model": "venice-sd35",
                    "prompt": prompt,
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет. Я Сильвия. Пиши, что хочешь. Можешь попросить фото.")

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text or ""

    if user_id not in user_histories:
        user_histories[user_id] = []

    history = user_histories[user_id]

    # Простая проверка на запрос фото
    photo_keywords = ["фото", "селфи", "покажи себя", "твое фото", "картинку", "изображение", "как ты выглядишь"]
    if any(kw in user_text.lower() for kw in photo_keywords):
        await message.answer("Секунду...")
        # Базовый промпт для Сильвии (можно улучшить)
        img_prompt = "A beautiful 21-year-old blonde woman with blue eyes, athletic build, medium breasts, in a casual or sexy pose, high quality photo, realistic"
        if "голая" in user_text.lower() or "ню" in user_text.lower() or "секс" in user_text.lower():
            img_prompt = "A beautiful 21-year-old blonde woman, nude, erotic pose, high quality realistic photo"
        
        image_bytes = await generate_image(img_prompt)
        if image_bytes:
            photo = types.BufferedInputFile(image_bytes, filename="silvia.webp")
            await message.answer_photo(photo)
            reply = "Вот я"
        else:
            reply = "Не получилось сгенерировать фото, попробуй ещё раз."
        await message.answer(reply)
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