import logging
import asyncio
import os
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Настройка бота
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Логирование
logging.basicConfig(level=logging.INFO)

# Файл для хранения данных пользователей
DATA_FILE = "users_data.json"

# Загружаем данные из JSON-файла
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Сохраняем данные в JSON-файл
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Данные пользователей
users_data = load_data()

# Приветствие нового пользователя
@dp.message(Command("start"))
async def start(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "Нет username"
    
    if user_id not in users_data:
        users_data[user_id] = {
            "username": f"@{username}",
            "skincare_products": [],
            "entries": []
        }
        save_data(users_data)

    await message.answer("Привет! Это твой дневник ухода за кожей. Напиши, какими средствами ты пользуешься (каждое с новой строки).")

# Сохранение списка средств
@dp.message()
async def save_products(message: Message):
    user_id = str(message.from_user.id)

    if not users_data.get(user_id, {}).get("skincare_products"):
        products = message.text.split("\n")
        users_data[user_id]["skincare_products"] = products
        save_data(users_data)

        await message.answer("Отлично! Теперь я буду каждый день спрашивать тебя о состоянии твоей кожи.")
        await ask_skin_status(user_id)

# Функция опроса состояния кожи
async def ask_skin_status(user_id):
    await bot.send_message(user_id, "Как твоя кожа сегодня? Оцени от 0 до 10.")

# Сохранение оценки
@dp.message()
async def save_skin_status(message: Message):
    user_id = str(message.from_user.id)
    score = message.text

    if score.isdigit() and 0 <= int(score) <= 10:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users_data[user_id]["entries"].append({"date": now, "score": int(score)})
        save_data(users_data)

        # Клавиатура с выбором использованных средств
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for product in users_data[user_id]["skincare_products"]:
            keyboard.add(KeyboardButton(product))

        await message.answer("Что использовал сегодня?", reply_markup=keyboard)

# Запись использованных средств
@dp.message()
async def save_used_product(message: Message):
    user_id = str(message.from_user.id)
    product = message.text

    if product in users_data.get(user_id, {}).get("skincare_products", []):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users_data[user_id]["entries"][-1]["used_products"] = product
        save_data(users_data)

        await message.answer("Спасибо! Я сохранил эту информацию.", reply_markup=types.ReplyKeyboardRemove())

# Запуск ежедневного опроса в 22:00
async def schedule_daily_task():
    while True:
        now = datetime.now()
        target_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
        if now > target_time:
            target_time += timedelta(days=1)

        wait_time = (target_time - now).seconds
        await asyncio.sleep(wait_time)

        for user_id in users_data.keys():
            await ask_skin_status(user_id)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(schedule_daily_task())
    loop.run_until_complete(main())
