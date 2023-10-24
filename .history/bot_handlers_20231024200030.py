# bot_handlers.py

import telebot
from db_operations import save_contact

BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(content_types=['contact'])
def handle_received_contact(message):
    contact_info = message.contact
    name = contact_info.first_name + " " + (contact_info.last_name if contact_info.last_name else "")
    phone = contact_info.phone_number
    save_contact(name, phone)
    bot.send_message(message.chat.id, "Контакт успешно сохранен!")

# Дополнительные обработчики для других команд и сообщений могут быть добавлены здесь
