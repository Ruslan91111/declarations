""" Запуск всего кода, который содержится в пакете. """
import os
import sys

import pandas as pd

from monitoring_process.process_result_file import finish_monitoring, split_result_file, ResultFileNames
from monitoring_process.monitoring_in_web import launch_checking_in_web

base_path = os.path.join("C:\\Users\\impersonal\\Desktop\\declarations\\monitoring")
if base_path not in sys.path:
    sys.path.insert(0, base_path)
from gold.gold_manager import launch_gold_module
from common.logger_config import logger

from common.exceptions import FileNotPassedException, FileNotExistingException
from common.constants import Files, PATH_TO_DESKTOP, MsgForUser
from common.file_worker import change_layout_on_english


def create_gold_codes_file(file_for_checking: str,
                           file_of_results: str = Files.BEFORE_GOLD.value):
    """
    Читает изначальный файл для мониторинга, берет из него две колонки:
    наименование и код товара, создает xlsx файл, в котором сохраняет данные два столбца:
    """
    # Предварительно обработать dataframe. Убрать лишние первые строки и установить columns.
    df = pd.read_excel(file_for_checking)
    df.columns = df.iloc[0]
    df = df.drop([0]).reset_index(drop=True)

    new_df = pd.DataFrame({
        'Порядковый номер АМ': range(1, len(df['Товар']) + 1),
        'Код товара': df['Код товара'],
        'Наименование товара': df['Товар'],
    })

    with pd.ExcelWriter(file_of_results, mode='w') as writer:
        new_df.to_excel(writer, index=False)


def get_file_name_from_user(message_for_user: str) -> str:
    """ Наименование файла xlsx, находящегося на рабочем столе."""
    file_from_user = input(message_for_user)
    path_to_file_from_user = PATH_TO_DESKTOP + file_from_user + '.xlsx'
    logger.info(f'Передан файл - <{file_from_user}>')
    print(f'Передан файл - <{file_from_user}>')

    # Проверки передано ли название файла для проверки и существует ли файл.
    if not file_from_user:
        exception = FileNotPassedException()
        print(exception.msg, '\nЗапустите программу еще раз')
        raise exception

    if not os.path.isfile(path_to_file_from_user):
        exception = FileNotExistingException()
        print(exception.msg, '\nЗапустите программу еще раз')
        raise exception

    print(MsgForUser.VALID_NAME_OF_FILE.value)
    return path_to_file_from_user


def create_brief_matrix_file(checking_file):
    """ Создать или вернуть файл с данными для проверки в ГОЛД,
    в котором будут номер в матрице, код и наименование продукта. """
    if not os.path.isfile(Files.BEFORE_GOLD.value):
        create_gold_codes_file(checking_file)


def launch_monitoring():
    """ Запуск программы мониторинга. """
    logger.info(" Старт программы мониторинга. ")
    print(MsgForUser.LAUNCH_OF_PROGRAM.value)

    input_file = get_file_name_from_user(MsgForUser.INPUT_FILE.value)
    change_layout_on_english()
    create_brief_matrix_file(input_file)
    launch_gold_module(500, Files.BEFORE_GOLD.value, Files.GOLD.value)
    launch_checking_in_web(gold_file=Files.GOLD.value,
                           result_file=Files.RESULT_FILE.value,
                           count_of_iterations=500,
                           file_for_last_number=Files.LAST_VIEWED_IN_WEB_NUMB.value)

    logger.info(MsgForUser.MAIN_MONITORING_COMPLETE.value)
    print(MsgForUser.MAIN_MONITORING_COMPLETE.value)
    df = pd.read_excel(Files.RESULT_FILE.value)
    split_result_file(df, ResultFileNames.FULL.value,
                      ResultFileNames.WRONG_STATUSES.value)
    sys.exit()


if __name__ == '__main__':
    change_layout_on_english()
    launch_monitoring()
