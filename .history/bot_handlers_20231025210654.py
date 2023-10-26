# bot_handlers.py
import telebot
from telebot import types
from db_operations import (add_event, add_reminder, get_family_members, add_reminder_to_db, 
                          get_family_member_by_name, find_contact_by_name_or_phone, 
                          get_reminders_by_family_member, add_contact)
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

@bot.message_handler(commands=['migrate'])
def migrate(message):
    """Handle migration command from user."""
    chat_id = message.chat.id
    try:
        password = message.text.split(' ')[1]
    except IndexError:
        bot.send_message(chat_id, "Please provide the migration password!")
        return

    if password == MIGRATION_PASSWORD:
        try:
            # Run the migration command
            subprocess.check_call(['alembic', 'upgrade', 'head'])
            bot.send_message(chat_id, "Migration successfully completed!")
        except subprocess.CalledProcessError:
            bot.send_message(chat_id, "Migration failed. Check server logs for details.")
    else:
        bot.send_message(chat_id, "Wrong migration password!")

# Dictionary to store current user state
user_sessions = {}

@bot.message_handler(commands=['start'])
def start(m):
    """Handle start command from user."""
    bot.send_message(m.chat.id, "Welcome! Use commands to interact with me.")

@bot.message_handler(commands=['addmember'])
def add_family_member(message):
    """Prompt user to add a new family member."""
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please send the name of the family member you want to add.")
    bot.register_next_step_handler(message, save_family_member_name)

def save_family_member_name(message):
    """Save provided family member name into the database."""
    member_name = message.text
    member_id = add_member_to_db(member_name)
    bot.send_message(message.chat.id, f"Family member '{member_name}' added with ID {member_id}.")

@bot.message_handler(commands=['getmember'])
def get_family_member(message):
    """Retrieve a family member's information."""
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please send the name of the family member you want to retrieve.")
    bot.register_next_step_handler(message, send_family_member_info)

def send_family_member_info(message):
    """Send back the information of the specified family member."""
    member_name = message.text
    member = get_family_member_by_name(member_name)
    if member:
        bot.send_message(message.chat.id, f"Family member found: {member.name}")
    else:
        bot.send_message(message.chat.id, "Family member not found.")

@bot.message_handler(commands=['addevent'])
def add_new_event(message):
    """Initiate process to add a new event."""
    chat_id = message.chat.id
    calendar, step = DetailedTelegramCalendar().build()
    user_sessions[chat_id] = {"action": "add_event"}
    bot.send_message(chat_id, f"Select {LSTEP[step]} for your event", reply_markup=calendar)

@bot.message_handler(commands=['addreminder'])
def add_new_reminder(message):
    """Initiate process to add a new reminder."""
    chat_id = message.chat.id
    calendar, step = DetailedTelegramCalendar().build()
    user_sessions[chat_id] = {"action": "add_reminder"}
    bot.send_message(chat_id, f"Select {LSTEP[step]} for your reminder", reply_markup=calendar)

@bot.message_handler(commands=['getreminders'])
def show_reminders(message):
    """Display reminders for family members."""
    chat_id = message.chat.id
    members = get_family_members()

    if not members:
        bot.send_message(chat_id, "You have no family members added!")
        return

    keyboard = types.InlineKeyboardMarkup()
    for member in members:
        callback_data = f"showreminders:{member.id}"
        keyboard.add(types.InlineKeyboardButton(text=member.name, callback_data=callback_data))

    bot.send_message(chat_id, "Select a family member to see their reminders:", reply_markup=keyboard)

@bot.message_handler(content_types=['document'])
def handle_vcard(message):
    """Process received vCard document."""
    chat_id = message.chat.id

    # Download vCard file from user
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Save and parse the vCard content
    with open("temp_contact_file.vcf", 'wb') as new_file:
        new_file.write(downloaded_file)

    with open("temp_contact_file.vcf", 'r') as contact_file:
        vcard = vobject.readOne(contact_file.read())
        full_name = vcard.fn.value
        try:
            telephone = vcard.tel.value
        except AttributeError:
            telephone = "Not provided"

        ask_to_save_contact(chat_id, full_name, telephone)

def ask_to_save_contact(chat_id, full_name, telephone):
    """Ask user whether to save parsed contact information."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    yes_button = types.InlineKeyboardButton("Yes", callback_data="save_contact_yes")
    no_button = types.InlineKeyboardButton("No", callback_data="save_contact_no")
    keyboard.add(yes_button, no_button)
    bot.send_message(chat_id, f"Do you want to save the contact?\nName: {full_name}\nPhone: {telephone}", reply_markup=keyboard)

# [Rest of the code...]
