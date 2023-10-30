
import bot_handlers
from db_operations import init_db
from dotenv import load_dotenv, find_dotenv
from os import getenv
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(f"{__name__}.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)



if __name__ == '__main__':
    init_db()
    bot_handlers.prepare()
    
    bot_handlers.bot.polling(none_stop=True)
