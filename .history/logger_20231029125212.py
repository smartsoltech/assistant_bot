import functools
import logging

logger = logging.getLogger(__name__)

def log_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} executed successfully with arguments: {args} and keyword arguments: {kwargs}.")
            return result
        except Exception as e:
            logger.error(f"Error occurred in {func.__name__}: {str(e)}")
            raise e
    return wrapper