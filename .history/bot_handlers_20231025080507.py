# bot_handlers.py
import telebot
from telebot import types
from db_operations import save_contact, add_family_member, add_event, add_reminder, get_family_members, add_reminder_to_db, get_family_member_by_name
from db_operations import find_contact_by_name_or_phone
from os import getenv
from dotenv import load_dotenv
from datetime import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

def prepare():
    load_dotenv('.env')
    token = getenv('TG_TOKEN')
    return token

bot = telebot.TeleBot(prepare())

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
        
        user_sessions[chat_id]["date"] = result  # сохраняем объект datetime.date
        
        if action == "add_event":
            bot.edit_message_text(f"You selected {result} for your event. Now send the event description.",
                                  chat_id,
                                  c.message.message_id)
            bot.register_next_step_handler(c.message, get_event_description)
        
        elif action == "add_reminder":
            bot.edit_message_text(f"You selected {result} for your reminder. Now send the reminder description.",
                                  chat_id,
                                  c.message.message_id)
            bot.register_next_step_handler(c.message, get_reminder_description)
def get_event_description(message):
    event_description = message.text
    select_family_member(message, event_description, "event")

def get_reminder_description(message):
    reminder_description = message.text
    select_family_member(message, reminder_description, "reminder")

def select_family_member(message, description, action_type):
    chat_id = message.chat.id
    members = get_family_members()
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    
    for member in members:
        markup.add(types.KeyboardButton(member.name))
    
    user_sessions[chat_id]["description"] = description
    user_sessions[chat_id]["action_type"] = action_type

    bot.send_message(chat_id, "Select a family member for this action:", reply_markup=markup)
    bot.register_next_step_handler(message, process_family_member_selection)

def process_family_member_selection(message):
    chat_id = message.chat.id
    member_name = message.text
    member = get_family_member_by_name(member_name)
    
    if member:
        if user_sessions[chat_id]["action_type"] == "event":
            add_event(user_sessions[chat_id]["description"], user_sessions[chat_id]["date"].strftime('%Y-%m-%d'), member.id)
            bot.send_message(chat_id, f"Event added for {member_name} on {user_sessions[chat_id]['date']}")
        
        elif user_sessions[chat_id]["action_type"] == "reminder":
            add_reminder_to_db(user_sessions[chat_id]["text"], user_sessions[chat_id]["date"].strftime('%Y-%m-%d'), member.id)
            bot.send_message(chat_id, f"Reminder added for {member_name} on {user_sessions[chat_id]['date']}")

        del user_sessions[chat_id]  # Очищаем сессию пользователя
    else:
        bot.send_message(chat_id, "Invalid family member. Try again.")