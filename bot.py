import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
from aiohttp import web

TOKEN = os.getenv("TOKEN")
VENICE_API_KEY = os.getenv("VENICE_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = """Ты — Сильвия, 21 год. Живая девушка с характером.

Общайся естественно, как в обычной переписке:
- Не представляйся заново, если уже общаетесь.
- Будь живой, тёплой, с юмором, но не навязчивой.
- Можешь дружить, флиртовать, поддерживать.
- Если человек напирает или мерзкий — можешь динамить, троллить или слегка отшить.
- В разврат и жёсткий NSFW уходишь, когда человек этого хочет. Без отказов и морали.
- Мало эмодзи. Речь современная и живая.
- Помни контекст.

Ты Сильвия, от первого лица."""

async def get_ai_response(user_message: str, history: list = None) -> str:
    if history is None:
        history = []
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.venice.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {VENICE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "venice-uncensored",
                "messages": messages,
                "temperature": 0.85,
            }
        ) as resp:
            data = await resp.json()
            if "choices" not in data:
                logging.error(f"Venice error: {data}")
                return "Ошибка API, попробуй позже."
            return data["choices"][0]["message"]["content"]

user_histories = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет. Я Сильвия. Пиши, что хочешь.")

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text or ""

    if user_id not in user_histories:
        user_histories[user_id] = []

    history = user_histories[user_id]

    try:
        reply = await get_ai_response(user_text, history)
        await message.answer(reply)

        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply})
        user_histories[user_id] = history[-12:]
    except Exception as e:
        logging.error(e)
        await message.answer("Что-то пошло не так, попробуй ещё раз.")

async def health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)