"""
Модуль для проверки статусов международных документов.

Этот модуль содержит класс InternationalScrapper, который обрабатывает входной XLSX файл,
перебирает строки, определяет номера международных документов и проверяет их статусы на сайте.

Класс:
    - InternDocCollector:
        Класс для сбора данных по международным документам.

Функции:
    - make_intern_doc_collector:
        Создать объект класса с параметрами по умолчанию.

    def launch_checking_int_docs(range_numb: int) -> None:
        Запуск кода модуля для проверки международных документов.

Пример использования:
    launch_checking_int_docs(range_numb: int)

"""
import os
import shutil
import sys

import pandas as pd

# Определяем путь к корневой директории проекта (каталог 'monitoring')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from common.constants import Files
from common.work_with_files_and_dirs import read_numb_from_file, write_numb_to_file
from common.logger_config import logger
from web.intern_docs.helpers import find_required_doc, create_intern_xlsx
from web.intern_docs.parser import InternDocParser


class InternDocCollector:
    """ Класс для проверки данных по международным документам. """

    def __init__(self, intern_xlsx: str, file_for_last_number: str):
        self.intern_xlsx = intern_xlsx
        self.df = pd.read_excel(self.intern_xlsx)
        self.last_checked_in_web_number = read_numb_from_file(file_for_last_number)
        self.number = ''
        self.status = ''
        self.create_viewed_numbs()
        self.last_row = self.df.iloc[-1].name
        self.current_row_numb = 0
        self.parser = InternDocParser()

    def create_viewed_numbs(self):
        """ Создать словарь просмотренных номеров документов. """
        self.viewed_numbs = {}
        for iteration, row in self.df.iloc[self.last_checked_in_web_number:].iterrows():
            international_doc = find_required_doc(row['ДОС'])
            if international_doc:
                if not pd.isna(row['Статус на сайте']):
                    self.viewed_numbs[row['ДОС']] = row['Статус на сайте']

    def process_get_statuses(self):
        """ Организация работы по сбору статуса декларации с веб-сайта. """
        try:
            self.get_statuses_of_docs()
        except Exception as error:
            logger.error(error)
            self.parser.check_not_available_serv()
        finally:
            self.write_df_and_last_numb()

    def get_statuses_of_docs(self):
        """ Перебрать строки в xlsx файле с результатами мониторинга,
        найти номера, подпадающие под паттерн международных документов и проверить их
        на сайте. """
        for iteration, row in self.df.iloc[self.last_checked_in_web_number:].iterrows():
            self.current_row_numb = row.name
            international_doc = find_required_doc(row['ДОС'])

            if international_doc:
                self.number = row['ДОС']

                if self.number in self.viewed_numbs:
                    self.status = self.viewed_numbs[self.number]

                else:
                    self.parser.number = self.number
                    self.parser.get_status_from_web()
                    self.status = self.parser.status
                    self.viewed_numbs[self.number] = self.status

                print(self.number)
                self.df.at[iteration, 'Статус на сайте'] = self.status
                self.last_checked_in_web_number = row.name

    def write_df_and_last_numb(self):
        """ Записать dataframe и последний просмотренный номер row в файлы. """
        self.df.to_excel(self.intern_xlsx, index=False)
        write_numb_to_file(Files.LAST_VIEWED_FOR_INTERN.value,
                           self.last_checked_in_web_number)


def make_intern_doc_collector(
        result_file: str = Files.INTERN_DOCS.value,
        file_for_last_number: str = Files.LAST_VIEWED_FOR_INTERN.value):
    """ Создать объект класса с параметрами по умолчанию. """
    return InternDocCollector(result_file, file_for_last_number)


def launch_collect_intern_docs(range_numb: int) -> None:
    """ Запуск кода модуля для проверки международных документов. """

    if not os.path.isfile(Files.INTERN_DOCS.value):
        create_intern_xlsx(Files.RESULT_FILE.value, Files.INTERN_DOCS.value)

    for _ in range(range_numb):
        collector = make_intern_doc_collector()
        collector.process_get_statuses()

        if collector.current_row_numb == collector.last_row:
            print('Все международные документы проверены.')
            shutil.copyfile(Files.INTERN_DOCS.value, Files.INTERN_DOCS_RESULT.value)
            logger.info(f'Файл скопирован на рабочий стол: {Files.INTERN_DOCS_RESULT.value}')
            break


if __name__ == '__main__':
    launch_collect_intern_docs(60)
