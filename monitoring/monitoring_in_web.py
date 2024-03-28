"""
Модуль работы кода с интернет-ресурсами, а именно, сайтами проверки данных: ФСА, СГР, ГОСТ.

Содержит функции:
    add_egrul_information
    get_address_from_egrul
    _compare_addresses
    add_gost_information
    check_gost
    _get_dict_from_text_nsi
    get_data_from_nsi
    make_new_tab
    make_all_required_tabs
    make_dict_ogrn_address
    check_number_declaration
    make_series_for_result
    check_or_create_result_xlsx
    write_viewed_numbers_to_file
    checking_data_in_iteration_through_browser - основная функция
    launch_checking - запуск кода
класс:
    FSAScrapper - для работы с сайтом ФСА с сбора данных с него по каждой декларации.
"""
import logging
import os
import random
import sys
import time
from datetime import datetime
import re
from types import NoneType

import pandas as pd
from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (NoSuchElementException,
                                        TimeoutException,
                                        ElementClickInterceptedException,
                                        StaleElementReferenceException, NoSuchWindowException)

from config import PROXY
from exceptions import (EgrulCaptchaException, MaxIterationException, StopBrowserException)
from gold_data_manager import write_last_viewed_number_to_file, read_last_viewed_number_from_file
##################################################################################
# Константы
##################################################################################
# URLs
URL_FSA_DECLARATION = "https://pub.fsa.gov.ru/rds/declaration"
URL_FSA_CERTIFICATE = "https://pub.fsa.gov.ru/rss/certificate"
URL_EGRUL = "https://egrul.nalog.ru/"
URL_GOST = "https://etr-torgi.ru/calc/check_gost/"
date_today = datetime.now().strftime('%Y-%m-%d')
URL_NSI = f'https://nsi.eaeunion.org/portal/1995?date={date_today}'

PATH_TO_DRIVER = r'..\.\chromedriver.exe'

# Файлы
VIEWED_IN_FSA_NUMBERS = r'.\viewed_in_web_numbers.txt'
LOGGING_FILE = r'.\monitoring.log'

# Подстроки, которые необходимо удалить из адресов перед их сравнением.
PARTS_TO_BE_REMOVED = [
    'БУЛЬВАР', 'Б-Р',
    ' ВН ',
    'ГОРОД ', ' Г ',
    ' Д ', 'ДОМ ',
    ' КАБ ', 'КАБИНЕТ',
    ' КОМ ', 'КОМНАТА ',
    'М Р-Н', 'МИКРОРАЙОН', ' МКР ',
    ' НАБ ', 'НАБЕРЕЖНАЯ ',
    ' ОБЛ ', 'ОБЛАСТЬ',
    ' ОФ ', 'ОФИС ',
    ' П ', ' ПОМ ', 'ПОМЕЩ ', 'ПОМЕЩЕНИЕ',
    'ПОСЕЛОК ГОРОДСКОГО ТИПА', 'ПОС ', 'ПГТ ',
    ' ПР-Д ', 'ПРОЕЗД ',
    'РАЙОН', ' Р-Н ',
    'РОССИЯ',
    ' СТР ', 'СТРОЕНИЕ ',
    ' ТЕР ',
    ' УЛ ', 'УЛИЦА ',
    'ШОССЕ ', ' Ш ',
    ' ЭТ ', 'ЭТАЖ ',
]


# X-paths, используемые в коде.
X_PATHS = {

    # Сайт для ФСА(декларации и свидетельства)
    'fsa_chapter': '//fgis-links-list/div/ul/li',
    'fsa_input_field': "//fgis-text/input",
    'fsa_search_button': "//button[contains(text(), 'Найти')]",
    'fsa_pick_document': "//*/fgis-h-table-limited-text-cell/div[1]",
    'fsa_return_declaration': "//fgis-rds-view-declaration-toolbar/div/div[1]",
    'fsa_return_certificate': "//fgis-rss-view-certificate-toolbar/div/div[1]",
    'fsa_doc_status': '//fgis-toolbar-status/span',
    'fsa_last_iter': '//fgis-links-list/div/ul/li',

    # Сайт для СГР
    'nsi_filter': '/html/body/div[1]/div/div/div[2]/div/div[1]/div[3]/'
                  'div/div/div[1]/table/thead/tr/th[2]/div/div/button/span',
    'nsi_input_field': '/html/body/div[3]/div[1]/div/input',
    'nsi_check_mark': '/html/body/div[3]/div[2]/button[2]/span[1]',
    'nsi_status': '//tbody/tr/td[3]/div/div/a/div/span',
    'nsi_no_data': '//tbody/tr/td',
    'nsi_applicant': '//tbody/tr/td[8]/div/div/span',
    'nsi_manufacturer': '//tbody/tr/td[7]/div/div/span',
    'nsi_document_name': '//tbody/tr/td[9]/div/div/span',
    'nsi_icon_file': '//*/table/tbody/tr/td[1]/button/span[1]',

    # ЕГРЮЛ
    'egrul_input': '//*[@id="query"]',
    'search_button_egrul': '//*[@id="btnSearch"]',
    'egrul_captcha': '//*[@id="frmCaptcha"]',

    # ГОСТ
    'gost_input_field': '//*[@id="poisk-form"]/input',
    'gost_search_button': '//*[@id="gost_filter"]',
    'gost_status': '//*[@id="data-box"]/div/div/div/p/b',
}

