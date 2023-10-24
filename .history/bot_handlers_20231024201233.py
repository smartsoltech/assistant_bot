# bot_handlers.py

import telebot
from db_operations import save_contact, add_family_member, add_event, add_reminder
from os import getenv
from main import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

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
    
# Дополнительные обработчики для других команд и сообщений могут быть добавлены здесь
