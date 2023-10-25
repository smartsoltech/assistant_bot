# bot_handlers.py

import telebot
from db_operations import save_contact, add_family_member, add_event, add_reminder, get_family_members, add_reminder_to_db
from db_operations import find_contact_by_name_or_phone
from os import getenv
from dotenv import load_dotenv
from datetime import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

# globals
user_sessions = {}

def prepare():
    load_dotenv('.env')
    token = getenv('TG_TOKEN')
    return token

bot = telebot.TeleBot(prepare())

@bot.message_handler(commands=['addevent'])
def add_new_event(message):
    chat_id = message.chat.id
    now = datetime.now()
    bot.send_message(chat_id=chat_id, text="Please select a date", reply_markup=DetailedTelegramCalendar().build())

@bot.message_handler(content_types=['contact'])
def handle_received_contact(message):
    contact_info = message.contact
    name = contact_info.first_name + " " + (contact_info.last_name if contact_info.last_name else "")
    phone = contact_info.phone_number
    save_contact(name, phone)
    bot.send_message(message.chat.id, "Контакт успешно сохранен!")

@bot.message_handler(commands=['addmember'])
def add_member(message):
    msg = bot.reply_to(message, "Введите имя нового члена семьи:")
    bot.register_next_step_handler(msg, process_member_name)

def process_member_name(message):
    name = message.text
    member_id = add_family_member(name)
    bot.send_message(message.chat.id, f"Член семьи с именем {name} добавлен с ID: {member_id}")

@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(c):
    result, key, step = DetailedTelegramCalendar().process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"You selected {result}",
                              c.message.chat.id,
                              c.message.message_id)

@bot.callback_query_handler(func=lambda call: not call.data.startswith(DetailedTelegramCalendar.ID))
def handle_callback_query(call):
    data = call.data.split(":")
    command = data[0]
    member_id = int(data[1])
    
    if command == 'add_event':
        bot.send_message(call.message.chat.id, "Пожалуйста, отправьте дату и описание события в формате YYYY-MM-DD Описание", reply_markup=DetailedTelegramCalendar().build())
        user_sessions[call.message.chat.id] = ('waiting_for_event_data', member_id)
    elif command == 'add_reminder':
        bot.send_message(call.message.chat.id, "Пожалуйста, отправьте дату и описание напоминания в формате YYYY-MM-DD Описание", reply_markup=DetailedTelegramCalendar().build())
        user_sessions[call.message.chat.id] = ('waiting_for_reminder_data', member_id)

@bot.message_handler(func=lambda message: user_sessions.get(message.chat.id) and user_sessions[message.chat.id][0] in ['waiting_for_event_data', 'waiting_for_reminder_data'])
def handle_data_input(message):
    state, member_id = user_sessions[message.chat.id]
    data_parts = message.text.split(" ", 1)
    if len(data_parts) != 2:
        bot.send_message(message.chat.id, "Неправильный формат. Пожалуйста, используйте формат YYYY-MM-DD Описание.")
        return

    date_str, description = data_parts
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        bot.send_message(message.chat.id, "Неправильная дата. Используйте формат YYYY-MM-DD.")
        return

    if state == 'waiting_for_event_data':
        add_event(member_id, date_obj, description)
        bot.send_message(message.chat.id, f"Событие '{description}' на {date_str} добавлено!")
    elif state == 'waiting_for_reminder_data':
        add_reminder(member_id, date_obj, description)
        bot.send_message(message.chat.id, f"Напоминание '{description}' на {date_str} добавлено!")

    # Сбрасываем состояние
    user_sessions.pop(message.chat.id, None)

@bot.message_handler(commands=['find_contact'])
def handle_find_contact_command(message):
    bot.send_message(message.chat.id, "Пожалуйста, введите имя или последние цифры номера телефона для поиска контакта.")
    user_sessions[message.from_user.id] = 'finding_contact'

@bot.message_handler(func=lambda message: user_sessions.get(message
.from_user.id) == 'finding_contact')
def find_contact_by_input(message):
    input_text = message.text
    contacts = find_contact_by_name_or_phone(input_text)
    
    if not contacts:
        bot.send_message(message.chat.id, "Контакты не найдены.")
    else:
        for contact in contacts:
            bot.send_message(message.chat.id, f"Имя: {contact['name']}, Телефон: {contact['phone']}")
    
    # Сбрасываем состояние
    user_sessions.pop(message.from_user.id, None)

# Если нужно добавить другие обработчики, вы можете продолжить добавлять их здесь