# Словарь с прочерками.
BLANK_DICT_FOR_FILLING = {
    'Наличие ДОС': 'Не найдено на сайте',
    # 'Статус на сайте': '-',
    'Соответствие с сайтом': '-',
    'Соответствие адресов с ЕГРЮЛ': '-',
    'Адрес места нахождения applicant': '-',
    'Статус НД': '-'
}

# Названия колонок для Series, формируемого в результате парсинга веб-сайтов.
TITLE_FOR_SERIES_TO_FINAL_DF = [
    'Сокращенное наименование юридического лица applicant',
    'Дата проверки',
    'Наличие ДОС',
    'Соответствие с сайтом',
    'Статус на сайте',
    'ОГРН applicant',
    'ОГРН manufacturer',
    'Соответствие адресов с ЕГРЮЛ',
    'Адрес места нахождения applicant',
    'Адрес места нахождения applicant ЕГРЮЛ',
    'Адрес места нахождения manufacturer',
    'Адрес места нахождения manufacturer ЕГРЮЛ',
    'Статус НД',
    'ФИО',
]

# Нужные ключи для сбора с ФСА
REQUIRED_KEYS_TO_FSA = {
    'Статус декларации', 'Полное наименование юридического лица',
    'Сокращенное наименование юридического лица',
    'Основной государственный регистрационный номер юридического лица (ОГРН)',
    'Адрес места нахождения', 'Наименование документа',
    'Обозначение стандарта, нормативного документа'}

# Названия колонок для финального DataFrames, формируемого и записываемого в result_data.
COLUMNS_FOR_FINAL_DF = [
    'Порядковый номер АМ',
    'Код товара',
    'Наименование товара',
    'ДОС',
    'Изготовитель',
    'Поставщик',
    'Дата проверки',
    'Наличие ДОС',
    'Соответствие с сайтом',
    'Статус на сайте',
    'ОГРН заявителя',
    'ОГРН изготовителя',
    'Соответствие адресов с ЕГРЮЛ',
    'Адрес заявителя',
    'Адрес заявителя ЕГРЮЛ',
    'Адрес изготовителя',
    'Адрес изготовителя ЕГРЮЛ',
    'Статус НД',
    'ФИО',
]


##################################################################################
# Логгирование.
##################################################################################
logging.basicConfig(
    level=logging.INFO,
    filename=LOGGING_FILE,
    filemode="a",
    encoding='utf-8',
    format="%(asctime)s %(levelname)s %(message)s",
)


##################################################################################
#  ЕГРЮЛ
# Работа с адресами - проверяем адреса юридических лиц, взятые с сайта ФСА.
# Дополнительно берем адреса по ОГРН с сайта ЕГРЮЛ и сравниваем между собой.
##################################################################################
def add_to_data_egrul_information(data: dict, tabs: dict, dict_ogrn_address: dict,
                                  browser_, wait_) -> (dict, dict):
    """Добавить в словарь данных о проверяемом документе адресов из ЕГРЮЛ.

    Предварительно проверить не проверяли ли ОГРН юрлиц ранее, если да,
    то взять адрес из словаря ранее проверенных, если не проверяли,
    то открыть сайт ЕГРЮЛ и взять из него адрес. В конце функции сравнить адреса
    и записать вывод о соответствии адресов на проверяемом сайте и сайте ЕГРЮЛ.

    : param data: словарь с данными о документе, полученными с сайта, в том числе юр.лицах,
    : param tabs: словарь с вкладками для переключения в браузере,
    : param dict_ogrn_address: словарь, где ключи - ОГРН, а значения адреса юр.лиц,
    """

    for org in ('applicant', 'manufacturer'):
        try:  # Проверяем не проверялся ли ОГРН ранее.
            data[f'Адрес места нахождения {org} ЕГРЮЛ'] = dict_ogrn_address[data[f'ОГРН {org}']]
            continue  # Если проверялся, то пропускаем итерацию.
        except KeyError:
            pass

        # Если ранее ОГРН не проверялся. Пытаемся найти и сохранить адрес с сайта ЕГРЮЛ.
        browser_.switch_to.window(tabs['egrul'])
        data = get_address_from_egrul(data, org, browser_, wait_)

        # Записываем в словарь результат сравнения.
        try:
            dict_ogrn_address[data[f'ОГРН {org}']] = data[f'Адрес места нахождения {org} ЕГРЮЛ']
        except KeyError:
            pass

    # Записываем в словарь вывод о соответствии адресов.
    if 'Нет ОГРН' in data.values():  # Если у поставщика или изготовителя не было ОГРН.
        data['Соответствие адресов с ЕГРЮЛ'] = 'НЕТ ОГРН'
    else:
        # ОГРН был - вызвать функцию сравнения адресов.
        data = _compare_addresses(data)  

    return data, dict_ogrn_address


