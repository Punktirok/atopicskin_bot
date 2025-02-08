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

    await message.answer("Привет! Это твой дневник ухода за кожей. Напиши,
