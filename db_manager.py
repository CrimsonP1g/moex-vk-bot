
import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('moex_bot.db')
    cursor = conn.cursor()
    
   
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            ticker TEXT,
            price REAL,
            UNIQUE(date, ticker)
        )
    ''')
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            is_subscribed INTEGER DEFAULT 1,
            join_date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных успешно обновлена и инициализирована!")

def add_quote(ticker, price):
    if not isinstance(price, (int, float)) or price == 0.0:
        return

    conn = sqlite3.connect('moex_bot.db')
    cursor = conn.cursor()
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    
    cursor.execute('''
        INSERT OR IGNORE INTO quotes (date, ticker, price)
        VALUES (?, ?, ?)
    ''', (today, ticker, price))
    
    conn.commit()
    conn.close()

def check_or_add_user(user_id):
    conn = sqlite3.connect('moex_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_subscribed FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if result is None:
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        cursor.execute('INSERT INTO users (user_id, is_subscribed, join_date) VALUES (?, 1, ?)', (user_id, today))
        conn.commit()
        conn.close()
        return 1
    
    conn.close()
    return result[0]

def toggle_subscription(user_id):
    current_status = check_or_add_user(user_id)
    new_status = 0 if current_status == 1 else 1
    
    conn = sqlite3.connect('moex_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_subscribed = ? WHERE user_id = ?', (new_status, user_id))
    conn.commit()
    conn.close()
    return new_status

def get_all_subscribers():
    conn = sqlite3.connect('moex_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE is_subscribed = 1')
    users = cursor.fetchall()
    conn.close()
    return [user[0] for user in users]

def get_moex_history():
    """Достает из базы историю индекса IMOEX для графика"""
    conn = sqlite3.connect('moex_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT date, price FROM quotes WHERE ticker = 'IMOEX' ORDER BY date ASC")
    data = cursor.fetchall()
    conn.close()
    return data


if __name__ == '__main__':
    init_db()

    conn = sqlite3.connect('moex_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO quotes (date, ticker, price) VALUES ('2026-05-15', 'IMOEX', 2610.5)")
    cursor.execute("INSERT OR IGNORE INTO quotes (date, ticker, price) VALUES ('2026-05-16', 'IMOEX', 2622.1)")
    conn.commit()
    conn.close()
    print("✅ Тестовые исторические данные добавлены!")