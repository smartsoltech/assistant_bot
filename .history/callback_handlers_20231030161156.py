# callback_handlers.py

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telebot import types
from db_operations import (get_family_members, 
                           get_reminders_by_family_member, 
                           add_contact, 
                           full_reset, 
                           add_event, 
                           add_reminder,
                           show_member_reminders,)
from logger import log_decorator
from telebot.apihelper import ApiTelegramException
import logging
import json

logger = logging.getLogger(__name__)

# Инициализация пользовательских сессий
from main import user_sessions


@log_decorator
def handle_save_contact_query(bot, call, callback_data):
    """
    Обрабатывает callback-запрос на сохранение контакта.

    Args:
    - bot: объект бота.
    - call: callback-запрос.
    - callback_data: данные callback-запроса.

    """
    try:
        first_name = callback_data["first_name"]
        last_name = callback_data["last_name"]
        telephone = callback_data["telephone"]
        chat_id = call.message.chat.id
        
        add_contact(chat_id, telephone, first_name, last_name)
        bot.edit_message_text(chat_id=chat_id, 
                              message_id=call.message.message_id, 
                              text=f"Контакт {first_name} {last_name} ({telephone}) был добавлен!")

    except KeyError:
        bot.answer_callback_query(call.id, "Ошибка при обработке данных контакта")


@log_decorator
def handle_family_member_selection(bot, call):
    """Обрабатывает выбор члена семьи пользователем."""
    member_id = call.data.split(":")[1]
    chat_id = call.message.chat.id

    if chat_id not in user_sessions:
        bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return

    user_sessions[chat_id]["family_member_id"] = member_id
    bot.edit_message_text("Now, send the reminder description.",
                          chat_id,
                          call.message.message_id)


@log_decorator
def handle_calendar_callback(bot, call):
    """Обрабатывает callback-запросы от календаря."""
    result, key, step = DetailedTelegramCalendar().process(call.data)
    chat_id = call.message.chat.id
    
    if chat_id not in user_sessions or "action" not in user_sessions[chat_id]:
        logger.error(f"No action found in user_sessions for chat_id: {chat_id}")
        bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return

    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}", chat_id, call.message.message_id, reply_markup=key)
    elif result:
        action = user_sessions[chat_id]["action"]
        user_sessions[chat_id]["date"] = result
        # Продолжаем в зависимости от действия (напоминание или событие)
        # ...


@log_decorator
def handle_all_callbacks(bot, call):
    """Обрабатывает все callback-запросы."""
    try:
        # Обработка календаря
        if call.data.startswith('cbcal_'):
            handle_calendar_callback(bot, call)
        # Обработка напоминаний
        elif call.data.startswith('showreminders:'):
            show_member_reminders(bot, call)
        # Сохранение контакта
        elif "action" in call.data and json.loads(call.data).get("action") == "save_contact_yes":
            handle_save_contact_query(bot, call, json.loads(call.data))
        # Остальные действия
        # ...

    except ApiTelegramException as e:
        logger.error(f"Telegram API Error while handling callback: {e}")
    except Exception as e:
        logger.error(f"Error handling callback: {e}")

# Другие функции...

def text_handle(bot, message):
    """Обработчик текстовых сообщений."""
    if message.text:
        bot.send_message(message.from_user.id, "Я не понимаю Вас!")
# callback_handlers.py

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telebot import types
from db_operations import (get_family_members, 
                           get_reminders_by_family_member, 
                           add_contact, 
                           full_reset, 
                           add_event, 
                           add_reminder)
from logger import log_decorator
from telebot.apihelper import ApiTelegramException
import logging
import json

logger = logging.getLogger(__name__)

# Инициализация пользовательских сессий
from main import user_sessions


@log_decorator
def handle_save_contact_query(bot, call, callback_data):
    """
    Обрабатывает callback-запрос на сохранение контакта.

    Args:
    - bot: объект бота.
    - call: callback-запрос.
    - callback_data: данные callback-запроса.

    """
    try:
        first_name = callback_data["first_name"]
        last_name = callback_data["last_name"]
        telephone = callback_data["telephone"]
        chat_id = call.message.chat.id
        
        add_contact(chat_id, telephone, first_name, last_name)
        bot.edit_message_text(chat_id=chat_id, 
                              message_id=call.message.message_id, 
                              text=f"Контакт {first_name} {last_name} ({telephone}) был добавлен!")

    except KeyError:
        bot.answer_callback_query(call.id, "Ошибка при обработке данных контакта")


@log_decorator
def handle_family_member_selection(bot, call):
    """Обрабатывает выбор члена семьи пользователем."""
    member_id = call.data.split(":")[1]
    chat_id = call.message.chat.id

    if chat_id not in user_sessions:
        bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return

    user_sessions[chat_id]["family_member_id"] = member_id
    bot.edit_message_text("Now, send the reminder description.",
                          chat_id,
                          call.message.message_id)


@log_decorator
def handle_calendar_callback(bot, call):
    """Обрабатывает callback-запросы от календаря."""
    result, key, step = DetailedTelegramCalendar().process(call.data)
    chat_id = call.message.chat.id
    
    if chat_id not in user_sessions or "action" not in user_sessions[chat_id]:
        logger.error(f"No action found in user_sessions for chat_id: {chat_id}")
        bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return

    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}", chat_id, call.message.message_id, reply_markup=key)
    elif result:
        action = user_sessions[chat_id]["action"]
        user_sessions[chat_id]["date"] = result
        # Продолжаем в зависимости от действия (напоминание или событие)
        # ...


@log_decorator
def handle_all_callbacks(bot, call):
    """Обрабатывает все callback-запросы."""
    try:
        # Обработка календаря
        if call.data.startswith('cbcal_'):
            handle_calendar_callback(bot, call)
        # Обработка напоминаний
        elif call.data.startswith('showreminders:'):
            show_member_reminders(bot, call)
        # Сохранение контакта
        elif "action" in call.data and json.loads(call.data).get("action") == "save_contact_yes":
            handle_save_contact_query(bot, call, json.loads(call.data))


    except ApiTelegramException as e:
        logger.error(f"Telegram API Error while handling callback: {e}")
    except Exception as e:
        logger.error(f"Error handling callback: {e}")

# Другие функции...

def text_handle(bot, message):
    """Обработчик текстовых сообщений."""
    if message.text:
        bot.send_message(message.from_user.id, "Я не понимаю Вас!")