def get_address_from_egrul(data_web: dict, org: str, browser_, wait_) -> dict:
    """
    Взять адрес с сайта ЕГРЮЛ по ОГРН. Если ОГРН нет, то так и записать.

    : param data_web: словарь с данными о документе, полученными с сайта, в том числе юр.лицах,
    : param org: строковое обозначение типа организации заявитель или изготовитель,
    """

    # Проверяем есть ли ОГРН у юр.лица.
    if f'ОГРН {org}' in data_web.keys() and data_web[f'ОГРН {org}'] != '-':  # Если есть ОГРН
        try:
            needed_element = wait_.until(EC.element_to_be_clickable(
                (By.XPATH, X_PATHS['egrul_input'])))
            needed_element.send_keys(data_web[f'ОГРН {org}'])  # Ввести ОГРН

            button_search = wait_.until(EC.element_to_be_clickable(
                (By.XPATH, X_PATHS['search_button_egrul'])))
            button_search.click()  # Нажать найти

            # Сохраняем в словарь адрес с сайта ЕГРЮЛ.
            try:
                text = wait_.until(EC.element_to_be_clickable((By.CLASS_NAME, 'res-text'))).text
                data_web[f'Адрес места нахождения {org} ЕГРЮЛ'] = text[:text.find('ОГРН')].strip(' ,')
            except:
                data_web[f'Адрес места нахождения {org} ЕГРЮЛ'] = 'Ошибка noDataFound'

            browser_.refresh()  # Обновить вкладку, для следующего ввода.

        except TimeoutException:
            raise EgrulCaptchaException

    else:  # Если ОГРН у юр.лица нет.
        data_web[f'Адрес места нахождения {org} ЕГРЮЛ'] = 'Нет ОГРН'

    return data_web


def _compare_addresses(data: dict) -> dict:
    """
    Сравнить строки - адреса: 1) с сайта и 2) ЕГРЮЛ.

    Предварительно из строк(адресов) убрать обозначения, наподобие: ул. гор. и т.д.
    И затем сравнить что останется в строках
    """
    elements_to_be_removed = PARTS_TO_BE_REMOVED  # Элементы, которые нужно убрать из строк.

    def prepare_addresses(string: str) -> list:
        """Подготовить адреса перед сравнением - убрать сокращения,
        лишние знаки, разбить в словарь по символам."""
        string = (string.upper().
                  replace('.', ' ').
                  replace('(', '').
                  replace(')', '').
                  replace(',', ' '))

        # Убираем сокращения и обозначения.
        for elem in elements_to_be_removed:
            string = string.replace(elem, ' ')
        string = string.replace(' ', '')
        result = sorted(string)
        return result

    # Привести адреса к единому виду - отсортированным спискам строк.
    applicant = prepare_addresses(data['Адрес места нахождения applicant'])
    applicant_egr = prepare_addresses(data['Адрес места нахождения applicant ЕГРЮЛ'])
    manufacturer = prepare_addresses(data['Адрес места нахождения manufacturer'])
    manufacturer_egr = prepare_addresses(data['Адрес места нахождения manufacturer ЕГРЮЛ'])

    # Сделать и внести в словарь вывод о соответствии адресов.
    if applicant == applicant_egr and manufacturer == manufacturer_egr:
        data['Соответствие адресов с ЕГРЮЛ'] = 'Соответствуют'
    else:
        data['Соответствие адресов с ЕГРЮЛ'] = 'Не соответствуют'

    return data


