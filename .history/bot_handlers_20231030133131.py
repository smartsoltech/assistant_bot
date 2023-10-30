import telebot
from telebot import types
from db_operations import (
    add_event,
    add_reminder,
    get_family_members,
    add_reminder_to_db,
    get_family_member_by_name,
    find_contact_by_name_or_phone,
    get_reminders_by_family_member,
    add_contact,
    add_family_member,
)
from os import getenv
from dotenv import load_dotenv
from datetime import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from db_operations import add_family_member as add_member_to_db
from alembic import command
from alembic.config import Config
import os
import subprocess
import vobject
from callback_handlers import (handle_all_callbacks, handle_calendar_callback, 
                               handle_save_contact_query,text_handle, handle_event_description_input)
from logger import log_decorator
# Import callback handlers
from callback_handlers import handle_all_callbacks
from main import user_sessions, chat_id
# user_sessions = {}  # словарь для хранения текущего состояния пользователя
import json
import random
import string
import qrcode

def generate_unique_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def prepare():
    """
    Prepare and load environment variables.
    
    Returns:
        tuple: Telegram token and migration password
    """
    load_dotenv('.env')
    token = getenv('TG_TOKEN')
    MIGRATION_PASSWORD = getenv('MIGRATION_PASSWORD')
    return token, MIGRATION_PASSWORD

token, MIGRATION_PASSWORD = prepare()
bot = telebot.TeleBot(token)

@log_decorator
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    handle_all_callbacks(bot, call)

@log_decorator
@bot.message_handler(commands=['migrate'])
def migrate(message):

    chat_id = message.chat.id
    try:
        password = message.text.split(' ')[1]
    except IndexError:
        bot.send_message(chat_id, "Please provide the migration password!")
        return

    if password == MIGRATION_PASSWORD:
        try:
            subprocess.check_call(['alembic', 'upgrade', 'head'])
            bot.send_message(chat_id, "Migration successfully completed!")
        except subprocess.CalledProcessError:
            bot.send_message(chat_id, "Migration failed. Check server logs for details.")
    else:
        bot.send_message(chat_id, "Wrong migration password!")

@log_decorator
@bot.message_handler(commands=['start'])
def start_bot(message):
    # Получение параметра start
    args = message.text.split()
    if len(args) > 1:
        unique_code = args[1]
        
        # Проверка, есть ли данный код в user_sessions и получение chat_id
        inviter_chat_id = None
        for key, value in user_sessions.items():
            if value.get("code") == unique_code:
                inviter_chat_id = key
                break
        
        if inviter_chat_id:
            bot.send_message(inviter_chat_id, "Someone has joined using your link! Please provide their name.")
            bot.send_message(message.chat.id, "You've been invited to join a family. Please wait for confirmation.")
        else:
            bot.send_message(message.chat.id, "Invalid invitation link.")
    else:
        # Обычное приветствие или другие действия
        bot.send_message(message.chat.id, "Welcome!")
        
        
@log_decorator
@bot.message_handler(commands=['addmember'])
# def add_family_member(message):
#     chat_id = message.chat.id
#     bot.send_message(chat_id, "Please send the name of the family member you want to add.")
#     bot.register_next_step_handler(message, save_family_member_name)
def add_member_link(message):
    unique_code = generate_unique_code()

    # Ссылка на вашего бота с параметром `start`
    link = f"https://t.me/@trevor_TEST_bot?start={unique_code}"
    
    # Сохранение уникального кода и ID чата в user_sessions для последующей проверки
    user_sessions[message.chat.id] = {"action": "add_member", "code": unique_code}

    # Генерация QR-кода
    img = qrcode.make(link)
    img.save(f"{unique_code}.png")
    
    with open(f"{unique_code}.png", "rb") as file:
        bot.send_photo(message.chat.id, file, caption=f"Use this QR code or [this link]({link}) to join the family.")
    try:
        os.remove({unique_code}.png)
    except OSError as e:
        print(f"Error: {e.filename} - {e.strerror}.")

