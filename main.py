import aiosqlite
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import logging

# 🔥 Логирование
logging.basicConfig(level=logging.INFO)

# 🔑 Загрузка токена из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ Ошибка: Токен бота не найден! Убедитесь, что BOT_TOKEN задан в переменных окружения.")

# 📌 Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
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

# 📌 Хранилище временных данных
user_data = {}

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
@dp.message(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я бот-напоминалка. Нажмите '📌 Написать напоминание'", reply_markup=main_menu)

# 📌 Написание напоминания
@dp.message(lambda message: message.text == "📌 Написать напоминание")
async def ask_reminder_text(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Введите текст напоминания:")

# 📅 Установка даты и времени
@dp.message(lambda message: message.from_user.id in user_data and "text" not in user_data[message.from_user.id])
async def set_reminder_text(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["text"] = message.text
    await message.answer("Теперь введите дату и время (Формат: YYYY-MM-DD HH:MM):")

@dp.message(lambda message: message.from_user.id in user_data and "text" in user_data[message.from_user.id])
async def set_reminder_time(message: types.Message):
    user_id = message.from_user.id

    try:
        remind_time = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("⚠️ Ошибка! Введите дату в формате YYYY-MM-DD HH:MM")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT INTO reminders (user_id, message, remind_time) VALUES (?, ?, ?)",
                         (user_id, user_data[user_id]["text"], remind_time.strftime("%Y-%m-%d %H:%M")))
        await db.commit()

    await message.answer(f"✅ Напоминание '{user_data[user_id]['text']}' установлено на {remind_time}", reply_markup=main_menu)
    del user_data[user_id]

# 🔔 Отправка напоминаний
async def send_reminders():
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id, user_id, message, remind_time, repeat FROM reminders WHERE remind_time <= ? AND read_status = 0",
                              (datetime.now().strftime("%Y-%m-%d %H:%M"),)) as cursor:
            reminders = await cursor.fetchall()

            for reminder_id, user_id, message_text, remind_time, repeat in reminders:
                await bot.send_message(user_id, f"🔔 Напоминание: {message_text}", reply_markup=read_button, parse_mode=ParseMode.HTML)

                if repeat == 0:
                    await db.execute("UPDATE reminders SET read_status = 1 WHERE id = ?", (reminder_id,))
                else:
                    new_time = datetime.strptime(remind_time, "%Y-%m-%d %H:%M")  # Парсим дату
                    new_time = new_time.replace(day=new_time.day + 1)  # Смещаем на 1 день вперёд
                    await db.execute("UPDATE reminders SET remind_time = ?, read_status = 0 WHERE id = ?",
                                     (new_time.strftime("%Y-%m-%d %H:%M"), reminder_id))

                await db.commit()

# ✅ Обработчик "Прочитано"
@dp.message(lambda message: message.text == "✅ Прочитано")
async def mark_as_read(message: types.Message):
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE reminders SET read_status = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    await message.answer("✅ Напоминание отмечено как прочитанное! Выберите действие:", reply_markup=repeat_menu)

# 🔄 Повторение напоминаний
@dp.message(lambda message: message.text == "Повторять")
async def set_repeat_reminder(message: types.Message):
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE reminders SET repeat = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    await message.answer("🔄 Напоминание теперь будет повторяться ежедневно!", reply_markup=main_menu)

# 📌 Возвращение в меню
@dp.message(lambda message: message.text == "Меню")
async def return_to_menu(message: types.Message):
    await message.answer("📌 Главное меню", reply_markup=main_menu)

# 📅 Управление напоминаниями
@dp.message(lambda message: message.text == "Управление напоминаниями")
async def manage_reminders(message: types.Message):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id, message, remind_time, repeat FROM reminders WHERE user_id = ?", (message.from_user.id,)) as cursor:
            reminders = await cursor.fetchall()
            if not reminders:
                await message.answer("У вас нет активных напоминаний.")
                return

            for _, message_text, remind_time, repeat in reminders:
                repeat_text = "🔄 Повторяется" if repeat else "❌ Не повторяется"
                await message.answer(f"Напоминание: {message_text}\nВремя: {remind_time}\n{repeat_text}")

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
