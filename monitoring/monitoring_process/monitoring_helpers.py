"""
Модуль с функциями и классами, которые оказывают вспомогательное содействие
в процессе мониторинга, но прямо не участвуют в нем.

Функции:
    - collect_ogrns_and_addresses:
        Сбор и возврат из файла уже проверенных документов.
        Возвращает словарь, где ключами являются <ОГРН>, а значениями – <адреса юридических лиц>.

    - choose_parser:
        Определение типа документа.
        Возвращает подходящий парсер в зависимости от типа документа.

    - prepare_result_df:
        Подготовка DataFrame для итогов мониторинга.

    - check_request_time:
        Проверка времени, прошедшего с последнего обращения к сайту ФСА.
        Если времени недостаточно, выполняется задержка.

Класс:
    - HelpData:
        Dataclass, предназначенный для хранения данных, необходимых для
        нормального функционирования мониторинга.
"""
import re
import time
from dataclasses import dataclass

import pandas as pd

from common.constants import COLS_FOR_RESULT_DF
from common.work_with_files_and_dirs import (read_numb_from_file,
                                             return_or_create_xlsx,
                                             return_or_create_new_df)

from web.parsers.sgr_parser import SgrParser
from web.parsers.fsa_parser import FSADeclParser, FSACertParser
from web.work_with_browser import MonitoringBrowser


def collect_ogrns_and_addresses(df: pd.DataFrame) -> dict:
    """Собрать и вернуть из файла уже проверенных документов
    словарь из ключей: <ОГРН> и значений: <адресов юридических лиц.>"""
    try:
        if len(df) != 0:
            df = df.dropna(subset=['ОГРН заявителя', 'Адрес заявителя',
                                   'ОГРН изготовителя', 'Адрес изготовителя'])
    except FileNotFoundError:
        return {}

    ogrn_and_addresses = {}

    for _, row in df.iterrows():
        ogrn_and_addresses[row['ОГРН заявителя']] = row['Адрес заявителя']
        ogrn_and_addresses[row['ОГРН изготовителя']] = row['Адрес изготовителя']
    if 'Нет ОГРН' in ogrn_and_addresses:
        del ogrn_and_addresses['Нет ОГРН']

    return ogrn_and_addresses


def choose_parser(number) -> type | None:
    """ Определить тип документа. Вернуть подходящий под тип документа парсер."""
    patterns = {
        r'(ЕАЭС N RU Д-[\w\.]+)': FSADeclParser,
        r'(РОСС RU Д-[\w\.]+)': FSADeclParser,
        r'(ТС N RU Д-[\w\.]+)': FSADeclParser,
        r'(ЕАЭС RU С-[\w\.]+)': FSACertParser,
        r'(РОСС RU С-[\w\.]+)': FSACertParser,
        r'\w{2}\.\d{2}\.(\d{2}|\w{2})\.\d{2}\.\d{2,3}\.\w\.\d{6}\.\d{2}\.\d{2}': SgrParser}
    for pattern, scrapper_class in patterns.items():
        if re.match(pattern, number):
            return scrapper_class
    return None


def prepare_result_df(result_file: str):
    """ Подготовить DataFrame для итогов мониторинга """
    df = pd.read_excel(return_or_create_xlsx(result_file))
    df = return_or_create_new_df(df, columns=[COLS_FOR_RESULT_DF])
    return df


def check_request_time(scrapper_by_type_of_doc, elapsed_time_from_last_request):
    """ Проверить сколько времени прошло с момента последнего обращения к сайту ФСА,
    если недостаточно, то выполнить задержку. """
    if (scrapper_by_type_of_doc in {FSADeclParser, FSACertParser} and
            0 < elapsed_time_from_last_request < 60):
        time.sleep(60 - elapsed_time_from_last_request)


@dataclass
class HelpData:
    """ Класс для хранения данных, необходимых для нормального осуществления мониторинга. """
    ogrn_and_addresses: dict
    checked_docs_numb: set
    last_checked_in_web_number: int
    last_row_in_gold: int
    current_iteration: int
    request_time: float
    error: str
    error_time: float
    browser_worker: any

    def __init__(self, result_df, gold_df, file_last_number_web,
                 number_of_iteration, error, time_error):
        self.ogrn_and_addresses = collect_ogrns_and_addresses(result_df)
        self.watched_docs_numbers = set(result_df['ДОС'])
        self.last_checked_in_web_number = read_numb_from_file(file_last_number_web)
        self.last_row_in_gold = gold_df.iloc[-1].name
        self.current_iteration = number_of_iteration
        self.request_time = 0
        self.error = error
        self.error_time = time_error
        self.browser_worker = MonitoringBrowser
