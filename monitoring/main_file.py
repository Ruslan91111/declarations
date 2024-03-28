"""Запуск всего кода, который содержится в пакете"""
import datetime
import logging
import os
import shutil
import sys

import pandas as pd

from exceptions import PathNotPass, FileNotExisting
from gold_data_manager import launch_gold_module
from monitoring_in_web import launch_checking

##################################################################################
# Сообщения для пользователя.
##################################################################################
MESSAGE_FOR_USER_VERIFIABLE_FILE = (
    'Убедитесь, что файл Excel, нуждающийся в проверке, находится на рабочем столе.\n'
    'Введите название файла, без пути и расширения, после чего нажмите <Enter>.\n'
    'Надежнее всего скопировать наименование файла в свойствах файла\n'
    'или скопировать наименование файла при переименовании\n>>>')


##################################################################################
# Пути к файлам.
##################################################################################
MONTH = datetime.datetime.now().strftime('%B')  # Определяем месяц
FILE_FOR_CHECKING = r'./АМ по всем регионам Декабрь 2023 ОКДК.xlsx'
FILE_FOR_TWO_COLUMNS = r'.\two_columns_%s.xlsx' % MONTH
FILE_GOLD = r'./gold_data_%s.xlsx' % MONTH
FILE_RESULT = r'.\result_data_after_web_%s.xlsx' % MONTH
LOGGING_FILE = r'.\monitoring.log'
PATH_TO_DESKTOP = "c:\\Users\\impersonal\\Desktop\\"


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
    path_from_user = PATH_TO_DESKTOP + path_from_user + '.xlsx'

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
        'Порядковый номер АМ': range(1, len(df['Товар']) + 1),
        'Код товара': df['Код товара'],
        'Наименование товара': df['Товар'],
    })
    with pd.ExcelWriter(file_of_results, mode='w') as writer:
        new_df.to_excel(writer, index=False)


##################################################################################
# Автономный запуск программы.
##################################################################################
def automatic_launch_program():
    """
    Запуск всего кода, который содержится в пакете.

    Проверяется на какой стадии проверки находится проверка конкретного
    файла. Проверяет создан ли файл из двух колонок: с кодом и наименованием товара.
    Далее проверяет, создан ли файл с данными из ГОЛД. Если не создан,
    то создает и начинает заполнять данными. Если создан, но не заполнен до конца,
    то продолжает заполнять. Если файл ГОЛД полностью сформирован, то
    запускает сбор и проверку данных на интернет-ресурсах.
    """

    # Файл для проверки, получить путь от пользователя через ввод.
    checking_file = get_path_for_existing_file(MESSAGE_FOR_USER_VERIFIABLE_FILE)

    # Проверяем существует ли файл с двумя колонками, если нет, то создаем такой файл.
    if not os.path.isfile(FILE_FOR_TWO_COLUMNS):
        create_sheet_write_codes_and_names(checking_file)
        logging.info("Создан файл %s", FILE_FOR_TWO_COLUMNS)
    else:
        logging.info("Файл %s уже существует.", FILE_FOR_TWO_COLUMNS)

    # Проверяем существует ли файл ГОЛД, если нет, то создаем его и начинаем наполнять данными.
    if not os.path.isfile(FILE_GOLD):
        launch_gold_module(30, FILE_FOR_TWO_COLUMNS, FILE_GOLD)

    # Если файл ГОЛД есть, но в нем не все строки, то продолжаем наполнять данными из ГОЛД.
    else:
        logging.info("Файл %s уже существует.", FILE_GOLD)
        two_columns = pd.read_excel(FILE_FOR_TWO_COLUMNS)
        gold = pd.read_excel(FILE_GOLD)

        if len(gold) == 0:
            launch_gold_module(50, FILE_FOR_TWO_COLUMNS, FILE_GOLD)
            logging.info("Начата проверка в ГОЛД.")

        elif two_columns['Порядковый номер АМ'].iloc[-1] != gold['Порядковый номер АМ'].iloc[-1]:
            logging.info(f"Не все строки проверены в GOLD. "
                         f"Последний номер продукта в файле {FILE_FOR_TWO_COLUMNS} - "
                         f"{two_columns['Порядковый номер АМ'].iloc[-1]}. \n "
                         f"Последний номер продукта в файле {FILE_GOLD} - "
                         f"{gold['Порядковый номер АМ'].iloc[-1]}")
            logging.info("Продолжается проверка в ГОЛД.")
            launch_gold_module(50, FILE_FOR_TWO_COLUMNS, FILE_GOLD)

    # Проверяем существует ли файл с результатами.
    # Если файла с результатами нет, то создаем его и запускаем проверку в вебе.
    if not os.path.isfile(FILE_RESULT):
        launch_checking(50, FILE_GOLD, FILE_RESULT)
    # Если файл с результатами есть, но в нем не все строки, то продолжаем наполнять данными.
    else:
        logging.info("Файл %s уже существует.", FILE_RESULT)
        result = pd.read_excel(FILE_RESULT)
        gold = pd.read_excel(FILE_GOLD)

        # Проверяем совпадает ли по количеству строк файлы результатов и голд-данных.
        if len(result) < len(gold):
            logging.info(f"Не все строки проверены после на интернет-ресурсах после GOLD. "
                         f"Длина файла {FILE_RESULT} - {len(result)} строк. \n "
                         f"Длина файла {FILE_GOLD} - {len(gold)} строк. ")
            logging.info("Продолжается проверка на интернет-ресурсах.")
            launch_checking(500, FILE_GOLD, FILE_RESULT)

        # Если в интернете проверены все строки, полученные из ГОЛД.
        else:
            logging.info("Проверка полностью завершена.")
            # Готовый результат копируем на рабочий стол.
            destination_file = os.path.join(
                PATH_TO_DESKTOP, os.path.basename('Результат проверки мониторинга.xlsx'))
            shutil.copyfile(FILE_RESULT, destination_file)
            logging.info(f'Файл скопирован на рабочий стол: {destination_file}')
            print(f'Проверка полностью завершена. \nФайл скопирован на рабочий стол: {destination_file}')
            sys.exit()


if __name__ == '__main__':
    automatic_launch_program()
