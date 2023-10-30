
import bot_handlers
from db_operations import init_db
from dotenv import load_dotenv, find_dotenv
from os import getenv

user_sessions={}
chat_id=""

def initialize_user_session(chat_id, action):
    user_sessions[chat_id] = {"action": action}
    
if __name__ == '__main__':
    init_db()
    bot_handlers.prepare()
    
    bot_handlers.bot.polling(none_stop=True)
