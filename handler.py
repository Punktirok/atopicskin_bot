from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import set_user_time_preference
from bot import dp  # Импортируем диспетчер бота из bot.py

# Временные слоты на выбор
TIME_SLOTS = ["21:00", "22:00", "23:00", "23:30"]

# Создаем клавиатуру с кнопками времени
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for time in TIME_SLOTS:
    keyboard.add(KeyboardButton(time))

# Обработчик выбора времени
@dp.message_handler(lambda message: message.text in TIME_SLOTS)
async def set_time_preference(message: types.Message):
    set_user_time_preference(message.from_user.id, message.text)  # Сохраняем в БД
    await message.answer(f"Ты выбрал {message.text}. Теперь ежедневные вопросы будут приходить в это время.")
