"""
Конфигурация логгинга.
"""
import logging
from pathlib import Path

from common.constants import DIR_CURRENT_MONTH

BASE_DIR = Path(__file__).resolve().parent.parent.parent

LOG_FILE = DIR_CURRENT_MONTH / 'log_file.log'

logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# Удаление всех существующих обработчиков из логгера
if logger.hasHandlers():
    logger.handlers.clear()

# Создание file handler для записи в файл
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')

file_handler.setLevel(logging.DEBUG)

# Создание форматтера и добавление его к file handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавление file handler к логгеру
logger.addHandler(file_handler)

# Создание stream handler для вывода в консоль
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)
# console_handler.setFormatter(formatter)

# Добавление stream handler к логгеру
# logger.addHandler(console_handler)
