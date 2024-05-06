""" Модуль с функциями для работы с файлами, директориями, процессами. """
import json
import os

import openpyxl
import psutil

from monitoring.logger_config import log_to_file_info


def return_or_create_dir(path_to_dir: str):
    """ Вернуть или создать директорию. """
    if not os.path.isdir(path_to_dir):
        os.mkdir(path_to_dir)
        log_to_file_info("Создана директория по пути %s" % path_to_dir)
    else:
        log_to_file_info("Директория %s уже существует." % path_to_dir)
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
    workbook.save(xlsx_file)
    log_to_file_info("Создан файл %s" % xlsx_file)
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
