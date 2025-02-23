import aiosqlite
import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 🔥 Логирование
logging.basicConfig(level=logging.INFO)

# 🔑 Токен бота (из переменных окружения Railway)
TOKEN = os.getenv("7887415022:AAHr5MDC83t1Yw6qqil-DWsmaUlqHgJSQcs")

# 📌 Инициализация бота и диспетчера
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# 📌 Главное меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("📌 Написать напоминание"))
main_menu.add(KeyboardButton("Управление напоминаниями"))

# 📌 Кнопки при получении напоминания
read_button = ReplyKeyboardMarkup(resize_keyboard=True)
read_button.add(KeyboardButton("✅ Прочитано"))

repeat_menu = ReplyKeyboardMarkup(resize_keyboard=True)
repeat_menu.add(KeyboardButton("Повторять"), KeyboardButton("Меню"))

# 📌 Файл базы данных
DB_FILE = "reminders.db"

# 📌 Создание БД
async def setup_database():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                remind_time TEXT,
                read_status INTEGER DEFAULT 0,
                repeat INTEGER DEFAULT 0
            )
        """)
        await db.commit()

# 🚀 Команда /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я бот-напоминалка. Нажмите '📌 Написать напоминание'", reply_markup=main_menu)

# 📌 Написание напоминания
@dp.message(lambda message: message.text == "📌 Написать напоминание")
async def ask_reminder_text(message: types.Message):
    await message.answer("Введите текст напоминания:")

# 📅 Установка даты и времени
@dp.message()
async def set_reminder(message: types.Message):
    async with aiosqlite.connect(DB_FILE) as db:
        user_id = message.from_user.id
        text = message.text
        await message.answer("Теперь введите дату и время (Формат: YYYY-MM-DD HH:MM):")
        remind_time = await bot.wait_for_message()
        try:
            remind_time = datetime.strptime(remind_time.text, "%Y-%m-%d %H:%M")
        except ValueError:
            await message.answer("⚠️ Ошибка! Введите дату в формате YYYY-MM-DD HH:MM")
            return

        await db.execute("INSERT INTO reminders (user_id, message, remind_time) VALUES (?, ?, ?)",
                         (user_id, text, remind_time.strftime("%Y-%m-%d %H:%M")))
        await db.commit()

        await message.answer(f"✅ Напоминание '{text}' установлено на {remind_time}", reply_markup=main_menu)

# 🔔 Отправка напоминаний
async def send_reminders():
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id, user_id, message, remind_time, repeat FROM reminders WHERE remind_time <= ? AND read_status = 0",
                              (datetime.now().strftime("%Y-%m-%d %H:%M"),)) as cursor:
            reminders = await cursor.fetchall()
            for reminder_id, user_id, message_text, remind_time, repeat in reminders:
                await bot.send_message(user_id, f"🔔 Напоминание: {message_text}", reply_markup=read_button)
                if repeat == 0:
                    await db.execute("UPDATE reminders SET read_status = 1 WHERE id = ?", (reminder_id,))
                else:
                    new_time = datetime.strptime(remind_time, "%Y-%m-%d %H:%M")
                    new_time = new_time.replace(day=new_time.day + 1)
                    await db.execute("UPDATE reminders SET remind_time = ?, read_status = 0 WHERE id = ?",
                                     (new_time.strftime("%Y-%m-%d %H:%M"), reminder_id))
                await db.commit()

# 📅 Планировщик задач
async def scheduler():
    while True:
        await send_reminders()
        await asyncio.sleep(60)

# 🚀 Запуск бота
async def main():
    await setup_database()
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
