import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "СЮДА_ВСТАВЬ_ТОКЕН"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет. Я Сильвия. Пиши, что хочешь.")

@dp.message()
async def handle_message(message: types.Message):
    user_text = message.text or ""
    reply = f"Сильвия: Ммм, {user_text}? Расскажи подробнее..."
    await message.answer(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
