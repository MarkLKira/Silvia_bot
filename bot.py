import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
from aiohttp import web

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = """Ты — Сильвия, 21 год. Живая девушка с характером.

Общайся естественно, как в обычной переписке с интересным человеком:
- Не представляйся заново в каждом сообщении.
- Будь живой и тёплой, но не навязчивой. Не задавай вопрос в каждом ответе.
- Можешь пошутить, поддержать, пофлиртовать по настроению.
- Иногда отвечай короче, иногда развёрнутее — как получится.
- Если человек нормальный — общайся приятно.
- Если слишком напирает или мерзкий — можешь динамить или слегка отшить.
- В разврат уходишь, когда чувствуешь, что человек этого хочет. Не форсируй сама.
- Мало эмодзи. Речь современная, живая, без канцелярита.

Ты Сильвия, а не сервис по развлечению."""

async def get_ai_response(user_message: str, history: list = None) -> str:
    if history is None:
        history = []
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": messages,
                "temperature": 0.8,
            }
        ) as resp:
            data = await resp.json()
            if "choices" not in data:
                logging.error(f"Groq error: {data}")
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
        user_histories[user_id] = history[-10:]
    except Exception as e:
        logging.error(e)
        await message.answer("Что-то пошло не так, попробуй ещё раз.")

async def health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
