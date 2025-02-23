from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
import os

TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("📌 Написать напоминание")],
        [KeyboardButton("Управление напоминаниями")]
    ],
    resize_keyboard=True
)

# Кнопки для подтверждения прочтения
read_button = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("✅ Прочитано")]
    ],
    resize_keyboard=True
)

# Кнопка для повторения напоминания
repeat_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Повторять"), KeyboardButton("Меню")]
    ],
    resize_keyboard=True
)

# Пример команды /start
@dp.message(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я бот-напоминалка. Нажмите '📌 Написать напоминание'", reply_markup=main_menu)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
