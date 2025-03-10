"""
Модуль с функциями для работы с файлами, директориями, процессами.

Функции:
    - return_or_create_dir:
        Вернуть или создать директорию.

    - write_numb_to_file:
        Записать номер последнего просмотренного документа в файл.

    - read_numb_from_file:
        Прочитать номер последнего просмотренного документа из файла.

    - return_or_create_xlsx:
        Проверить существует ли xlsx файл, если да, то вернуть его, если нет, то создать.

    - dict_from_json_file:
        Вернуть словарь из JSON файла.

    - check_process_in_os:
        Проверяет запущен ли процесс в ОС.

    - terminate_the_proc:
        Закрыть переданный процесс.

    -return_or_create_new_df:
        Вернуть или создать DataFrame.

    - change_layout_on_english:
        Переключить на английскую раскладку.

    - random_delay_from_1_to_3:
        Выполнить случайную задержку.

    - create_copy_of_file:
        Сделать копию файла.

"""
import json
import os
import random
import time

import openpyxl
import pandas as pd
import psutil
import py_win_keyboard_layout

from common.constants import MsgForUser
from common.logger_config import logger


def write_numb_to_file(file: str, number: int) -> None:
    """Записать номер последнего просмотренного документа в файл."""
    with open(file, 'w', encoding='utf-8') as file:
        file.write(str(number))


def read_numb_from_file(file: str) -> int:
    """Прочитать номер последнего просмотренного документа из файла."""
    if not os.path.isfile(file):
        with open(file, 'w', encoding='utf-8') as file:
            file.write('0')
            return 0
    with open(file, 'r', encoding='utf-8') as file:
        last_number = int(file.read())
        return last_number


def return_or_create_xlsx(xlsx_file: str) -> str:
    """ Проверить существует ли xlsx файл, если да, то вернуть его, если нет, то создать. """
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


def dict_from_json_file(json_file: str) -> dict:
    """ Вернуть словарь из JSON файла. """
    with open(json_file, 'r') as file:
        return json.load(file)


def check_process_in_os(process: str):
    """ Проверяет запущен ли процесс в ОС """
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
            time.sleep(10)
            break


def return_or_create_new_df(df, columns):
    """Вернуть или создать DataFrame. """
    if len(df) == 0:  # Если файл пустой, создаем DataFrame.
        return pd.DataFrame(columns=columns)
    return df


def change_layout_on_english():
    """ Переключить на английскую раскладку. """
    py_win_keyboard_layout.change_foreground_window_keyboard_layout(0x04090409)


def random_delay():
    """ Выполнить случайную задержку. """
    time.sleep(random.randint(3, 5))


def create_copy_of_file(dir_type_of_stage, row_name, new_df):
    """ Сделать копию файла"""
    from common.constants import COPIES_GOLD, COPIES_WEB

    file_name = r'./copy_lane_%s.xlsx' % (str(row_name))

    if dir_type_of_stage == 'copies_of_gold':
        copy_xlsx_file = COPIES_GOLD / file_name
    if dir_type_of_stage == 'copies_of_web':
        copy_xlsx_file = COPIES_WEB / file_name

    new_df.to_excel(copy_xlsx_file, index=False)
    logger.info(f"Создана копия файла. Путь к файлу {copy_xlsx_file}")


def prepare_df_for_work(result_file: str, columns: list):
    """ Подготовить DataFrame для итогов мониторинга """
    df = pd.read_excel(return_or_create_xlsx(result_file))
    df = return_or_create_new_df(df, columns=columns)
    return df
