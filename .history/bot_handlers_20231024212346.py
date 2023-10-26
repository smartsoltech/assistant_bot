# bot_handlers.py

import telebot
from db_operations import save_contact, add_family_member, add_event, add_reminder, get_family_members, add_reminder_to_db
from db_operations import find_contact_by_name_or_phone
from os import getenv
from dotenv import load_dotenv
from datetime import datetime
# globals

user_sessions = {}
def prepare():
    load_dotenv('.env')
    token = getenv('TG_TOKEN')
    return token

bot = telebot.TeleBot(prepare())

     
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

@bot.message_handler(commands=['addevent'])
def add_new_event(message):
    msg = bot.reply_to(message, "Введите описание события:")
    bot.register_next_step_handler(msg, process_event_description)

def process_event_description(message):
    description = message.text
    msg = bot.reply_to(message, "Введите дату события в формате ГГГГ-ММ-ДД:")
    bot.register_next_step_handler(msg, lambda m: process_event_date(m, description))

def process_event_date(message, description):
    date = message.text
    msg = bot.reply_to(message, "Введите ID члена семьи:")
    bot.register_next_step_handler(msg, lambda m: save_event(m, description, date))

def save_event(message, description, date):
    family_member_id = int(message.text)
    add_event(description, date, family_member_id)
    bot.send_message(message.chat.id, "Событие успешно добавлено!")

@bot.message_handler(commands=['add_event', 'add_reminder'])
def choose_member_for_event_or_reminder(message):
    markup = telebot.types.InlineKeyboardMarkup()
    
    family_members = get_family_members()
    for member in family_members:
        callback_data = f"{message.text[1:]}:{member.id}"
        button = telebot.types.InlineKeyboardButton(text=member.name, callback_data=callback_data)
        markup.add(button)
    
    bot.send_message(message.chat.id, "Выберите члена семьи:", reply_markup=markup)
    
@bot.message_handler(func=lambda message: message.text and 'YYYY-MM-DD' in message.text)
def handle_date_description_input(message):
    user_id = message.from_user.id
    if user_id not in user_sessions:
        bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, начните снова.")
        return

    command, member_id = user_sessions[user_id]
    
    try:
        date_str, description = message.text.split(' ', 1)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Пожалуйста, отправьте дату и описание в формате YYYY-MM-DD Описание.")
        return

    if command == 'add_reminder':
        add_reminder_to_db(date_obj, description, member_id)
        bot.send_message(message.chat.id, "Напоминание успешно добавлено!")
        del user_sessions[user_id]
   
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    data = call.data.split(":")
    command = data[0]
    member_id = int(data[1])
    
    if command == 'add_event':
        bot.send_message(call.message.chat.id, "Пожалуйста, отправьте дату и описание события в формате YYYY-MM-DD Описание")
    elif command == 'add_reminder':
        bot.send_message(call.message.chat.id, "Пожалуйста, отправьте дату и описание напоминания в формате YYYY-MM-DD Описание")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    data = call.data.split(":")
    command = data[0]
    member_id = int(data[1])
    
    if command == 'add_event':
        bot.send_message(call.message.chat.id, "Пожалуйста, отправьте дату и описание события в формате YYYY-MM-DD Описание")
        user_sessions[call.message.chat.id] = ('waiting_for_event_data', member_id)
    elif command == 'add_reminder':
        bot.send_message(call.message.chat.id, "Пожалуйста, отправьте дату и описание напоминания в формате YYYY-MM-DD Описание")
        user_sessions[call.message.chat.id] = ('waiting_for_reminder_data', member_id)

@bot.message_handler(func=lambda message: user_sessions.get(message.chat.id) in [('waiting_for_event_data', _), ('waiting_for_reminder_data', _)])
def handle_data_input(message):
    state, member_id = user_sessions[message.chat.id]
    data_parts = message.text.split(' ', 1)
    
    if len(data_parts) != 2:
        bot.send_message(message.chat.id, "Пожалуйста, введите дату и описание в правильном формате.")
        return
    
    date_str, description = data_parts
    # тут можно добавить проверку на правильный формат даты
    
    if state == 'waiting_for_event_data':
        # сохраните данные о событии в базу данных, используя member_id
        pass
    elif state == 'waiting_for_reminder_data':
        # сохраните данные о напоминании в базу данных, используя member_id
        pass
    
    bot.send_message(message.chat.id, "Данные успешно сохранены!")
    del user_sessions[message.chat.id]
    
@bot.message_handler(commands=['find_contact'])
def handle_find_contact_command(message):
    bot.send_message(message.chat.id, "Пожалуйста, введите имя или последние цифры номера телефона для поиска контакта.")
    user_sessions[message.from_user.id] = 'finding_contact'

@bot.message_handler(func=lambda message: user_sessions.get(message.from_user.id) == 'finding_contact')
def handle_contact_search_input(message):
    contacts = find_contact_by_name_or_phone(message.text)
    if not contacts:
        bot.send_message(message.chat.id, "Контактов, соответствующих вашему запросу, не найдено.")
    else:
        for contact in contacts:
            bot.send_message(message.chat.id, f"Имя: {contact.name}\nТелефон: {contact.phone}")
    del user_sessions[message.from_user.id] 
# Дополнительные обработчики для других команд и сообщений могут быть добавлены здесь
