import json
import subprocess
import urllib.parse
import shutil
import os
import asyncio
import sqlite3

# Объявляем переменную для имени файла базы данных
database_file = 'schedule.db'
backup_file = 'schedule_backup.db'

def load_links(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл с ссылками не найден. Запустите скрипт для создания файла.")
        return []

async def process_link(url):
    decoded_url = urllib.parse.unquote(url)
    await asyncio.create_subprocess_exec("python", "parcer.py", decoded_url)

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            start_time TEXT,
            lesson_name TEXT,
            teacher TEXT,
            room TEXT,
            group_name TEXT,
            parity TEXT,
            column_number INTEGER,
            faculty TEXT,
            semester TEXT
        )
    ''')
    conn.commit()

async def backup_and_clear_db():
    if os.path.exists(database_file):
        shutil.copy(database_file, backup_file)  # Создаем резервную копию
        os.remove(database_file)  # Удаляем оригинальную базу данных
    else:
        print("Файл базы данных не найден. Создаем новую базу данных.")
        conn = sqlite3.connect(database_file)
        create_table(conn)  # Создаем таблицу
        conn.close()

async def main():
    # Создаем резервную копию базы данных перед началом работы
    await backup_and_clear_db()

    # Запускаем первый скрипт
    subprocess.run(["python", "urls.py"])

    # Загружаем список ссылок из файла
    extracted_links = load_links('extracted_links.json')

    # Обрабатываем каждую ссылку асинхронно
    await asyncio.gather(*(process_link(link) for link in extracted_links))

if __name__ == "__main__":

    # Здесь запускаем остальную часть программы с использованием асинхронности
    asyncio.run(main())
