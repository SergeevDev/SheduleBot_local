import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.executor import start_polling
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from aiogram import executor

# Создаем бота
API_TOKEN = '7085107605:AAGjuo8AT88l2k9H-vsoKGsxzAdYYHYTtOQ'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Определение состояний
class ScheduleState(StatesGroup):
    main_menu = State()
    faculty = State()
    group = State()
    day_selection = State()

# Соединение с базой данных
conn = sqlite3.connect('schedule.db', check_same_thread=False)
cursor = conn.cursor()

def get_week_info():
    today = datetime.now()
    week_number = today.isocalendar()[1]
    week_parity = 'Чётная' if week_number % 2 == 0 else 'Нечётная'
    day_of_week = today.weekday() + 1
    return today, week_parity, day_of_week

def get_day_name(day_number):
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    return days[day_number - 1] if 1 <= day_number <= 7 else 'Неизвестный день'

@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.reset_state()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Начать"))
    await message.answer("Добро пожаловать! Нажмите 'Начать'", reply_markup=keyboard)
    await ScheduleState.main_menu.set()

@dp.message_handler(state=ScheduleState.main_menu)
async def main_menu(message: types.Message, state: FSMContext):
    if message.text == "Начать":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Посмотреть расписание"))
        await message.answer("Выберите действие:", reply_markup=keyboard)
        await ScheduleState.faculty.set()
    else:
        await message.answer("Нажмите 'Начать' для продолжения.")

@dp.message_handler(state=ScheduleState.faculty)
async def select_faculty(message: types.Message, state: FSMContext):
    if message.text == "Посмотреть расписание":
        cursor.execute("SELECT DISTINCT faculty FROM schedule")
        faculties = cursor.fetchall()
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for faculty in faculties:
            keyboard.add(KeyboardButton(faculty[0]))
        keyboard.add(KeyboardButton("Назад"))
        await message.answer("Выберите ваш факультет:", reply_markup=keyboard)
    elif message.text == "Назад":
        await start(message, state)
    else:
        selected_faculty = message.text
        cursor.execute("SELECT MAX(semester) FROM schedule WHERE faculty = ?", (selected_faculty,))
        max_semester = cursor.fetchone()[0]
        await state.update_data(faculty=selected_faculty, semester=max_semester)
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton('1'))
        keyboard.add(KeyboardButton('2'))
        keyboard.add(KeyboardButton('Все'))
        keyboard.add(KeyboardButton("Назад"))
        await message.answer("Выберите вашу группу:", reply_markup=keyboard)
        await ScheduleState.group.set()

@dp.message_handler(state=ScheduleState.group)
async def select_group(message: types.Message, state: FSMContext):
    selected_group = message.text
    if selected_group == "Назад":
        cursor.execute("SELECT DISTINCT faculty FROM schedule")
        faculties = cursor.fetchall()
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for faculty in faculties:
            keyboard.add(KeyboardButton(faculty[0]))
        keyboard.add(KeyboardButton("Назад"))
        await message.answer("Выберите ваш факультет:", reply_markup=keyboard)
        await ScheduleState.faculty.set()
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton('Сегодня'), KeyboardButton('Завтра'), KeyboardButton('Назад'))
        await message.answer(f"Выбрана группа: {selected_group}\nВыберите, что вы хотите видеть:", reply_markup=keyboard)
        await state.update_data(group=selected_group)
        await ScheduleState.day_selection.set()

@dp.message_handler(state=ScheduleState.day_selection)
async def show_schedule(message: types.Message, state: FSMContext):
    selected_day = message.text
    if selected_day == "Назад":
        selected_faculty = (await state.get_data())['faculty']
        cursor.execute("SELECT MAX(semester) FROM schedule WHERE faculty = ?", (selected_faculty,))
        max_semester = cursor.fetchone()[0]
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton('1'))
        keyboard.add(KeyboardButton('2'))
        keyboard.add(KeyboardButton('Все'))
        keyboard.add(KeyboardButton("Назад"))
        await message.answer("Выберите вашу группу:", reply_markup=keyboard)
        await ScheduleState.group.set()
    else:
        data = await state.get_data()
        selected_faculty, selected_semester, selected_group = data['faculty'], data['semester'], data['group']
        _, week_parity, day_of_week = get_week_info()
        week_parity_symbol = "🟢" if week_parity == "Чётная" else "🔴"
        
        # Строим условие для выбора группы
        group_condition = "(group_name = '1' OR group_name = '2' OR group_name = '')" if selected_group == "Все" else f"(group_name = '{selected_group}' OR group_name = '')"
        
        # Выбираем запрос в зависимости от выбранного дня
        if selected_day == 'Сегодня':
            query = f"""
                SELECT start_time, lesson_name, teacher, room, column_number 
                FROM schedule 
                WHERE faculty = ? AND semester = ? AND {group_condition}
                AND (parity = ? OR parity = '') AND column_number = ?
            """
            params = (selected_faculty, selected_semester, week_parity, day_of_week)
        elif selected_day == 'Завтра':
            next_day = (day_of_week % 7) + 1
            query = f"""
                SELECT start_time, lesson_name, teacher, room, column_number 
                FROM schedule 
                WHERE faculty = ? AND semester = ? AND {group_condition}
                AND (parity = ? OR parity = '') AND column_number = ?
            """
            params = (selected_faculty, selected_semester, week_parity, next_day)
        else:
            await message.answer("Некорректный выбор. Пожалуйста, выберите 'Сегодня' или 'Завтра'.")
            return

        cursor.execute(query, params)
        schedule = cursor.fetchall()

        response = f"{week_parity} {week_parity_symbol}\nРасписание для факультета {selected_faculty}\nСеместр: {selected_semester}\nГруппа: {selected_group}\n\n"
        day_name = get_day_name(day_of_week) if selected_day == 'Сегодня' else get_day_name(next_day)

        if schedule:
            response += f"{day_name} ({selected_day})\n" + "_" * 24 + "\n"
            for entry in schedule:
                response += f"\nНачало: {entry[0]}\nПредмет: {entry[1]}\nАудитория: {entry[3]}\nПреподаватель: {entry[2]}\n" + "_" * 24 + "\n"
        else:
            response += "Расписание отсутствует для выбранного дня."

        await message.answer(response, parse_mode='HTML')

if __name__ == '__main__':
    executor.start_polling(dp)
