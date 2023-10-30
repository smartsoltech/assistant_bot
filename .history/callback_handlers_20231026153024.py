from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telebot import types
from db_operations import get_family_members, get_reminders_by_family_member, add_contact
from logger import log_decorator

# user_sessions = {}

user_sessions={}

@log_function_call
@log_decorator
def handle_all_callbacks(bot, call):
    if call.data.startswith('calendar_'):
        handle_calendar_callback(bot, call)
    elif call.data.startswith('showreminders:'):
        show_member_reminders(bot, call)
    elif call.data in ["save_contact_yes", "save_contact_no"]:
        handle_save_contact_query(bot, call)
    else:
        bot.answer_callback_query(call.id, "Неизвестный запрос")

@log_function_call
@log_decorator
def handle_calendar_callback(bot, call):
    result, key, step = DetailedTelegramCalendar().process(call.data)
    chat_id = call.message.chat.id
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              chat_id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        action = user_sessions[chat_id]["action"]
        user_sessions[chat_id]["date"] = result

        if action == "add_event":
            bot.edit_message_text(f"You selected {result} for your event. Now send the event description.",
                                  chat_id,
                                  call.message.message_id)
        elif action == "add_reminder":
            bot.edit_message_text(f"You selected {result} for your reminder. Now send the reminder description.",
                                  chat_id,
                                  call.message.message_id)

@log_decorator
def show_member_reminders(bot, call):
    member_id = call.data.split(":")[1]
    reminders = get_reminders_by_family_member(member_id)
    if reminders:
        reminders_text = "\n".join([f"{reminder.id}. {reminder.text}" for reminder in reminders])
        bot.edit_message_text(f"Reminders for member {member_id}:\n{reminders_text}", call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text(f"No reminders found for member {member_id}.", call.message.chat.id, call.message.message_id)


@log_decorator
def handle_save_contact_query(bot, call):
    chat_id = call.message.chat.id
    if call.data == "save_contact_yes":
        full_name, telephone = call.message.text.split('\n')[1:3]
        full_name = full_name.split(":")[1].strip()
        telephone = telephone.split(":")[1].strip()
        add_contact(chat_id, full_name, telephone)
        bot.answer_callback_query(call.id, "Contact saved!")
    elif call.data == "save_contact_no":
        bot.answer_callback_query(call.id, "Contact not saved!")
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="Done!")
