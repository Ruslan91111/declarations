"""Вспомогательные функции для работы с файлами."""
import os

import pandas as pd

from selenium_through.config import INDEXES_FOR_DF_COMPARISON


def read_columns_from_xlsx(xlsx_template: str) -> list:
    """Вернуть список наименований всех столбцов из шаблонного xlsx файла."""
    df = pd.read_excel(xlsx_template)
    columns_from_df = df.columns
    return columns_from_df


def give_columns_for_scrapping_declaration(columns: list) -> set:
    """Предоставить названия столбцов для скрапинга декалараций."""
    columns = list(columns)
    columns.extend(['Адрес места нахождения', 'Полное наименование юридического лица',
                    'Полное наименование', 'Номер записи в РАЛ испытательной лаборатории',
                    'Номер документа'])
    columns = set(columns)
    return columns


def give_columns_for_scrapping_certificate(columns: list) -> set:
    """Предоставить названия столбцов для скраппинга сертификатов."""
    columns = list(columns)
    columns.extend(['Полное наименование', 'Фамилия руководителя', 'Имя руководителя',
                    'Отчество руководителя', 'Адрес места нахождения',
                    'Адрес места осуществления деятельности', 'Адрес производства продукции',
                    'Общее наименование продукции', 'Наименование испытательной лаборатории',
                    'Бланк сертификата'
                    'Номер записи в РАЛ испытательной лаборатории',
                    'Номер документа'])
    columns = set(columns)
    return columns


def write_viewed_numbers_to_file(text_file: str, viewed: list) -> None:
    """Записать номера просмотренных документов в файл."""
    with open(text_file, 'a') as file:
        for number in viewed:
            file.write(str(number) + '\n')


def read_viewed_numbers_of_documents(text_file: str) -> dict:
    """Прочитать номера просмотренных документов из файла."""
    if not os.path.isfile(text_file):
        with open(text_file, 'w') as file:
            file.write('')

    with open(text_file, 'r') as file:
        list_of_viewed = file.read().split("\n")
        my_dict = {number: 0 for number in list_of_viewed}
        return my_dict


def write_to_excel_result_of_comparison(lists: list, path_to_excel: str):
    """Принять на вход несколько списков и записать их
    в excel файл в строки друг над другом с индексами слева."""
    data = {index: values for index, values in zip(INDEXES_FOR_DF_COMPARISON, lists)}
    df = pd.DataFrame(data)
    df = df.transpose()  # Транспонирование DataFrame: строки становятся столбцами и наоборот.
    with pd.ExcelWriter(path_to_excel) as writer:
        df.to_excel(writer, index=True, header=False)
        # df.to_excel(writer, index=False)  Записать в 4 столбца


def write_to_excel_data_one_document(lists: list, path_to_excel: str):
    """Принять на вход несколько списков и записать их
    в excel файл в строки друг над другом с индексами слева."""
    df = pd.DataFrame(lists)
    with pd.ExcelWriter(path_to_excel) as writer:
        df.to_excel(writer, index=False, header=False)
