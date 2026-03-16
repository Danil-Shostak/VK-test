# logger.py
# Модуль логирования для VK Parser
import logging
import os
from datetime import datetime
from config import LOG_LEVEL, LOG_FILE

def get_logger(name: str) -> logging.Logger:
    """
    Создает и возвращает настроенный логгер
    
    Args:
        name: Имя логгера (обычно имя модуля)
    
    Returns:
        Настроенный объект логгера
    """
    logger = logging.getLogger(name)
    
    # Если логгер уже настроен, возвращаем его
    if logger.handlers:
        return logger
    
    # Уровень логирования
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик (если указан)
    if LOG_FILE:
        # Создаем директорию для логов, если нужно
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_execution_time(logger: logging.Logger):
    """
    Декоратор для логирования времени выполнения функции
    
    Usage:
        @log_execution_time(logger)
        def my_function():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.debug(f"Начало выполнения: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Завершено: {func.__name__} за {elapsed:.2f}с")
                return result
            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.error(f"Ошибка в {func.__name__} после {elapsed:.2f}с: {e}")
                raise
        return wrapper
    return decorator