import json
import subprocess
import urllib.parse
import shutil
import os
import sqlite3
import time

start_time = time.time()

# Переменные для файлов базы данных
database_file = 'schedule.db'
backup_file = 'schedule_backup.db'

# Загрузка списка ссылок из файла
def load_links(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл с ссылками не найден. Запустите скрипт для создания файла.")
        return []

# Обработка каждой ссылки
def process_link(url):
    decoded_url = urllib.parse.unquote(url)
    subprocess.run(["python", "parcer.py", decoded_url])

# Создание таблицы в базе данных
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

# Создание резервной копии базы данных перед началом работы
def backup_and_clear_db():
    if os.path.exists(database_file):
        shutil.copy(database_file, backup_file)  
        os.remove(database_file)  
    else:
        print("Файл базы данных не найден. Создаем новую базу данных.")
        conn = sqlite3.connect(database_file)
        create_table(conn)  
        conn.close()

# Проверка наличия файла с извлеченными ссылками
def check_links_file():
    while not os.path.exists('extracted_links.json'):
        time.sleep(0.001)  
    print("Файл с ссылками найден. Продолжаем работу.")

# Запуск скрипта urls.py для извлечения ссылок
def run_urls_script():
    subprocess.run(["python", "urls.py"])

def main():
    backup_and_clear_db()  # Создаем резервную копию базы данных перед началом работы
    run_urls_script()  # Запускаем скрипт для извлечения ссылок
    check_links_file()  # Проверяем наличие файла с ссылками

    extracted_links = load_links('extracted_links.json')  # Загружаем список ссылок из файла

    # Обрабатываем каждую ссылку
    for link in extracted_links:
        process_link(link)

if __name__ == "__main__":
    main()

end_time = time.time()
execution_time = end_time - start_time
print("Время выполнения:", execution_time)
