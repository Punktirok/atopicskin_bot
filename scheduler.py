from aiogram import Bot
from aiogram.utils.exceptions import BotBlocked
from database import get_all_users_with_times
from datetime import datetime
import pytz
import asyncio

async def send_daily_question(bot: Bot):
    now = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M")
    users = get_all_users_with_times()  # Получаем всех пользователей с их временем

    for user_id, time in users:
        if time == now:
            try:
                await bot.send_message(user_id, "Как твоя кожа сегодня? Оцени от 0 до 10")
            except BotBlocked:
                print(f"Бот заблокирован пользователем {user_id}")
            except Exception as e:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

# Функция для запуска планировщика
async def start_scheduler(bot: Bot):
    while True:
        await send_daily_question(bot)
        await asyncio.sleep(60)  # Проверяем каждую минуту
