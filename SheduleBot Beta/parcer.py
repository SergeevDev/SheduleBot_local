import sys
import sqlite3
from bs4 import BeautifulSoup
import re
import requests

def fetch_schedule(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем наличие ошибок при запросе
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        # Извлекаем номер семестра из HTML-кода
        semester_element = soup.find('option', selected=True)
        if semester_element:
            semester = semester_element.text.split()[1]  # Получаем текст из <option>, а затем разбиваем его и берем второй элемент (номер семестра)
        else:
            semester = None
     
        # Извлекаем название факультета из HTML-кода
        faculty_element = soup.find('div', class_='groups')
        if faculty_element:
            faculty_text = faculty_element.find_next('div', class_='groups').text.strip()  # Получаем текст элемента
            faculty = faculty_text.split('Гр. ')[1] if 'Гр. ' in faculty_text else None  # Ищем "Гр. " в тексте и берем вторую часть, если найдено
        else:
            faculty = None
        if semester and faculty:
            pass # print(f"Факультет: {faculty}, Семестр: {semester}") #Для проверки убрать удалить решетку и pass
        else:
            print("Номер факультета и/или семестр не найдены в HTML-коде.")
        
        return html_content, faculty, semester
    except requests.exceptions.RequestException as e:
        print(f"Error fetching schedule: {e}")
        return None, None, None

def parse_schedule(html_content, faculty, semester, conn):  # Добавляем параметры faculty и semester
    soup = BeautifulSoup(html_content, 'html.parser')
    time_rows = soup.find_all('tr')  # Находим все строки с временем и уроками
    
    for row in time_rows:
        time_cell = row.find('td', class_='td1')
        if time_cell is not None:  # Проверяем, что строка содержит время
            start_time = re.search(r'(\d{1,2}:\d{2})', time_cell.text)
            if start_time:  # Проверяем, что удалось извлечь время
                start_time = start_time.group(1)

                # Получаем все столбцы (td) в текущей строке
                data_cells = row.find_all('td', class_='td1')
                
                for index, data_cell in enumerate(data_cells):
                    # Находим все блоки с данными о занятии в текущем столбце
                    lesson_boxes = data_cell.find_all('div', class_=re.compile(r'lesson_box\d*'))
                    
                    for lesson_box in lesson_boxes:
                        parse_and_save(lesson_box, start_time, index, faculty, semester, conn)  # Добавляем параметры faculty и semester

def parse_and_save(lesson_info, start_time, column_number, faculty, semester, conn):  # Добавляем параметры faculty и semester
    lesson_name = lesson_info.find('div', id='lesson_name').text.strip()
    teacher = lesson_info.find('div', id='foot').text.strip()
    room_info = lesson_info.find('div', id='room').text.strip()
    room_parts = room_info.split('(')
    room = room_parts[0].strip()
    group_name = re.sub(r'\D', '', room_parts[1]) if len(room_parts) > 1 else ''
    parity = lesson_info.find('div', class_=re.compile(r'r(left|right)'))
    parity = parity.text.strip() if parity else ''

    insert_data(conn, start_time, lesson_name, teacher, room, group_name, parity, column_number, faculty, semester)  # Вызываем функцию для вставки данных

    print(f"Start Time: {start_time}")
    print(f"Lesson: {lesson_name}")
    print(f"Teacher: {teacher}")
    print(f"Room: {room}")
    print(f"Group Name: {group_name}")
    print(f"Parity: {parity}")
    print(f"Column Number: {column_number}")  # Выводим порядковый номер столбца
    print(f"Facultet: {faculty}")  # Выводим порядковый номер столбца
    print(f"Semester: {semester}")  # Выводим порядковый номер столбца
    print(f"________________________________")
    
# Функция для создания таблицы, если она не существует
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

# Функция для вставки данных в таблицу
def insert_data(conn, start_time, lesson_name, teacher, room, group_name, parity, column_number, faculty, semester):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO schedule (start_time, lesson_name, teacher, room, group_name, parity, column_number, faculty, semester)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (start_time, lesson_name, teacher, room, group_name, parity, column_number, faculty, semester))
    conn.commit()

def main():
    if len(sys.argv) < 2:
        print("Usage: python WIN.py <url>")
        return

    url = sys.argv[1]
    html_content, faculty, semester = fetch_schedule(url)
    if html_content:
        conn = sqlite3.connect('schedule.db')  # Создаем соединение с базой данных
        create_table(conn)  # Создаем таблицу, если ее нет
        parse_schedule(html_content, faculty, semester, conn)  # Парсим расписание и сохраняем в базу данных
        conn.close()  # Закрываем соединение с базой данных

if __name__ == "__main__":
    main()
