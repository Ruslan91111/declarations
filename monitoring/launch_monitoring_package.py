""" Запуск всего кода, который содержится в пакете. """
import os
import shutil
import sys

import pandas as pd

from monitoring_process.monitoring_in_web import launch_checking_in_web

base_path = os.path.join("C:\\Users\\impersonal\\Desktop\\declarations\\monitoring")
if base_path not in sys.path:
    sys.path.insert(0, base_path)
from gold.data_manager import launch_gold_module
from common.logger_config import logger

# from monitoring.monitoring_in_web import launch_checking_in_web

from common.exceptions import FileNotPassedException, FileNotExistingException
from common.constants import Files, PATH_TO_DESKTOP, MESSAGE_TO_INPUT_FILE
from common.work_with_files_and_dirs import change_layout_on_english


def create_sheet_write_codes_and_names(file_for_checking: str,
                                       file_of_results: str = Files.BEFORE_GOLD.value):
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


def get_name_for_matrix_file_on_desktop(message_for_user: str) -> str:
    """ Наименование файла xlsx, находящегося на рабочем столе."""
    file_from_user = input(message_for_user)
    path_to_file_from_user = PATH_TO_DESKTOP + file_from_user + '.xlsx'
    logger.info(f'Передан файл - <{file_from_user}>')

    # Проверки передано ли название файла для проверки и существует ли файл.
    if not file_from_user:
        raise FileNotPassedException
    if not os.path.isfile(path_to_file_from_user):
        raise FileNotExistingException
    return path_to_file_from_user


def check_or_create_file_before_checking_in_gold(checking_file):
    """ Создать или вернуть файл с данными для проверки в ГОЛД,
    в котором будут номер в матрице, код и наименование продукта. """
    if not os.path.isfile(Files.BEFORE_GOLD.value):
        create_sheet_write_codes_and_names(checking_file)


def launch_monitoring():
    """ Запуск программы мониторинга. """
    logger.info(" Старт программы мониторинга. ")
    checking_file = get_name_for_matrix_file_on_desktop(MESSAGE_TO_INPUT_FILE)
    change_layout_on_english()
    check_or_create_file_before_checking_in_gold(checking_file)
    launch_gold_module(500, Files.BEFORE_GOLD.value, Files.GOLD.value)
    launch_checking_in_web(gold_file=Files.GOLD.value,
                           result_file=Files.RESULT_FILE.value,
                           count_of_iterations=500,
                           file_for_last_number=Files.LAST_VIEWED_IN_WEB_NUMB.value)

    logger.info("Проверка полностью завершена.")

    # Готовый результат копируем на рабочий стол.
    destination_file = os.path.join(PATH_TO_DESKTOP, os.path.basename(
        'Результат проверки мониторинга.xlsx'))

    shutil.copyfile(Files.RESULT_FILE.value, destination_file)
    logger.info(f'Файл скопирован на рабочий стол: {destination_file}')
    sys.exit()


if __name__ == '__main__':
    change_layout_on_english()
    launch_monitoring()
