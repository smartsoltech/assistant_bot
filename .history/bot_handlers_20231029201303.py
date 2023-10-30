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
from callback_handlers import handle_all_callbacks, handle_calendar_callback, handle_save_contact_query
from logger import log_decorator
# Import callback handlers
from callback_handlers import handle_all_callbacks
from main import user_sessions, chat_id
# user_sessions = {}  # словарь для хранения текущего состояния пользователя
import json

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
def start(m):
    bot.send_message(m.chat.id, "Welcome! Use commands to interact with me.")

@log_decorator
@bot.message_handler(commands=['addmember'])
def add_family_member(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please send the name of the family member you want to add.")
    bot.register_next_step_handler(message, save_family_member_name)

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
    yes_button = types.InlineKeyboardButton("Yes", callback_data=f"save_contact_yes:{first_name}:{last_name}:{telephone}")
    no_button = types.InlineKeyboardButton("No", callback_data="save_contact_no")
    keyboard.add(yes_button, no_button)
    bot.send_message(chat_id, f"Do you want to save the contact?\nName: {first_name} {last_name}\nPhone: {telephone}", reply_markup=keyboard)
    
    
@log_decorator   
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    handle_all_callbacks(bot, call)

@log_decorator
@bot.message_handler(commands=['full_reset'])
def full_reset(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton("Да, я уверен", callback_data="full_reset_confirm")
    no_button = types.InlineKeyboardButton("Нет, отменить", callback_data="full_reset_cancel")
    markup.add(yes_button, no_button)
    bot.send_message(chat_id, "Вы уверены, что хотите полностью сбросить все таблицы? Это действие удалит все данные!", reply_markup=markup)
