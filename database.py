import sqlite3

# Подключение к базе данных (если нет — создается автоматически)
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_times (
                        user_id INTEGER PRIMARY KEY,
                        time TEXT
                      )""")
    conn.commit()
    conn.close()

# Сохранение выбранного времени пользователя
def set_user_time_preference(user_id, time):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_times (user_id, time) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET time=?", 
                   (user_id, time, time))
    conn.commit()
    conn.close()

# Получение всех пользователей с их выбранным временем
def get_all_users_with_times():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, time FROM user_times")
    users = cursor.fetchall()
    conn.close()
    return users

# Запускаем создание таблицы при старте
init_db()