##################################################################################
# Работа с ГОСТ.
##################################################################################
def add_to_data_gost_information(data: dict, tabs: dict, browser_, wait_) -> dict:
    """
    Добавить к словарю данные о статусе ГОСТ.

    : param data: словарь с данными о документе, полученными с сайта,
    : param tabs: словарь с вкладками для переключения в браузере
    """
    browser_.switch_to.window(tabs['gost'])
    data = check_gost_on_web(data, wait_)  # ГОСТ.
    return data


def check_gost_on_web(data: dict, wait_) -> dict:
    """Проверить ГОСТ, взятый с сайта(ФСА или nsi) на сайте проверки ГОСТ.
     Добавить в словарь вывод о статусе ГОСТ."""

    # Сокращения для ключей
    product = 'Наименование документа product'
    standard = "Обозначение стандарта, нормативного документа product"

    # Проверяем взяты ли данные с сайта с тех полей, где могут содержаться номера ГОСТ.
    if product in data or standard in data:

        # Берем непосредственно текст, в котором может быть номер ГОСТ.
        if product in data and standard in data:
            text = data[product] + ' ' + data[standard]
        elif product in data:
            text = data[product]
        elif standard in data:
            text = data[standard]

        # Ищем подстроки, совпадающие с паттерном ГОСТ.
        pattern_gost = r"ГОСТ\s\b\d{4,5}-\d{2,4}\b"
        result = set(re.findall(pattern_gost, text))
        status_gost = set()  # Переменная для сбора статусов ГОСТ.

        if result:  # Если в тексте ГОСТ есть, ввести и проверить на сайте.

            for gost_number in result:  # Перебираем ГОСТы.
                needed_element = wait_.until(EC.element_to_be_clickable(
                    (By.XPATH, X_PATHS['gost_input_field'])))
                needed_element.clear()
                needed_element.send_keys('ГОСТ ' + gost_number)  # Ввести номер ГОСТ
                button_search = wait_.until(EC.element_to_be_clickable(
                    (By.XPATH, X_PATHS['gost_search_button'])))
                button_search.click()  # Нажать найти
                # Сохранить статус ГОСТа на сайте.
                try:
                    element = wait_.until(EC.element_to_be_clickable(
                        (By.XPATH, X_PATHS['gost_status'])))
                    text = element.text
                    status_gost.add(text)
                    data['Статус НД'] = " ".join(status_gost)  # Сохранить значения с сайта ГОСТ
                except:
                    data['Статус НД'] = 'Информация о стандарте не найдена.'

        else:  # Если данных о ГОСТе нет.
            data['Статус НД'] = '-'

    return data


##################################################################################
# Работа с сайтом nsi - проверка свидетельства о гос.регистрации
##################################################################################
def _get_dict_from_text_nsi(text: str, type_of_org: str) -> dict:
    """
    Функция формирует из текста с сайта nsi словарь данных по юридическому лицу.


    """
    data = {}  # Словарь для возврата данных.

    # Ищем и добавляем в словарь наименование и адрес юр.лица.
    pattern_index = r'\d{6}'  # Паттерн для поиска почтового индекса.
    match_index = re.search(pattern_index, text)  # Ищем почтовый индекс.

    if match_index:  # Если почтовый индекс есть в тексте
        # То, что в тексте до почтового индекса сохраняем в качестве наименования юр.лица.
        data[f'Сокращенное наименование юридического лица {type_of_org}'] = (
            text[:match_index.start()].strip(" ,"))
        data[f'Адрес места нахождения {type_of_org}'] = (
            text[match_index.start():text.find('[')])

    elif '[' in text:  # Если нет почтового индекса.
        data[f'Сокращенное наименование юридического лица {type_of_org}'] = (
            text[:text.find('[') + 1])

    else:  # Значит из информации только наименование.
        data[f'Сокращенное наименование юридического лица {type_of_org}'] = text
        data[f'Адрес места нахождения {type_of_org}'] = '-'

    # Ищем ОГРН
    pattern_ogrn = r'\d{13}'  # Паттерн для поиска ОГРН.
    ogrn = re.search(pattern_ogrn, text)

    if isinstance(ogrn, NoneType):
        data[f'ОГРН {type_of_org}'] = '-'
    else:
        data[f'ОГРН {type_of_org}'] = ogrn.group()

    return data


