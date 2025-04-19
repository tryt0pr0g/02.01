import sqlite3

def update_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Добавляем недостающие поля в таблицу users
    cursor.execute('''
        ALTER TABLE users ADD COLUMN full_name TEXT;
    ''')
    cursor.execute('''
        ALTER TABLE users ADD COLUMN birth_year INTEGER;
    ''')

    # Создаем таблицу секций
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("База данных обновлена!")

if __name__ == '__main__':
    update_database()
