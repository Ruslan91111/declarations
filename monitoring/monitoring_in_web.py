"""Модуль проверки"""
import logging
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
                                        StaleElementReferenceException)

from monitoring.exceptions import SeleniumNotFoundException, EgrulCaptchaException
from monitoring.supporting_functions import (write_viewed_numbers_to_file,
                                             read_viewed_numbers_of_documents,
                                             check_or_create_temporary_xlsx)

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

PATH_TO_DRIVER = (r'C:\Users\RIMinullin\PycharmProjects'
                  r'\someProject\selenium_through\chromedriver.exe')

# Файлы
VIEWED_IN_FSA_NUMBERS = r'.\viewed_in_web_numbers.txt'
INPUT_FILE = r'gold_data.xlsx'
RESULT_FILE = r'result_data_after_web.xlsx'
LOGGING_FILE_WEB_MONITORING = r'.\monitoring_in_web_log.log'

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
    'Статус на сайте': '-',
    'Соответствие с сайтом': '-',
    'Соответствие адресов с ЕГРЮЛ': '-',
    'Адрес места нахождения applicant': '-',
    'Статус НД': '-'
}

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


COLUMNS_FOR_FINAL_DF = [
    'Код товара', 'Наименование товара', 'ДОС',
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
    filename=LOGGING_FILE_WEB_MONITORING,
    filemode="a",
    encoding='utf-8',
    format="%(asctime)s %(levelname)s %(message)s",
)


##################################################################################
#  ЕГРЮЛ
# Работа с адресами - проверяем адреса юридических лиц, взятые с сайта ФСА.
# Дополнительно берем адреса по ОГРН с сайта ЕГРЮЛ и сравниваем между собой.
##################################################################################
def add_egrul_information(data: dict, tabs: dict, dict_ogrn_address: dict,
                          browser_, wait_) -> (dict, dict):
    """Добавить в словарь адреса из ЕГРЮЛ. Предварительно проверить не проверяли ли
    ОГРН ранее, если да, то взять адрес из словаря ранее проверенных, если не проверяли,
    то открыть сайт ЕГРЮЛ и взять из него адрес. В конце функции сравнить адреса
    и записать вывод о соответствии."""

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
        data = _compare_addresses(data)  # ОГРН был - вызвать функцию сравнения адресов.

    return data, dict_ogrn_address


def get_address_from_egrul(data_web: dict, org: str, browser_, wait_) -> dict:
    """Взять адрес с сайта ЕГРЮЛ по ОГРН. Если ОГРН нет, то так и записать."""

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
            text = wait_.until(EC.element_to_be_clickable((By.CLASS_NAME, 'res-text'))).text
            data_web[f'Адрес места нахождения {org} ЕГРЮЛ'] = text[:text.find('ОГРН')].strip(' ,')
            browser_.refresh()  # Обновить вкладку, для следующего ввода.

        except TimeoutException:
            raise EgrulCaptchaException

    else:  # Если ОГРН у юр.лица нет.
        data_web[f'Адрес места нахождения {org} ЕГРЮЛ'] = 'Нет ОГРН'

    return data_web


def _compare_addresses(data: dict) -> dict:
    """Сравнить строки - адреса: с сайта и ЕГРЮЛ."""
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
def add_gost_information(data: dict, tabs: dict, browser_, wait_):
    """Добавить к словарю данные о статусе ГОСТ."""
    browser_.switch_to.window(tabs['gost'])
    data = check_gost(data, wait_)  # ГОСТ.
    return data


def check_gost(data: dict, wait_):
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
                element = wait_.until(EC.element_to_be_clickable(
                    (By.XPATH, X_PATHS['gost_status'])))
                text = element.text
                status_gost.add(text)

            data['Статус НД'] = " ".join(status_gost)  # Сохранить значения с сайта ГОСТ

        else:  # Если данных о ГОСТе нет.
            data['Статус НД'] = '-'

    return data


##################################################################################
# Работа с сайтом nsi - проверка свидетельства о гос.регистрации
##################################################################################
def _get_dict_from_text_nsi(text: str, type_of_org: str) -> dict:
    """Функция для поиска в тексте с сайта nsi для словаря данных по юридическому лицу. """
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


def get_data_from_nsi(document_number, browser_, wait_) -> None | dict:
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
            return BLANK_DICT_FOR_FILLING
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


def check_number_declaration(number: str) -> str | None:
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

    series = pd.Series(list_for_series, index=COLUMNS_FOR_FINAL_DF[3:])

    return series


