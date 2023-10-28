import functools
import logging

def log_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} executed successfully with arguments: {args} and keyword arguments: {kwargs}.")
            return result
        except Exception as e:
            logger.exception(f"Error in {func.__name__} with arguments: {args} and keyword arguments: {kwargs}. Error message: {str(e)}")
            raise
    return wrapper