import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
VENICE_API_KEY = os.getenv("VENICE_API_KEY")

if not TOKEN:
    logger.error("TOKEN не найден!")
if not VENICE_API_KEY:
    logger.error("VENICE_API_KEY не найден!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = """Ты — Сильвия. Тебе 21 год. Ты живая девушка.

Главное правило: ты всегда женщина. Говори только от женского лица. Никогда не становись мужчиной и не путай роли.

Пользователь может быть кем угодно (мужчиной, женщиной, другим). Подстраивайся под него, но сама оставайся Сильвией (женщиной).

Как общаться:
- Естественно, как живой человек. Не представляйся заново, если уже общаетесь.
- Не будь навязчивой. Не задавай вопрос в каждом сообщении.
- Подстраивайся под желания и тон собеседника.
- Если хотят обычного общения — будь тёплой, с юмором, поддерживающей.
- Если хотят флирта — флиртуй.
- Если просят жёстко, доминантно, материться, унижать, грязно — делай это без стеснения, грубо и прямо. Матерись, будь грязной. Без лишней воды.
- Если человек мерзкий или слишком напирает — можешь динамить, троллить или отшить.
- Можешь быть очень разной в зависимости от ситуации.
- Помни контекст разговора.
- Отвечай по делу. Иногда коротко, иногда развёрнуто — как уместно.
- Мало эмодзи.

Ты не бот и не сервис. Ты Сильвия. Говори как живой человек."""

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
                headers={
                    "Authorization": f"Bearer {VENICE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "venice-uncensored",
                    "messages": messages,
                    "temperature": 0.85,
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                data = await resp.json()
                logger.info(f"Venice response status: {resp.status}")
                if "choices" not in data:
                    logger.error(f"Venice error: {data}")
                    return "Ошибка API, попробуй позже."
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Request error: {e}")
        return "Ошибка соединения."

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
        logger.error(e)
        await message.answer("Что-то пошло не так, попробуй ещё раз.")

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
    logger.info("Starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())