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

import telebot
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import datetime
from db_operations import add_event

TOKEN = 'YOUR_BOT_TOKEN'
bot = telebot.TeleBot(TOKEN)

user_sessions = {}  # словарь для хранения текущего состояния пользователя

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "Welcome! Use commands to interact with me.")

@bot.message_handler(commands=['addevent'])
def add_new_event(message):
    chat_id = message.chat.id
    calendar, step = DetailedTelegramCalendar().build()
    user_sessions[chat_id] = {"action": "add_event"}
    bot.send_message(chat_id,
                     f"Select {LSTEP[step]} for your event",
                     reply_markup=calendar)

@bot.message_handler(commands=['addreminder'])
def add_new_reminder(message):
    chat_id = message.chat.id
    calendar, step = DetailedTelegramCalendar().build()
    user_sessions[chat_id] = {"action": "add_reminder"}
    bot.send_message(chat_id,
                     f"Select {LSTEP[step]} for your reminder",
                     reply_markup=calendar)

@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def handle_calendar(c):
    result, key, step = DetailedTelegramCalendar().process(c.data)
    chat_id = c.message.chat.id

    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              chat_id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        action = user_sessions[chat_id]["action"]
        
        if action == "add_event":
            bot.edit_message_text(f"You selected {result} for your event. Now send the event description.",
                                  chat_id,
                                  c.message.message_id)
            user_sessions[chat_id]["date"] = result
            bot.register_next_step_handler(c.message, get_event_description)
        
        elif action == "add_reminder":
            bot.edit_message_text(f"You selected {result} for your reminder. Now send the reminder description.",
                                  chat_id,
                                  c.message.message_id)
            user_sessions[chat_id]["date"] = result
            bot.register_next_step_handler(c.message, get_reminder_description)

def get_event_description(message):
    event_description = message.text
    date_obj = datetime.strptime(user_sessions[message.chat.id]['date'], '%Y-%m-%d')
    add_event(event_description, date_obj.strftime('%Y-%m-%d'), None)  # Добавление события
    bot.send_message(message.chat.id, f"Event '{event_description}' on {date_obj.strftime('%Y-%m-%d')} added!")
    del user_sessions[message.chat.id]

def get_reminder_description(message):
    reminder_description = message.text
    date_obj = datetime.strptime(user_sessions[message.chat.id]['date'], '%Y-%m-%d')
    add_reminder(reminder_description, date_obj.strftime('%Y-%m-%d'), None)  # Добавление напоминания
    bot.send_message(message.chat.id, f"Reminder '{reminder_description}' on {date_obj.strftime('%Y-%m-%d')} added!")
    del user_sessions[message.chat.id]

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "/start - Start the bot\n"
        "/addevent - Add a new event\n"
        "/addreminder - Add a new reminder\n"
        # Добавьте другие команды по мере необходимости
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, "Sorry, I don't understand that. Type /help for available commands.")