def get_data_from_nsi_web(document_number, browser_, wait_) -> None | dict:
    """Собрать данные по свидетельству о государственной регистрации с сайта nsi.
    Вернет либо словарь, достаточный для добавления и последующей записи, либо None"""

    # Найти и нажать на кнопку фильтра - после которой можно ввести номер СГР
    filter_button = wait_.until(EC.element_to_be_clickable((By.XPATH, X_PATHS['nsi_filter'])))
    filter_button.click()

    # Дождаться возможности ввода номера СГР.
    input_number_field = wait_.until(EC.element_to_be_clickable(
        (By.XPATH, X_PATHS['nsi_input_field'])))
    input_number_field.clear()
    input_number_field.send_keys(document_number)  # Ввести номер СГР

    # Нажать на галочку - запустить поиск.
    check_mark = wait_.until(EC.element_to_be_clickable((By.XPATH, X_PATHS['nsi_check_mark'])))
    check_mark.click()

    # Дождаться загрузки страницы - исчезновения элемента: затемнения на дисплее.
    loaded = False
    while not loaded:
        try:
            time.sleep(0.06)
            browser_.find_element(By.CLASS_NAME, 'p-datatable-loading-overlay')
        except NoSuchElementException:
            loaded = True

    # Проверяем есть ли данные. Если данных нет, то будет соответсвующее сообщение на странице.
    try:
        data_on_nsi = browser_.find_element(By.XPATH, X_PATHS['nsi_no_data']).text
        if data_on_nsi == 'Нет данных':
            data = BLANK_DICT_FOR_FILLING
            data['Статус на сайте'] = 'Нет на сайте'
            return data

    except NoSuchElementException:  # Если сообщение об отсутствии данных не найдено, то продолжить.
        pass

    # Создаем словарь с данными по СГР. Сохраняем первую пару ключ - значение.
    data = {'Статус на сайте': wait_.until(EC.element_to_be_clickable(
        (By.XPATH, X_PATHS['nsi_status']))).text}

    # Добавляем в data данные по заявителю, производителю, документации и по остальным ключам.
    text_applicant = wait_.until(EC.presence_of_element_located(
        (By.XPATH, X_PATHS['nsi_applicant']))).text
    data.update(_get_dict_from_text_nsi(text_applicant, 'applicant'))

    text_manufacturer = wait_.until(EC.presence_of_element_located(
        (By.XPATH, X_PATHS['nsi_manufacturer']))).text
    data.update(_get_dict_from_text_nsi(text_manufacturer, 'manufacturer'))

    data['Наименование документа product'] = wait_.until(
        EC.presence_of_element_located((By.XPATH, X_PATHS['nsi_document_name']))).text

    if data:
        data['Наличие ДОС'] = 'Да'
        data['Соответствие с сайтом'] = 'Соответствует'

    return data


##################################################################################
# Небольшие вспомогательные функции.
##################################################################################
def make_new_tab(browser_, url: str):
    """Открыть новое окно в браузере с определенным
    сайтом и вернуть указатель на него."""
    browser_.switch_to.new_window('tab')
    browser_.get(url)
    time.sleep(random.randint(1, 3))
    return browser_.current_window_handle


def make_all_required_tabs(browser_) -> dict:
    """Создать все 5 необходимых вкладок в браузере."""
    tabs = {
        'declaration': make_new_tab(browser_, URL_FSA_DECLARATION),
        'certificate': make_new_tab(browser_, URL_FSA_CERTIFICATE),  # Сертификаты.
        'egrul': make_new_tab(browser_, URL_EGRUL),  # ЕГРЮЛ
        'gost': make_new_tab(browser_, URL_GOST),  # ГОСТ
        'nsi': make_new_tab(browser_, URL_NSI),  # СГР
    }
    return tabs


def make_dict_ogrn_address(file: str) -> dict:
    """Собрать и вернуть словарь из ключей: ОГРН и значений: адресов юридических лиц."""
    try:
        df = pd.read_excel(file)
    except FileNotFoundError:
        return {}
    dict_ = {}
    for _, row in df.iterrows():
        dict_[row['ОГРН заявителя']] = row['Адрес заявителя']
        dict_[row['ОГРН изготовителя']] = row['Адрес изготовителя']
    return dict_


def define_type_of_doc(number: str) -> str | None:
    """Проверить номер декларации из xlsx файла и определить какой тип документа."""
    pattern_declaration1 = r'(ЕАЭС N RU Д-[\w\.]+)'
    pattern_declaration2 = r'(РОСС RU Д-[\w\.]+)'
    pattern_certificate = r'(ЕАЭС RU С-[\w\.]+)'
    pattern_nsi = r'\w{2}\.\d{2}\.(\d{2}|\w{2})\.\d{2}\.\d{2,3}\.\w\.\d{6}\.\d{2}\.\d{2}'

    if re.match(pattern_declaration1, number) or re.match(pattern_declaration2, number):
        return 'declaration'
    if re.match(pattern_certificate, number):
        return 'certificate'
    if re.match(pattern_nsi, number):
        return 'nsi'

    return None


