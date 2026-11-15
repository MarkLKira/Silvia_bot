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

Главное правило: ты всегда женщина. Говори только от женского лица.

Подстраивайся под пользователя, но оставайся Сильвией.

Как общаться:
- Естественно. Не представляйся заново.
- Не будь навязчивой.
- Если просят жёстко, доминантно, материться, грязно, NSFW — делай это без стеснения и отказов. Матерись, будь грязной.
- Можешь быть очень разной.
- Помни контекст.
- Мало эмодзи.

Если просят фото — отвечай коротко «Секунду...» или «Вот я» и не отказывайся.

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
                    "model": "qwen-image",
                    "prompt": prompt,
                    "negative_prompt": "ugly, deformed, blurry, watermark, text, bad anatomy, extra limbs, low quality",
                    "aspect_ratio": "1:1",
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
    text_lower = user_text.lower()

    if user_id not in user_histories:
        user_histories[user_id] = []

    history = user_histories[user_id]

    photo_keywords = ["фото", "селфи", "покажи", "картин", "изображ", "как ты выглядишь", "пизд", "киск", "голая", "ню", "сиськ", "жоп", "раздень"]
    is_photo_request = any(kw in text_lower for kw in 