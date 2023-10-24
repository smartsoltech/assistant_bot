# main.py

import bot_handlers
from db_operations import init_db

if __name__ == '__main__':
    init_db()
    bot_handlers.bot.polling(none_stop=True)