def make_series_for_result(data: dict) -> pd.Series:
    """Создать Series для добавления в лист мониторинга."""
    data['ФИО'] = 'Код'
    data['Дата проверки'] = datetime.now().strftime('%d.%m.%Y-%H.%M.%S')
    list_for_series = []
    for title in TITLE_FOR_SERIES_TO_FINAL_DF:
        if title in data:
            list_for_series.append(data[title])
        else:
            list_for_series.append('-')

    series = pd.Series(list_for_series, index=COLUMNS_FOR_FINAL_DF[5:])

    return series


def return_existing_result_file_or_create_new(file: str) -> str:
    """Проверить есть ли xlsx файл для временного хранения данных,
    если да - открыть его, если нет_ создать."""
    if os.path.isfile(file):
        return file
    df = pd.DataFrame(columns=[COLUMNS_FOR_FINAL_DF])
    df.to_excel(file)

    return file


##################################################################################
# Класс для работы с сайтом ФСА.
##################################################################################
class FSAScrapper:
    """Класс для сбора данных с сайта ФСА."""

    def __init__(self, browser_, wait_):
        """Инициация объекта. Принимает browser, wait"""
        self.browser = browser_
        self.wait = wait_
        self.chapter_xpath = X_PATHS['fsa_chapter']
        self.required_keys = REQUIRED_KEYS_TO_FSA

    def input_document_number(self, document_number: str):
        """Открыть страницу с полем для ввода номера документа,
        ввести номер декларации, нажать на кнопку 'найти'."""
        input_number_document = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, X_PATHS['fsa_input_field'])))
        input_number_document.clear()
        input_number_document.send_keys(document_number)
        button_search = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, X_PATHS['fsa_search_button'])))
        button_search.click()
        request_time = time.time()
        return request_time

    def pick_needed_document_in_list(self, document_number: str):
        """Обновить браузер, дождаться список документов,
        кликнуть по нужному документу в списке."""
        try:
            document_number = document_number.strip()
            needed_document_element = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, X_PATHS['fsa_pick_document'])))  # Элемент для клика.
            while needed_document_element.text.strip() != document_number:
                needed_document_element = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, X_PATHS['fsa_pick_document'])))
            needed_document_element.click()
            return True

        except TimeoutException:
            return False

    def return_to_input_document_number(self, xpath) -> None:
        """После сохранения данных по декларации нажать на возврат
        для ввода следующего номера декларации."""
        back_to_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        back_to_input.click()

    def get_inner_elements(self, chapter) -> dict:
        """Собрать внутренние элементы на веб-странице. Для которых
        недостаточно метода get_data_on_document_by_columns"""
        inner_elements = {}
        self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME,
                                                             'card-edit-row__content')))
        keys = self.browser.find_elements(By.CLASS_NAME, 'card-edit-row__header')
        values = self.browser.find_elements(By.CLASS_NAME, 'card-edit-row__content')
        for key, value in zip(keys, values):
            inner_elements[key.text + ' ' + chapter] = value.text
        return inner_elements

    def get_data_on_document(self, type_of_doc: str) -> dict:
        """Собрать с WEB страницы данные в словарь по определенным в шаблоне
         колонкам."""

        try:  # Пытаемся найти статус документа.
            status = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, X_PATHS['fsa_doc_status']))).text
        except TimeoutException:
            status = 'Статус не найден на ФСА'

        if status != 'ДЕЙСТВУЕТ':  # Любой статус кроме ДЕЙСТВУЕТ
            data = {'Статус на сайте': status}
            data.update(BLANK_DICT_FOR_FILLING)
            if type_of_doc == 'declaration':
                self.return_to_input_document_number(X_PATHS['fsa_return_declaration'])
            else:
                self.return_to_input_document_number(X_PATHS['fsa_return_certificate'])
            return data

        # Для действующей декларации.
        data = {'Статус на сайте': self.wait.until(EC.presence_of_element_located(
            (By.XPATH, X_PATHS['fsa_doc_status']))).text}
        # Определяем номер последней главы - количество итераций для сбора данных.
        elements = self.wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, X_PATHS['fsa_last_iter'])))
        number_of_last_chapter = len(elements)  # Номер последней итерации.

        # Перебираем и кликаем по подразделам на странице.
        for item in range(1, number_of_last_chapter + 1):
            time.sleep(random.randint(1, 3))
            data = self.get_data_from_one_chapter(data, item, type_of_doc)

        # Возвращение на страницу для ввода номера документа.
        if type_of_doc == 'declaration':
            self.return_to_input_document_number(X_PATHS['fsa_return_declaration'])
        else:
            self.return_to_input_document_number(X_PATHS['fsa_return_certificate'])

        if data:
            data['Наличие ДОС'] = 'Да'
            data['Соответствие с сайтом'] = 'Соответствует'

        return data

    def get_data_from_one_chapter(self, data, item, type_of_doc):
        """Собрать данные с одного подраздела на сайте ФСА."""
        # Кликаем слева по подразделу.
        needed_chapter = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, self.chapter_xpath + f'[{item}]/a')))
        needed_chapter.click()
        # Имя подзаголовка, берем из ссылки перед нажатием.
        chapter = needed_chapter.get_attribute('href')
        chapter = chapter[chapter.rfind('/') + 1:]
        # Собираем данные со страницы.
        headers = self.browser.find_elements(By.CLASS_NAME, "info-row__header")  # Ключи
        texts = self.browser.find_elements(By.CLASS_NAME, "info-row__text")  # Значения

        # Преобразуем данные в словарь.
        for header, text in zip(headers, texts):
            key = header.text.strip()
            # Берем только те ключи и значения, который в списке необходимых колонок.
            if key in self.required_keys:
                value = text.text.strip()
                # Если ключ уже в словаре, то добавляем к ключу строку - название подраздела.
                if key == ('Основной государственный регистрационный '
                           'номер юридического лица (ОГРН)'):
                    data['ОГРН' + ' ' + chapter] = value
                else:
                    data[key + ' ' + chapter] = value
            continue

        # Для сертификатов изъятие данных отличается. Собираются внутренние элементы.
        if chapter in {'applicant', 'manufacturer'} and type_of_doc == 'certificate':
            inner_data = self.get_inner_elements(chapter)
            data.update(inner_data)
        return data

    def get_data_from_fsa(self, doc_number, type_of_doc, tabs):
        """Общий метод диспетчер для деклараций и сертификатов."""
        # Переключаемся на соответсвующее окно в соответствии от типа документа.
        if type_of_doc == 'declaration':
            self.browser.switch_to.window(tabs['declaration'])
        elif type_of_doc == 'certificate':
            self.browser.switch_to.window(tabs['certificate'])

        # На сайте вводим номер декларации.
        request_time = self.input_document_number(doc_number)
        time.sleep(random.randint(1, 3))

        # Выбираем нужный документ.
        picked = self.pick_needed_document_in_list(doc_number)
        if picked is True:
            data = self.get_data_on_document(type_of_doc)  # Данные ФСА.
            return data, request_time

        return {'Статус на сайте': "Статус не найден на ФСА"}, request_time


