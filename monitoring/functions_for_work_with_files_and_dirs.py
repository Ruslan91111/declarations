""" Модуль с функциями для работы с файлами, директориями, процессами. """
import json
import os
import random
import time

import openpyxl
import pandas as pd
import psutil
import py_win_keyboard_layout

from monitoring.logger_config import logger


def return_or_create_dir(path_to_dir: str):
    """ Вернуть или создать директорию. """
    if not os.path.isdir(path_to_dir):
        os.mkdir(path_to_dir)
        logger.info("Создана директория <%s>." % path_to_dir)
    else:
        logger.info("Проверено наличие директории <%s>. "
                         "Директория существует. " % path_to_dir)
    return path_to_dir


def write_last_viewed_number_to_file(file: str, number: int) -> None:
    """Записать номер последнего просмотренного документа в файл."""
    with open(file, 'w', encoding='utf-8') as file:
        file.write(str(number))


def read_last_viewed_number_from_file(file: str) -> int:
    """Прочитать номер последнего просмотренного документа из файла."""
    if not os.path.isfile(file):
        with open(file, 'w', encoding='utf-8') as file:
            file.write('0')
            return 0
    with open(file, 'r', encoding='utf-8') as file:
        last_number = int(file.read())
        return last_number


def return_or_create_xlsx_file(xlsx_file: str) -> str:
    """Проверить существует ли xlsx файл, если да, то открыть его, если нет, то создать."""
    if os.path.isfile(xlsx_file):
        return xlsx_file
    workbook = openpyxl.Workbook()
    # Создаем лист и делаем его видимым
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.sheet_view.showGridLines = True
    workbook.save(xlsx_file)
    logger.info("Создан файл %s" % xlsx_file)
    return xlsx_file


def read_and_return_dict_from_json_file(json_file: str) -> dict:
    """ Вернуть словарь из JSON файла. """
    with open(json_file, 'r') as file:
        return json.load(file)


def check_process_in_os(process: str):
    """Проверяет запущен ли процесс в ОС"""
    for proc in psutil.process_iter():  # Перебираем текущие процессы.
        name = proc.name()
        if name == process:
            return proc  # Возвращаем работающий процесс
    return None


def terminate_the_proc(process: str) -> None:
    """ Закрыть переданный процесс."""
    # Перебираем текущие процессы и ищем нужный нам процесс.
    for proc in psutil.process_iter():
        name = proc.name()
        # Если нужный процесс запущен.
        if name == process:
            proc.terminate()
            break


def return_or_create_new_df(df, columns):
    """Вернуть или создать DataFrame для итогового результата. """
    if df is None:  # Если файл пустой, создаем DataFrame.
        new_df = pd.DataFrame(columns=columns)
    else:  # Если нет, то читаем существующий
        new_df = pd.read_excel(df)
    return new_df


def change_layout_on_english():
    """ Переключить на английскую раскладку. """
    py_win_keyboard_layout.change_foreground_window_keyboard_layout(0x04090409)


def random_delay_from_1_to_3():
    time.sleep(random.randint(1, 3))
