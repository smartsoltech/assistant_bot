
import bot_handlers
from db_operations import init_db
from dotenv import load_dotenv, find_dotenv
from os import getenv

load_dotenv('.env')
BOT_TOKEN = getenv('TG_TOKEN')

if __name__ == '__main__':
    init_db()
    bot_handlers.bot.polling(none_stop=True)