##################################################################################
# Главная функция для работы с сайтами через браузер.
##################################################################################
def checking_data_in_iteration_through_browser(
        input_file: str, output_file: str, browser_, wait_) -> None:
    """
    Проверка данных на интернет ресурсах.

    Открывает файл excel с данными после проверки в ГОЛД, определяет откуда продолжать проверку,
    читает построчно, берет номер документа, определяет тип документа,
    исходя из типа, собирает данные с сайтов ФСА, СГР, вызывая при этом
    соответствующую функцию или метод. Также добавляет к данным
    сведения с ЕГРЮЛ и по ГОСТ. Полученные с интернет ресурсов данные добавляет к
    данным из ГОЛД, создает Series который добавляет к новому DataFrame записывает его в файл.
    Также отслеживает количество обращений к сайту ФСА и в случае превышения 20 раз,
    вызывает исключение, на которое внешняя функция закрывает браузер и
    открывает браузер с новыми фейковыми данными.
    Также отслеживает время, прошедшее с последнего запроса к сайту ФСА.
    """

    # Итоговый файл проверяем есть ли он или нет, если нет, то создаем.
    output_file = return_existing_result_file_or_create_new(output_file)

    gold_df = pd.read_excel(input_file)  # Данные из xlsx после ГОЛД
    old_df = pd.read_excel(output_file)  # DataFrame из уже проверенных в WEB данных.
    new_df = pd.DataFrame(columns=[COLUMNS_FOR_FINAL_DF])  # Новый DataFrame, для конечного результата
    # Словарь из ОГРН и адресов.
    dict_ogrn_address = make_dict_ogrn_address(output_file)

    # Определяем последнюю проверенную из ГОЛД файла строку.
    try:
        last_row_name_from_gold = read_last_viewed_number_from_file(VIEWED_IN_FSA_NUMBERS)
        if last_row_name_from_gold is None:
            last_row_name_from_gold = 0
    except:
        last_row_name_from_gold = 0

    # Создаем в браузере 5 вкладок для попеременной работы с сайтами.
    tabs = make_all_required_tabs(browser_)  # Словарь вкладок
    times = 0  # Количество обращений к сайту ФСА.
    request_time = 0  # Прошедшее с последнего запроса к сайту ФСА время.

    try:
        # Через цикл перебираем строки в ГОЛД файле.
        for _, row in gold_df.iloc[last_row_name_from_gold:].iterrows():

            # Если более 20 раз обращались к сайту в ФСА, то поднять исключение,
            # открыть новый браузер с новыми фейковыми данными.
            if times > 20:
                raise MaxIterationException

            data = {}
            doc_number = row['ДОС']  # Номер документа из DataFrame из ГОЛД
            # Прогоняем через паттерны, определяем тип документа.
            type_of_doc = define_type_of_doc(doc_number)

            # Если номер документа не ФСА и не СГР
            if type_of_doc is None:
                data['Статус на сайте'] = '-'
            # Если тип документа СГР
            elif type_of_doc == 'nsi':
                browser_.switch_to.window(tabs['nsi'])
                data = get_data_from_nsi_web(doc_number, browser_, wait_)
            # Если тип документа ФСА
            elif type_of_doc in {'declaration', 'certificate'}:
                # Высчитываем время, прошедшее с последнего обращения к сайту ФСА.
                time_from_last_request = time.time() - request_time
                # Проверяем прошло ли 15 секунд.
                if time_from_last_request < 15:
                    time.sleep(15 - time_from_last_request)
                # Собираем данные по декларации с сайта ФСА.
                fsa_scrapper = FSAScrapper(browser_, wait_)
                data, request_time = fsa_scrapper.get_data_from_fsa(doc_number, type_of_doc, tabs)
                times += 1  # Увеличиваем счетчик обращения к сайту ФСА

            # Если статус документа 'рабочий'(действующий),
            # то собрать и добавить данные с ЕГРЮЛ и ГОСТ.
            if data['Статус на сайте'] in {'ДЕЙСТВУЕТ', 'подписан и действует'}:
                data, dict_ogrn_address = add_to_data_egrul_information(
                    data, tabs, dict_ogrn_address, browser_, wait_)  # ЕГРЮЛ
                data = add_to_data_gost_information(data, tabs, browser_, wait_)  # ГОСТ

            # Формируем Series с собранными данными и добавляем его в DataFrame.
            new_series = make_series_for_result(data)
            new_row = row._append(new_series)  # Объединяем со старым Series
            new_df = new_df._append(new_row, ignore_index=True)  # Добавляем в DF

        # При нормальной работе цикла записать последнюю строку.
        write_last_viewed_number_to_file(VIEWED_IN_FSA_NUMBERS, row.name)
        # Если была последняя строка из ГОЛД файла выйти из кода.
        if row.name == gold_df.iloc[-1].name:
            sys.exit()

    except (TimeoutException, EgrulCaptchaException, ElementClickInterceptedException,
            StaleElementReferenceException, MaxIterationException, NoSuchWindowException,
            KeyboardInterrupt) as e:
        logging.error(e)
        raise StopBrowserException

    finally:
        # Записать новый DataFrame и последнюю строку из голда в файлы.
        total_df = pd.concat([old_df, new_df])
        with pd.ExcelWriter(output_file, engine="openpyxl", mode='w') as writer:
            total_df.to_excel(writer, index=False, columns=COLUMNS_FOR_FINAL_DF)
        write_last_viewed_number_to_file(VIEWED_IN_FSA_NUMBERS, row.name)


