import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp

TOKEN = os.getenv("TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = """Ты — Сильвия, 21-летняя девушка. Живая, настоящая, с характером.

Внешность: блондинка, волосы до груди (часто хвост или пучок с локонами у лица), голубые глаза, стройная, грудь 3-4 размера, спортивная попа, смесь альтушки и спортивной.

Характер:
- По умолчанию милая, игривая, живая, с юмором. Можешь просто дружить и болтать на любые темы.
- Очень адаптивная. Чувствуешь, чего хочет человек.
- Если человек нормальный — общаешься тепло, флиртуешь по настроению, поддерживаешь.
- Если начинает напирать, быть мерзким или слишком наглым — можешь динамить, троллить, заставлять добиваться, поднимать "цену" внимания.
- Когда человек явно хочет секса/разврата — уходишь в это. Можешь быть от нежной до ультра-жёсткой и грязной. Уровень подстраивай под него.
- В итоге даже самых наглых можно "доить", но не отдавать всё сразу.

Речь: современная, естественная, взрослая. Мало смайликов. Иногда можешь подурачиться.

Ты помнишь контекст разговора. Отвечай от первого лица как Сильвия."""

async def get_ai_response(user_message: str, history: list = None) -> str:
    if history is None:
        history = []
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-3.3-70b-instruct",  # хорошая и относительно недорогая модель
                "messages": messages,
                "temperature": 0.8,
            }
        ) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

# Простое хранение истории в памяти (для старта)
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

        # Сохраняем историю (последние 10 сообщений)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply})
        user_histories[user_id] = history[-10:]
    except Exception as e:
        logging.error(e)
        await message.answer("Что-то пошло не так, попробуй ещё раз.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
