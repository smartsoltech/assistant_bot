# bot_handlers.py
import telebot
from telebot import types
from db_operations import add_event, add_reminder, get_family_members, add_reminder_to_db, get_family_member_by_name
from db_operations import find_contact_by_name_or_phone, get_reminders_by_family_member, add_contact
from os import getenv
from dotenv import load_dotenv
from datetime import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from db_operations import add_family_member as add_member_to_db
from telebot.ext import CommandHandler
from alembic import command
from alembic.config import Config

def prepare():
    load_dotenv('.env')
    token = getenv('TG_TOKEN')
    MIGRATION_PASSWORD = getenv('MIGRATION_PASSWORD')
    return token, MIGRATION_PASSWORD


bot_token, MIGRATION_PASSWORD = prepare()

bot = bot_token

@bot.message_handler(commands=['migrate'])
def migrate(message):
    chat_id = message.chat.id
    text = message.text.split()
    
    # Проверяем, что пароль предоставлен и верен
    if len(text) != 2 or text[1] != MIGRATION_PASSWORD:
        bot.send_message(chat_id, "Invalid password or syntax.")
        return

    # Запускаем миграцию
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    bot.send_message(chat_id, "Migration completed!")

# Добавьте этот обработчик к диспетчеру
dp.add_handler(CommandHandler("migrate", migrate)
               
user_sessions = {}  # словарь для хранения текущего состояния пользователя

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "Welcome! Use commands to interact with me.")

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id

    if not message.contact:
        bot.send_message(chat_id, "Please send a valid contact.")
        return

    # Извлекаем информацию из контакта
    phone_number = message.contact.phone_number
    first_name = message.contact.first_name
    last_name = message.contact.last_name

    # Сохраняем контакт в базе данных
    add_contact(chat_id, phone_number, first_name, last_name)
    bot.send_message(chat_id, f"Contact {first_name} {last_name} saved!")
    
@bot.message_handler(commands=['addmember'])
def add_family_member(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please send the name of the family member you want to add.")
    bot.register_next_step_handler(message, save_family_member_name)

def save_family_member_name(message):
    member_name = message.text
    member_id = add_member_to_db(member_name)  # вызываем функцию из db_operations
    bot.send_message(message.chat.id, f"Family member '{member_name}' added with ID {member_id}.")

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
@bot.message_handler(commands=['getreminders'])
def show_reminders(message):
    chat_id = message.chat.id
    members = get_family_members()  # получаем список всех членов семьи

    if not members:
        bot.send_message(chat_id, "You have no family members added!")
        return

    keyboard = types.InlineKeyboardMarkup()
    for member in members:
        callback_data = f"showreminders:{member.id}"  # формат: команда:id_члена_семьи
        keyboard.add(types.InlineKeyboardButton(text=member.name, callback_data=callback_data))

    bot.send_message(chat_id, "Select a family member to see their reminders:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("showreminders"))
def show_member_reminders(call):
    member_id = int(call.data.split(":")[1])  # извлекаем id члена семьи из callback_data
    reminders = get_reminders_by_family_member(member_id)

    if not reminders:
        bot.send_message(call.message.chat.id, "This family member has no reminders!")
        return

    reminders_text = "\n".join([f"{reminder.date} - {reminder.description}" for reminder in reminders])
    bot.send_message(call.message.chat.id, f"Reminders:\n{reminders_text}")
    
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
            add_reminder_to_db(description=user_sessions[chat_id]["description"], date=user_sessions[chat_id]["date"], member_id=member.id)

            # add_reminder_to_db(user_sessions[chat_id]["description"], user_sessions[chat_id]["date"].strftime('%Y-%m-%d'), member.id)
            bot.send_message(chat_id, f"Reminder added for {member_name} on {user_sessions[chat_id]['date']}")

        del user_sessions[chat_id]  # Очищаем сессию пользователя
    else:
        bot.send_message(chat_id, "Invalid family member. Try again.")
        
