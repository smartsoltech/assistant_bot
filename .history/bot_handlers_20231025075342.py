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
        user_sessions[chat_id]["date"] = result
        send_family_members_options(chat_id, user_sessions[chat_id]["action"])

def send_family_members_options(chat_id, action):
    """Отправить пользователю список доступных членов семьи."""
    family_members = get_family_members()
    if not family_members:
        bot.send_message(chat_id, "No family members found. Please add some first.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for member in family_members:
        callback_data = f"{action}_for_{member.id}"
        markup.add(types.InlineKeyboardButton(member.name, callback_data=callback_data))

    bot.send_message(chat_id, "Choose a family member:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_event_for_') or call.data.startswith('add_reminder_for_'))
def handle_family_member_selection(call):
    action, _, member_id = call.data.split("_")
    chat_id = call.message.chat.id

    if action == "add_event":
        user_sessions[chat_id]['family_member_id'] = member_id
        bot.send_message(chat_id, "Now send the event description.")
        bot.register_next_step_handler(call.message, get_event_description)

    elif action == "add_reminder":
        user_sessions[chat_id]['family_member_id'] = member_id
        bot.send_message(chat_id, "Now send the reminder description.")
        bot.register_next_step_handler(call.message, get_reminder_description)

def get_event_description(message):
    event_description = message.text
    date_obj = user_sessions[message.chat.id]['date']
    family_member_id = user_sessions[message.chat.id]['family_member_id']
    add_event(event_description, date_obj.strftime('%Y-%m-%d'), family_member_id)
    bot.send_message(message.chat.id, f"Event '{event_description}' on {date_obj.strftime('%Y-%m-%d')} added for family member {family_member_id}!")
    del user_sessions[message.chat.id]
