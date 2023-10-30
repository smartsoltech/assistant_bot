from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telebot import types
from db_operations import (get_family_members, 
                           get_reminders_by_family_member, 
                           add_contact, 
                           full_reset, 
                           add_event, 
                           add_reminder,
                           add_family_member)
from logger import log_decorator
from telebot.apihelper import ApiTelegramException
import logging
from main import user_sessions, chat_id, initialize_user_session, print_user_sessions
import json 

logger = logging.getLogger(__name__)

@log_decorator
def handle_save_contact_query(bot, call, callback_data):
    try:
        first_name = callback_data["first_name"]
        last_name = callback_data["last_name"]
        telephone = callback_data["telephone"]
        chat_id = call.message.chat.id
        
        add_contact(chat_id, telephone, first_name, last_name)
        
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=call.message.message_id, 
            text=f"Контакт {first_name} {last_name} ({telephone}) был добавлен!"
        )

    except KeyError:
        bot.answer_callback_query(call.id, "Ошибка при обработке данных контакта")

        
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="Done!")
    
@log_decorator
def handle_family_member_selection(bot, call):
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
    result, key, step = DetailedTelegramCalendar().process(call.data)
    chat_id = call.message.chat.id
    
    if chat_id not in user_sessions or "action" not in user_sessions[chat_id]:
        logger.error(f"No action found in user_sessions for chat_id: {chat_id}")
        bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return
    
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              chat_id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        action = user_sessions[chat_id]["action"]
        user_sessions[chat_id]["date"] = result

        if action == "addevent":
            bot.edit_message_text(f"You selected {result} for your event. Now send the event description.",
                                  chat_id,
                                  call.message.message_id)
        elif action == "addreminder":
            # After selecting a date, let the user choose a family member
            members = get_family_members()
            markup = types.InlineKeyboardMarkup()
            for member in members:
                markup.add(types.InlineKeyboardButton(member.name, callback_data=f"choose_member:{member.id}"))
            bot.edit_message_text(f"You selected {result} for your reminder. Now choose a family member:",
                                  chat_id,
                                  call.message.message_id,
                                  reply_markup=markup)

@log_decorator
def show_member_reminders(bot, call):
    try:
        member_id = call.data.split(":")[1]
        reminders = get_reminders_by_family_member(member_id)
        if reminders:
            reminders_text = "\n".join([f"{reminder.id}. {reminder.text}" for reminder in reminders])
            bot.edit_message_text(f"Reminders for member {member_id}:\n{reminders_text}", call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(f"No reminders found for member {member_id}.", call.message.chat.id, call.message.message_id)
    except ApiTelegramException as e:
        logger.error(f"Telegram API Error in show_member_reminders: {e}")
    except Exception as e:
        logger.error(f"Error in show_member_reminders: {e}")


@log_decorator
def handle_all_callbacks(bot, call):
    try:
        if call.data.startswith('showreminders:'):
            show_member_reminders(bot, call)
        
        elif call.data in ["save_contact_yes", "save_contact_no"]:
            handle_save_contact_query(bot, call)
            if call.data == "save_contact_yes":
                add_contact()
        elif call.data == "full_reset_confirm":
            full_reset()
            bot.edit_message_text("Таблицы были успешно сброшены!", call.message.chat.id, call.message.message_id)
        elif call.data == "full_reset_cancel":
            bot.edit_message_text("Сброс отменен!", call.message.chat.id, call.message.message_id)

        else:
            logger.warning(f"Unknown callback data received: {call.data}")
            bot.answer_callback_query(call.id, "Неизвестный запрос")
    except ApiTelegramException as e:
        logger.error(f"Telegram API Error while handling callback: {e}")
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        
    try:
        callback_data = json.loads(call.data)
        action = callback_data.get("action")
        
        if action == "save_contact_yes":
            handle_save_contact_query(bot, call, callback_data)
        # Добавьте другие условия обработки здесь по необходимости
        else:
            bot.answer_callback_query(call.id, "Неизвестный запрос")

    except json.JSONDecodeError:
        bot.answer_callback_query(call.id, "Некорректные callback данные")
        
    try:
        if call.data.startswith('cbcal_'):
            handle_calendar_callback(bot, call)

        elif call.data.startswith('choose_member:'):
            handle_family_member_selection(bot, call)
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        
        
def text_handle(bot, message):
    if message.text:
        bot.send_message(message.from_user.id, "Я не понимаю Вас!")
        
@log_decorator
def handle_event_description_input(bot, message):
    chat_id = message.chat.id
    initialize_user_session(chat_id, "action")
    print_user_sessions()
    if chat_id not in user_sessions or "action" not in user_sessions[chat_id]:
        logger.error(f"No action found in user_sessions for chat_id: {chat_id}")
        bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return
    
    action = user_sessions[chat_id]["action"]
    date = user_sessions[chat_id]["date"]
    print_user_sessions()
    if action == "addevent":
        # Сохраняем событие в базу данных
        add_event(message.text, date, chat_id)  # Предположим, что chat_id является ID члена семьи
        bot.send_message(chat_id, "Ваше событие было добавлено!")

    elif action == "addreminder":
        # Сохраняем напоминание в базу данных
        add_reminder(message.text, date, chat_id)  # Предположим, что chat_id является ID члена семьи
        bot.send_message(chat_id, "Ваше напоминание было добавлено!")

    # Удаляем информацию из user_sessions, чтобы предотвратить путаницу
    del user_sessions[chat_id]
    
@log_decorator
def handle_new_member_input(bot, message):
    chat_id = message.chat.id
    print_user_sessions()
    # Создаем нового пользователя (или члена семьи) в базе данных
    add_family_member(first_name=message.text, last_name="", user_code="", chat_id=chat_id)
    
    bot.send_message(chat_id, "Новый пользователь был добавлен!")
    
    # Удаляем информацию из user_sessions, чтобы предотвратить путаницу
    del user_sessions[chat_id]