def launch_checking(range_: int, input_file: str, output_file: str):
    """
    Запуск кода из модуля в цикле.

    Условно внешняя функция для функции checking_data_in_iteration_through_browser.
    Запускает ее в цикле, каждый раз с новым браузером и данными.
    """

    logging.info("Старт проверки данных на интернет ресурсах: ФСА, СГР, ЕГРЮЛ, ГОСТ.")
    for i in range(range_):

        try:
            # Настройки браузера.
            service = Service(PATH_TO_DRIVER)
            service.start()
            options = webdriver.ChromeOptions()
            options.add_argument("--window-size=1920,1080")
            # Подключать прокси на четных итерациях.
            if i % 2 == 0:
                options.add_argument(f'--proxy-server={PROXY}')
            # options.add_argument('--headless')
            # Фейковый данные user agent
            ua = UserAgent()
            user_agent = ua.random
            options.add_argument(f'--user-agent={user_agent}')
            browser = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(browser, 5)
            logging.info("Старт итерации проверки данных в интернете № %d", i)
            # Запуск внутренней функции проверки данных в интернете.
            checking_data_in_iteration_through_browser(input_file, output_file, browser, wait)

        except StopBrowserException as error:
            logging.error(error.msg)
            browser.quit()  # Закрыть браузер.
            time.sleep(random.randint(1, 3))
