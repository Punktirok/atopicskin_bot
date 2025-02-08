import logging
import asyncio
import os
import asyncpg
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Создаем бота и диспетчер
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Подключение к PostgreSQL
async def create_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

# Функция создания таблиц в БД
async def create_tables():
    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            skincare_products TEXT[]
        );

        CREATE TABLE IF NOT EXISTS entries (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score INTEGER,
            used_products TEXT[]
        );
        """)

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Нет username"

    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING",
            user_id, username
        )

    await message.answer("Привет! Напиши, какими средствами ты пользуешься (каждое с новой строки).")

# Сохранение списка средств пользователя
@dp.message()
async def save_products(message: Message):
    user_id = message.from_user.id
    products = message.text.split("\n")

    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET skincare_products = $1 WHERE user_id = $2",
            products, user_id
        )

    await message.answer("Спасибо! Теперь я буду спрашивать тебя о состоянии кожи.")

# Функция отправки вопроса "Как твоя кожа сегодня?"
async def ask_skin_status(user_id):
    await bot.send_message(user_id, "Как твоя кожа сегодня? Оцени от 0 до 10.")

# Запрос состояния кожи и сохранение оценки
@dp.message()
async def save_skin_status(message: Message):
    user_id = message.from_user.id
    score = message.text

    if score.isdigit() and 0 <= int(score) <= 10:
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO entries (user_id, score) VALUES ($1, $2)",
                user_id, int(score)
            )

        # Получаем список средств пользователя
        async with db_pool.acquire() as conn:
            skincare_products = await conn.fetchval(
                "SELECT skincare_products FROM users WHERE user_id = $1",
                user_id
            )

        # Создаем клавиатуру с продуктами
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        if skincare_products:
            for product in skincare_products:
                keyboard.add(KeyboardButton(product))

        await message.answer("Что использовал сегодня?", reply_markup=keyboard)

# Сохранение использованных средств
@dp.message()
async def save_used_product(message: Message):
    user_id = message.from_user.id
    product = message.text

    async with db_pool.acquire() as conn:
        user_products = await conn.fetchval(
            "SELECT skincare_products FROM users WHERE user_id = $1",
            user_id
        )

    if user_products and product in user_products:
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE entries SET used_products = array_append(used_products, $1) WHERE user_id = $2 ORDER BY date DESC LIMIT 1",
                product, user_id
            )

        await message.answer("Спасибо! Я сохранил информацию.", reply_markup=types.ReplyKeyboardRemove())

# Функция для отправки ежедневных вопросов в 22:00
async def schedule_daily_task():
    while True:
        now = datetime.now()
        target_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
        if now > target_time:
            target_time += timedelta(days=1)

        wait_time = (target_time - now).seconds
        await asyncio.sleep(wait_time)

        async with db_pool.acquire() as conn:
            users = await conn.fetch("SELECT user_id FROM users")

        for user in users:
            await ask_skin_status(user["user_id"])

# Главная функция запуска бота
async def main():
    global db_pool
    db_pool = await create_db_pool()  # Подключение к базе
    await create_tables()  # Создание таблиц
    asyncio.create_task(schedule_daily_task())  # Запуск ежедневных вопросов
    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())
