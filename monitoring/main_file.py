""" Запуск всего кода, который содержится в пакете. """
import os
import shutil
import sys

import pandas as pd
from monitoring.exceptions import PathNotPassException, FileNotExistingException
from gold_data_manager import launch_gold_module
from monitoring.constants import Files, PATH_TO_DESKTOP, MESSAGE_FOR_USER_TO_INPUT_FILE
from monitoring.functions_for_work_with_files_and_dirs import change_layout_on_english
from monitoring_in_web import launch_checking_in_web, RequiredTabsWorker
from logger_config import log_to_file_info


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
    path_from_user = input(message_for_user)
    path_from_user = PATH_TO_DESKTOP + path_from_user + '.xlsx'
    if not path_from_user:
        raise PathNotPassException
    if not os.path.isfile(path_from_user):
        raise FileNotExistingException
    return path_from_user


def check_or_create_file_before_checking_in_gold(checking_file):
    if not os.path.isfile(Files.BEFORE_GOLD.value):
        create_sheet_write_codes_and_names(checking_file)
        log_to_file_info("Создан файл %s" % Files.BEFORE_GOLD.value)
    else:
        log_to_file_info("Файл %s уже существует." % Files.BEFORE_GOLD.value)


def automatic_launch_program():
    checking_file = get_name_for_matrix_file_on_desktop(MESSAGE_FOR_USER_TO_INPUT_FILE)
    change_layout_on_english()
    check_or_create_file_before_checking_in_gold(checking_file)
    launch_gold_module(500, Files.BEFORE_GOLD.value, Files.GOLD.value)
    launch_checking_in_web(gold_file=Files.GOLD.value,
                           result_file=Files.RESULT_FILE.value,
                           count_of_iterations=500,
                           file_for_last_number=Files.LAST_VIEWED_IN_WEB_NUMBER.value,
                           browser_worker=RequiredTabsWorker)
    log_to_file_info("Проверка полностью завершена.")
    # Готовый результат копируем на рабочий стол.
    destination_file = os.path.join(PATH_TO_DESKTOP, os.path.basename('Результат проверки мониторинга.xlsx'))
    shutil.copyfile(Files.RESULT_FILE.value, destination_file)
    log_to_file_info(f'Файл скопирован на рабочий стол: {destination_file}')
    print(f'Проверка полностью завершена. \nФайл скопирован на рабочий стол: {destination_file}')
    sys.exit()


if __name__ == '__main__':
    change_layout_on_english()
    automatic_launch_program()