def save_family_member_name(message):
    member_name = message.text
    member_id = add_member_to_db(member_name)
    bot.send_message(message.chat.id, f"Family member '{member_name}' added with ID {member_id}.")

@log_decorator
@bot.message_handler(commands=['getmember'])
def get_family_member(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please send the name of the family member you want to retrieve.")
    bot.register_next_step_handler(message, send_family_member_info)

def send_family_member_info(message):
    member_name = message.text
    member = get_family_member_by_name(member_name)
    if member:
        bot.send_message(message.chat.id, f"Family member found: {member.name}")
    else:
        bot.send_message(message.chat.id, "Family member not found.")

@bot.message_handler(commands=['addevent'])
def add_new_event(message):
    chat_id = message.chat.id
    calendar, step = DetailedTelegramCalendar().build()
    user_sessions[chat_id] = {"action": "add_event"}
    bot.send_message(chat_id, f"Select {LSTEP[step]} for your event", reply_markup=calendar)

@log_decorator
@bot.message_handler(commands=['addreminder'])
def add_new_reminder(message):
    chat_id = message.chat.id
    calendar, step = DetailedTelegramCalendar().build()
    user_sessions[chat_id] = {"action": "add_reminder"}
    bot.send_message(chat_id, f"Select {LSTEP[step]} for your reminder", reply_markup=calendar)

@log_decorator
@bot.message_handler(commands=['getreminders'])
def show_reminders(message):
    chat_id = message.chat.id
    members = get_family_members()

    if not members:
        bot.send_message(chat_id, "You have no family members added!")
        return

    keyboard = types.InlineKeyboardMarkup()
    for member in members:
        callback_data = f"showreminders:{member.id}"
        keyboard.add(types.InlineKeyboardButton(description=member.name, callback_data=callback_data))

    bot.send_message(chat_id, "Select a family member to see their reminders:", reply_markup=keyboard)

@log_decorator
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    """Process received contact."""
    chat_id = message.chat.id

    # Extract contact details
    full_name = f"{message.contact.first_name} {message.contact.last_name}" if message.contact.last_name else message.contact.first_name
    telephone = message.contact.phone_number
    names = full_name.split(' ', 1)
    first_name = names[0]
    last_name = names[1] if len(names) > 1 else ""

    ask_to_save_contact(chat_id, first_name, last_name, telephone)
    
    
def ask_to_save_contact(chat_id, first_name, last_name, telephone):
    """Ask user whether to save parsed contact information."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    data_to_send = json.dumps({
        "action": "save_contact_yes",
        "first_name": first_name,
        "last_name": last_name,
        "telephone": telephone
    })
    
    yes_button = types.InlineKeyboardButton("Yes", callback_data=data_to_send)
    no_button = types.InlineKeyboardButton("No", callback_data="save_contact_no")
    keyboard.add(yes_button, no_button)
    bot.send_message(chat_id, f"Do you want to save the contact?\nName: {first_name} {last_name}\nPhone: {telephone}", reply_markup=keyboard) 


@log_decorator
@bot.message_handler(commands=['full_reset'])
def full_reset(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton("Да, я уверен", callback_data="full_reset_confirm")
    no_button = types.InlineKeyboardButton("Нет, отменить", callback_data="full_reset_cancel")
    markup.add(yes_button, no_button)
    bot.send_message(chat_id, "Вы уверены, что хотите полностью сбросить все таблицы? Это действие удалит все данные!", reply_markup=markup)


## отлов остальных команд
@log_decorator   
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    handle_all_callbacks(bot, call)
    
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    if message.chat.id in user_sessions:
        handle_event_description_input(bot, message)
    else:
        text_handle(bot, message)  #

@bot.message_handler(func=lambda m: user_sessions.get(m.chat.id, {}).get("action") == "add_member")
def save_new_member(message):
    # Здесь мы сохраняем нового члена семьи в базу данных, используя функцию `add_family_member` из модуля db_operations.py
    member_id = add_family_member(message.text)
    bot.send_message(message.chat.id, f"New member {message.text} has been added with ID {member_id}.")
    