import logging

logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('log_file.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def log_to_file_info(message):
    logger.info(message)


def log_to_file_error(message):
    logger.error(message)
