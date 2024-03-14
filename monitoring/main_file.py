"""Запуск всего кода, который содержится в пакете"""
import datetime
import logging
import os

import pandas as pd

from exceptions import PathNotPass, FileNotExisting
from gold_data_manager import launch_gold_module
from monitoring_in_web import launch_checking


##################################################################################
# Сообщения для пользователя.
##################################################################################
MESSAGE_FOR_USER_VERIFIABLE_FILE = (
    'Введите полный путь до файла xlsx, нуждающегося в проверке, '
    'в том числе название файла и расширение:\n>>>')


##################################################################################
# Пути к файлам.
##################################################################################
MONTH = datetime.datetime.now().strftime('%B')  # Определяем месяц
FILE_FOR_CHECKING = r'./АМ по всем регионам Декабрь 2023 ОКДК.xlsx'
FILE_FOR_TWO_COLUMNS = r'.\two_columns_%s.xlsx' % MONTH
FILE_GOLD = r'./gold_data_%s.xlsx' % MONTH
FILE_RESULT = r'.\result_data_after_web_%s.xlsx' % MONTH
LOGGING_FILE = r'.\monitoring.log'


##################################################################################
# Логирование.
##################################################################################
logging.basicConfig(
    level=logging.INFO,
    filename=LOGGING_FILE,
    filemode="a",
    encoding='utf-8',
    format="%(asctime)s %(levelname)s %(message)s",
)


##################################################################################
# Функции для взаимодействия с пользователем.
##################################################################################
def get_path_for_existing_file(message_for_user: str) -> str:
    """Получить путь от пользователя к существующему файлу."""
    path_from_user = input(message_for_user)
    # Если путь указан неверно.
    if not path_from_user:
        raise PathNotPass
    # Если файл не существует.
    if not os.path.isfile(path_from_user):
        raise FileNotExisting

    return path_from_user


##################################################################################
# Функция формирующая колонки в файле с результатами.
##################################################################################
def create_sheet_write_codes_and_names(file_for_checking: str,
                                       file_of_results: str = FILE_FOR_TWO_COLUMNS):
    """
    Читает изначальный файл для мониторинга, берет из него две колонки:
    наименование и код товара, создает xlsx файл, в котором сохраняет данные два столбца:
    """
    df = pd.read_excel(file_for_checking)
    new_df = pd.DataFrame({
        'Порядковый номер АМ': range(1, len(df) - 1),
        'Код товара': df['Unnamed: 6'][2:],
        'Наименование товара': df['Unnamed: 7'][2:],
    })
    with pd.ExcelWriter(file_of_results, mode='w') as writer:
        new_df.to_excel(writer, index=False)


##################################################################################
# Автономный запуск программы.
##################################################################################
def automatic_launch_program():
    """Запуск всего кода, который содержится в пакете.
    Проверяется на какой стадии проверки находится проверка конкретного
    файла."""
    # Файл для проверки, получить путь от пользователя через ввод.
    checking_file = get_path_for_existing_file(MESSAGE_FOR_USER_VERIFIABLE_FILE)

    # Проверка и создание файла с двумя колонками.
    if not os.path.isfile(FILE_FOR_TWO_COLUMNS):
        create_sheet_write_codes_and_names(checking_file)
        logging.info("Создан файл %s", FILE_FOR_TWO_COLUMNS)
    else:
        logging.info("Файл %s уже существует.", FILE_FOR_TWO_COLUMNS)

    # Если файла ГОЛД нет, создаем его и начинаем наполнять данными из ГОЛД.
    if not os.path.isfile(FILE_GOLD):
        launch_gold_module(30, FILE_FOR_TWO_COLUMNS, FILE_GOLD)
    # Если файл ГОЛД есть, но в нем не все строки, то продолжаем наполнять данными из ГОЛД.
    else:
        logging.info("Файл %s уже существует.", FILE_GOLD)
        two_columns = pd.read_excel(FILE_FOR_TWO_COLUMNS)
        gold = pd.read_excel(FILE_GOLD)
        if len(two_columns) > len(gold):
            logging.info(f"Не все строки проверены в GOLD. Длина {FILE_FOR_TWO_COLUMNS} - "
                         f"{len(two_columns)}. \n Длина {FILE_GOLD} - "
                         f"{len(gold)}")
            launch_gold_module(50, FILE_FOR_TWO_COLUMNS, FILE_GOLD)

    # Если файла с результатами нет.
    if not os.path.isfile(FILE_RESULT):
        launch_checking(50, FILE_GOLD, FILE_RESULT)

    else:  # Если файл с результатами есть, но в нем не все строки, то продолжаем наполнять данными.
        logging.info("Файл %s уже существует.", FILE_RESULT)
        result = pd.read_excel(FILE_RESULT)
        gold = pd.read_excel(FILE_GOLD)
        if result['Порядковый номер АМ'].iloc[-1] != gold['Порядковый номер АМ'].iloc[-1]:

            logging.info(f"Не все строки проверены после на интернет-ресурсах после GOLD. "
                         f"Последняя строка в файле {FILE_RESULT} - "
                         f"{result['Порядковый номер АМ'].iloc[-1]}. \n "
                         f"Последняя строка в файле {FILE_GOLD} - "
                         f"{gold['Порядковый номер АМ'].iloc[-1]}")
            logging.info("Продолжается проверка на интернет-ресурсах.")

            launch_checking(50, FILE_GOLD, FILE_RESULT)


if __name__ == '__main__':
    automatic_launch_program()