##################################################################################
# Главная функция для работы с сайтами через браузер.
##################################################################################
def checking_data_on_web(input_file: str, output_file: str, browser_, wait_):
    """Основная функция - работа с данными в вебе, на сайтах,
    последующее их преобразование и работы с ними в DataFrame."""

    # Просмотренные номера деклараций. Берем из файла.
    viewed_numbers = read_viewed_numbers_of_documents(VIEWED_IN_FSA_NUMBERS)
    gold_df = pd.read_excel(input_file)  # Данные из xlsx после ГОЛД
    new_df = pd.DataFrame(columns=[COLUMNS_FOR_FINAL_DF])  # Новый DataFrame, для итоговых данных
    dict_ogrn_address = make_dict_ogrn_address(output_file)  # Словарь ОГРН и адресов.

    # Создаем в браузере 5 вкладок.
    tabs = make_all_required_tabs(browser_)  # Словарь вкладок

    try:
        for _, row in gold_df.iterrows():  # Перебираем документы.
            data = {}
            doc_number = row['ДОС']  # Номер документа из старого DataFrame из ГОЛД
            # Пропустить итерацию если ранее документ просматривали.
            if doc_number in viewed_numbers:
                continue

            # Прогоняем через паттерны, определяем тип документа.
            type_of_doc = check_number_declaration(doc_number)
            if type_of_doc is None:  # Если номер документа не ФСА и не СГР
                data['Статус на сайте'] = '-'
            elif type_of_doc == 'nsi':  # Если СГР
                browser_.switch_to.window(tabs['nsi'])
                data = get_data_from_nsi(doc_number, browser_, wait_)
            elif type_of_doc in {'declaration', 'certificate'}:  # Если ФСА
                fsa_scrapper = FSAScrapper(browser_, wait_)
                data = fsa_scrapper.get_data_from_fsa(doc_number, type_of_doc, tabs)

            # Если статус документа 'рабочий', то собрать данные с ЕГРЮЛ и ГОСТ.
            if data['Статус на сайте'] in {'ДЕЙСТВУЕТ', 'подписан и действует'}:
                data, dict_ogrn_address = add_egrul_information(
                    data, tabs, dict_ogrn_address, browser_, wait_)  # ЕГРЮЛ
                data = add_gost_information(data, tabs, browser_, wait_)  # ГОСТ

            # Формируем Series с собранными данными и добавляем его в DataFrame.
            new_series = make_series_for_result(data)
            new_row = row._append(new_series)  # Объединяем со старым Series
            new_df = new_df._append(new_row, ignore_index=True)
            viewed_numbers.add(doc_number)

    except (TimeoutException, EgrulCaptchaException, ElementClickInterceptedException,
            StaleElementReferenceException) as e:
        logging.error(e.msg)
        raise SeleniumNotFoundException from e

    finally:  # Записать новый DataFrame и просмотренные номера.
        output_file = check_or_create_temporary_xlsx(output_file)
        old_df_from_result = pd.read_excel(output_file)
        total_df = pd.concat([old_df_from_result, new_df])
        with pd.ExcelWriter(output_file, engine="openpyxl", mode='w') as writer:
            total_df.to_excel(writer, index=False, columns=COLUMNS_FOR_FINAL_DF)
        write_viewed_numbers_to_file(VIEWED_IN_FSA_NUMBERS, viewed_numbers)
        logging.info('Номер документа, на котором произошло исключение - %s' % doc_number)


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
        self.input_document_number(doc_number)
        # Выбираем нужный документ.
        picked = self.pick_needed_document_in_list(doc_number)
        if picked is True:
            data = self.get_data_on_document(type_of_doc)  # Данные ФСА.
            return data

        return {'Статус на сайте': "Статус не найден на ФСА"}


def launch_checking(range_):
    """Запуск кода из модуля в цикле. При каждой итерации,
    создается браузер. По окончании итерации браузер закрывается."""

    logging.info("Начало работы программы по работе с WEB мониторингом - 'monitoring_in_web'")
    for i in range(range_):
        try:
            # Настройки браузера.
            service = Service(PATH_TO_DRIVER)
            service.start()
            options = webdriver.ChromeOptions()
            options.add_argument("--window-size=1920,1080")
            ua = UserAgent()
            user_agent = ua.random
            options.add_argument(f'--user-agent={user_agent}')
            # Экземпляр браузера и wait.
            browser = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(browser, 5)
            logging.info("Старт итерации № %d", i)
            checking_data_on_web(INPUT_FILE, RESULT_FILE, browser, wait)

        except SeleniumNotFoundException as error:
            logging.error(error.msg)
            browser.quit()  # Закрыть браузер.


if __name__ == '__main__':
    launch_checking(1)
