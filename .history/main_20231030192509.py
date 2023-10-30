
import bot_handlers
from db_operations import init_db
from dotenv import load_dotenv, find_dotenv
from os import getenv
import json

user_sessions = {
    "chat_id": {
        "action": "some_action",
        "registration_open": False
    }
}

chat_id=""

def initialize_user_session(chat_id, action):
    user_sessions[chat_id] = {"action": action}
    
def print_user_sessions():
    session_content = json.dumps(user_sessions, indent=4, ensure_ascii=False)
    print(session_content)

if __name__ == '__main__':
    init_db()
    bot_handlers.prepare()
    
    bot_handlers.bot.polling(none_stop=True)
