from datetime import datetime
import re
from types import NoneType

import pandas as pd
import pyautogui
from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium_through.supporting_functions import write_viewed_numbers_to_file, read_viewed_numbers_of_documents


URL_FSA_DECLARATION = "https://pub.fsa.gov.ru/rds/declaration"
URL_FSA_CERTIFICATE = "https://pub.fsa.gov.ru/rss/certificate"
URL_EGRUL = "https://egrul.nalog.ru/"
URL_GOST = "https://etr-torgi.ru/calc/check_gost/"

date_today = datetime.now().strftime('%Y-%m-%d')
URL_NSI = f'https://nsi.eaeunion.org/portal/1995?date={date_today}'

PATH_TO_DRIVER = (r'C:\Users\RIMinullin\PycharmProjects'
                  r'\someProject\selenium_through\chromedriver.exe')

VIEWED_IN_FSA_NUMBERS = r'.\viewed_in_fsa_numbers.txt'


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
    ' ЭТ ', 'ЭТАЖ '
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

    # ГОСТ
    'gost_input_field': '//*[@id="poisk-form"]/input',
    'gost_search_button': '//*[@id="gost_filter"]',
    'gost_status': '//*[@id="data-box"]/div/div/div/p/b',

}

# Словарь для заполнения прочерками.
BLANK_DICT_FOR_FILLING = {
    'Наличие ДОС': 'Не найдено на сайте ФСА',
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
    'Соответствие адресов с ЕГРЮЛ',
    'Адрес места нахождения applicant',
    'Адрес места нахождения applicant ЕГРЮЛ',
    'Адрес места нахождения manufacturer',
    'Адрес места нахождения manufacturer ЕГРЮЛ',
    'Статус НД',
    'ФИО',
]

COLUMNS_FOR_FINAL_DF = [
    'Код товара', 'Наименование товара', 'ДОС', 'Поставщик',
    'Изготовитель', 'Дата проверки', 'Наличие ДОС', 'Соответствие с сайтом',
    'Статус на сайте', 'Соответствие адресов с ЕГРЮЛ',
    'Адрес заявителя', 'Адрес заявителя ЕГРЮЛ', 'Адрес изготовителя',
    'Адрес изготовителя ЕГРЮЛ', 'Статус НД', 'ФИО'
]

##################################################################################
# Создание экземпляра браузера и настройка, а также экземпляра wait.
##################################################################################
service = Service(PATH_TO_DRIVER)
service.start()
options = webdriver.ChromeOptions()
options.add_argument("--window-size=1920,1080")
ua = UserAgent()
user_agent = ua.random
options.add_argument(f'--user-agent={user_agent}')
browser = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(browser, 15)


##################################################################################
# Работа с адресами - проверяем адреса юридических лиц, взятые с сайта ФСА.
# Дополнительно берем адреса по ОГРН с сайта ЕГРЮЛ и сравниваем между собой.
##################################################################################
def _compare_addresses(data: dict) -> dict:
    """Сравнить строки - адреса: с сайта ФСА и ЕГРЮЛ."""
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
        for i in elements_to_be_removed:
            string = string.replace(i, ' ')
        string = string.replace(' ', '')
        result = sorted(string)
        return result

    try:
        # Привести адреса к единому виду - отсортированным спискам строк.
        applicant = prepare_addresses(data['Адрес места нахождения applicant'])
        applicant_egr = prepare_addresses(data['Адрес места нахождения applicant ЕГРЮЛ'])
        manufacturer = prepare_addresses(data['Адрес места нахождения manufacturer'])
        manufacturer_egr = prepare_addresses(data['Адрес места нахождения manufacturer ЕГРЮЛ'])

        if applicant == applicant_egr and manufacturer == manufacturer_egr:
            data['Соответствие адресов с ЕГРЮЛ'] = 'Соответствуют'
        else:
            data['Соответствие адресов с ЕГРЮЛ'] = 'Не соответствуют'
    except:
        pass

    return data


def get_addresses_from_egrul(data_web: dict, browser, wait) -> dict:
    """Проверить адреса с ЕГРЮЛ. Открыть сайт ЕГРЮЛ, ввести номер ОГРН
    заявителя, взять адрес, сравнить с адресом с сайта Росаккредитации.
    Аналогично для изготовителя."""
    #  Выполнить две итерации для заявителя и изготовителя.
    applicant_and_manufacturer = ('applicant', 'manufacturer')
    for i in applicant_and_manufacturer:

        # Проверяем есть ли ОГРН у юр.лица, по которому можно проверить адрес на сайте ЕГРЮЛ.
        if f'ОГРН {i}' in data_web.keys():
            # Ищем поле для ввода
            needed_element = wait.until(EC.element_to_be_clickable(
                (By.XPATH, X_PATHS['egrul_input'])))
            needed_element.send_keys(data_web[f'ОГРН {i}'])  # Ввести ОГРН
            button_search = wait.until(EC.element_to_be_clickable(
                (By.XPATH, X_PATHS['search_button_egrul'])))
            button_search.click()  # Нажать найти

            # Сохраняем в словарь адрес с сайта ЕГРЮЛ.
            text = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'res-text'))).text
            data_web[f'Адрес места нахождения {i} ЕГРЮЛ'] = text[:text.find('ОГРН')].strip(' ,')
            browser.refresh()  # Обновить вкладку, для следующего ввода.

        else:  # Если ОГРН у юр.лица нет.
            data_web[f'Адрес места нахождения {i} ЕГРЮЛ'] = 'Нет ОГРН'

    # Блок - записываем в словарь результат сравнения.
    if 'Нет ОГРН' in data_web.values():  # Если у поставщика или изготовителя не было ОГРН.
        data_web['Соответствие адресов с ЕГРЮЛ'] = 'НЕТ ОГРН'
    else:
        data_web = _compare_addresses(data_web)  # Вызвать функцию сравнения адресов.

    return data_web


##################################################################################
# Работа с ГОСТ.
##################################################################################
def check_gost(data: dict, browser, wait):
    """Проверить ГОСТ, взятый с сайта ФСА на сайте проверки ГОСТ"""
    # Сокращения для ключей
    product = 'Наименование документа product'
    standard = "Обозначение стандарта, нормативного документа product"

    # Проверяем взяты ли данные ФСА с тех полей, где могут содержаться номера ГОСТ.
    if product in data or standard in data:

        # Берем непосредственно текст, в котором может быть номер ГОСТ.
        if product in data and standard in data:
            text = data[product] + data[standard]
        elif product in data:
            text = data[product]
        elif standard in data:
            text = data[standard]

        # Ищем подстроку, совпадающую с паттерном ГОСТ.
        pattern_gost = r"\b\d{5}-\d{2,4}\b"
        result = re.findall(pattern_gost, text)

        # Если в тексте ГОСТ есть, ввести на сайте .
        if result:
            gost_number = result[0]
            needed_element = wait.until(EC.element_to_be_clickable(
                (By.XPATH, X_PATHS['gost_input_field'])))
            needed_element.clear()
            needed_element.send_keys('ГОСТ ' + gost_number)  # Ввести номер ГОСТ
            button_search = wait.until(EC.element_to_be_clickable(
                (By.XPATH, X_PATHS['gost_search_button'])))
            button_search.click()  # Нажать найти
            # Сохранить статус ГОСТа на сайте.
            element = wait.until(EC.element_to_be_clickable(
                (By.XPATH, X_PATHS['gost_status'])))
            text = element.text
            data['Статус НД'] = text  # Сохранить значение с сайта ГОСТ
            return data

    # Если данных о ГОСТе нет.
    data['Статус НД'] = '-'
    return data


##################################################################################
# Работа с сайтом eaeunion.org - проверка свидетельства о гос.регистрации
##################################################################################
def _get_dict_from_text_nsi(text: str, type_of_org: str) -> dict:
    """Функция для поиска в тексте с сайта nsi для словаря данных по юридическому лицу. """
    data = {}  # Словарь для возврата данных.
    pattern_index = r'\d{6}'  # Паттерн для поиска почтового индекса.
    match_index = re.search(pattern_index, text)  # Ищем почтовый индекс.
    if match_index:  # Если почтовый индекс есть в тексте
        # То, что в тексте до почтового индекса сохраняем в качестве наименования юр.лица.
        data[f'Полное наименование юридического лица {type_of_org}'] = text[:match_index.start()].strip(" ,")
        data[f'Адрес места нахождения {type_of_org}'] = text[match_index.start():text.find('[')]
    elif '[' in text:  # Если нет почтового индекса.
        data[f'Полное наименование юридического лица {type_of_org}'] = text[:text.find('[') + 1]
    else:
        data[f'Полное наименование юридического лица {type_of_org}'] = text

    # ОГРН
    pattern_ogrn = r'\d{13}'  # Паттерн для поиска ОГРН.
    ogrn = re.search(pattern_ogrn, text)
    if type(ogrn) == NoneType:
        data[f'ОГРН {type_of_org}'] = 'Нет ОГРН'
    else:
        data[f'ОГРН {type_of_org}'] = ogrn.group()

    return data


def get_data_from_nsi(document_number, browser=browser, wait=wait) -> None | dict:
    """Собрать данные по свидетельству о государственной регистрации с сайта nsi.
    Вернет либо словарь, достаточный для добавления и последующей записи, либо None"""
    # Найти и нажать на кнопку фильтра - после чего можно ввести номер СГР
    filter_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, X_PATHS['nsi_filter'])))
    filter_button.click()

    # Дождаться возможности ввода номера СГР.
    input_number_field = wait.until(EC.element_to_be_clickable(
        (By.XPATH, X_PATHS['nsi_input_field'])))
    input_number_field.clear()
    input_number_field.send_keys(document_number)# Ввести номер СГР

    # Нажать на галочку - запустить поиск.
    check_mark = wait.until(EC.element_to_be_clickable((By.XPATH, X_PATHS['nsi_check_mark'])))
    check_mark.click()

    # Проверяем есть ли данные. Если данных нет, то будет соответсвующее сообщение на странице.
    try:
        data_on_nsi = browser.find_element(By.XPATH, X_PATHS['nsi_no_data']).text
        if data_on_nsi == 'Нет данных':
            return None
    except:  # Если сообщение об отсутствии данных не найдено, то продолжить выполнение кода.
        pass

    # Создаем словарь с данными по СГР. Сохраняем первую пару ключ - значение.
    data = {'Статус на сайте': wait.until(EC.element_to_be_clickable(
        (By.XPATH, X_PATHS['nsi_status']))).text}

    # Добавляем в data данные по заявителю, производителю, документации и по остальным ключам.
    text_applicant = wait.until(EC.presence_of_element_located(
        (By.XPATH, X_PATHS['nsi_applicant']))).text
    data.update(_get_dict_from_text_nsi(text_applicant, 'applicant'))

    text_manufacturer = wait.until(EC.presence_of_element_located(
        (By.XPATH, X_PATHS['nsi_manufacturer']))).text
    data.update(_get_dict_from_text_nsi(text_manufacturer, 'manufacturer'))

    data['Наименование документа product'] = wait.until(
        EC.presence_of_element_located((By.XPATH, X_PATHS['nsi_document_name']))).text

    if data:
        data['Наличие ДОС'] = 'Да'
        data['Соответствие с сайтом'] = 'Соответствует'

    return data


##################################################################################
# Небольшие вспомогательные функции.
##################################################################################
def check_number_declaration(number: str) -> tuple | None:
    """Проверить номер декларации из xlsx файла и определить какой тип документа."""
    pattern_declaration1 = r'(ЕАЭС N RU Д-[\w\.]+)'
    pattern_declaration2 = r'(РОСС RU Д-[\w\.]+)'
    pattern_certificate = r'(ЕАЭС RU С-[\w\.]+)'
    pattern_nsi = r'\w{2}\.\d{2}\.(\d{2}|\w{2})\.\d{2}\.\d{2,3}\.\w\.\d{6}\.\d{2}\.\d{2}'

    if re.match(pattern_declaration1, number) or re.match(pattern_declaration2, number):
        return number, 'declaration'

    elif re.match(pattern_certificate, number):
        return number, 'certificate'

    elif re.match(pattern_nsi, number):
        return number, 'nsi'

    else:
        return number, None


def make_series_for_result(fsa_data: dict) -> pd.Series:
    """Создать Series для добавления в лист мониторинга."""
    list_for_series = []
    for i in TITLE_FOR_SERIES_TO_FINAL_DF:
        if i in fsa_data:
            list_for_series.append(fsa_data[i])
        else:
            list_for_series.append('-')

    series = pd.Series(list_for_series, index=[
        'Поставщик', 'Дата проверки', 'Наличие ДОС',
        'Соответствие с сайтом', 'Статус на сайте',
        'Соответствие адресов с ЕГРЮЛ', 'Адрес заявителя',
        'Адрес заявителя ЕГРЮЛ', 'Адрес изготовителя',
        'Адрес изготовителя ЕГРЮЛ', 'Статус НД', 'ФИО'])

    return series


##################################################################################
# Главная функция для работы с сайтами через браузер.
##################################################################################
def launch_checking_data(file_after_gold: str, file_result: str, sheet: str):
    """Основная функция - работа с данными в вебе, на сайтах,
    последующее их преобразование и работы с ними в DataFrame."""

    # Просмотренные номера деклараций. Берем из файла.
    viewed_numbers = read_viewed_numbers_of_documents(VIEWED_IN_FSA_NUMBERS)

    # Создаем экземпляр для работы с браузером и 5 вкладок в нем.
    browser_handler = BrowserHandler(browser, wait)  # Класс - для работы с браузером.
    declaration_fsa_window = browser_handler.make_new_tab(URL_FSA_DECLARATION)
    certificate_fsa_window = browser_handler.make_new_tab(URL_FSA_CERTIFICATE)  # Сертификаты.
    egrul_window = browser_handler.make_new_tab(URL_EGRUL)  # ЕГРЮЛ
    gost_window = browser_handler.make_new_tab(URL_GOST)  # ГОСТ
    nsi_window = browser_handler.make_new_tab(URL_NSI)  # СГР

    gold_df = pd.read_excel(file_after_gold)  # Данные из xlsx после ГОЛД

    # Новый DataFrame, в котором будут итоговые данные.
    new_df = pd.DataFrame(columns=[COLUMNS_FOR_FINAL_DF])

    count = 0  # Для подсчета количества операций за цикл.

    try:
        # Перебираем документы.
        for _, row in gold_df.iterrows():
            fsa_data = {}
            number_document = row['ДОС']  # Номер документа из старого DataFrame из ГОЛД

            # Пропустить итерацию если ранее документ просматривали.
            if number_document in viewed_numbers:
                continue

            # Прогоняем через паттерны, определяем тип документа.
            number_document, type_of_doc = check_number_declaration(number_document)

            # Если номер документа не соответствует паттерну номера для ФСА или СГР
            if type_of_doc is None:
                fsa_data['ДОС'] = number_document

            # Если документ - это свидетельство о государственной регистрации.
            elif type_of_doc == 'nsi':
                browser_handler.switch_to_tab(nsi_window)
                #  Вернется или словарь данных, или None.
                fsa_data = get_data_from_nsi(number_document)
                if fsa_data:
                    browser_handler.switch_to_tab(egrul_window)
                    fsa_data = get_addresses_from_egrul(fsa_data, browser, wait)  # ЕГРЮЛ.
                    browser_handler.switch_to_tab(gost_window)
                    fsa_data = check_gost(fsa_data, browser, wait)  # ГОСТ.
                else:  # Если None
                    fsa_data = BLANK_DICT_FOR_FILLING

            # Если документ - это декларация или свидетельство с ФСА.
            elif type_of_doc == 'declaration' or type_of_doc == 'certificate':
                # Переключаемся на соответсвующее окно в соответствии от типа документа.
                if type_of_doc == 'declaration':
                    browser_handler.switch_to_tab(declaration_fsa_window)
                elif type_of_doc == 'certificate':
                    browser_handler.switch_to_tab(certificate_fsa_window)

                # На сайте вводим номер декларации.
                browser_handler.input_document_number(number_document)
                # Выбираем нужный документ.
                picked = browser_handler.pick_needed_document_in_list(number_document)

                if picked is True:
                    # Собрать словарь данных, с ФСА, ЕГРЮЛ, ГОСТ.
                    fsa_data = browser_handler.get_data_on_document(type_of_doc)  # Данные ФСА.
                    if fsa_data['Статус на сайте'] == 'ДЕЙСТВУЕТ':
                        browser.switch_to.window(egrul_window)
                        fsa_data = get_addresses_from_egrul(fsa_data, browser, wait)  # ЕГРЮЛ.
                        browser_handler.switch_to_tab(gost_window)
                        fsa_data = check_gost(fsa_data, browser, wait)  # ГОСТ.
                    else:
                        pass
                else:
                    fsa_data = BLANK_DICT_FOR_FILLING
                    fsa_data['Статус на сайте'] = 'Не найдено на ФСА'

            # Общий код для всех типов документов.
            fsa_data['ФИО'] = 'Код'
            fsa_data['Дата проверки'] = datetime.now().strftime('%d.%m.%Y-%H.%M.%S')
            # Формируем Series с собранными данными.
            new_series = make_series_for_result(fsa_data)
            # Объединяем со старым Series в один и добавляем в новый DataFrame.
            new_row = row._append(new_series)
            new_df = new_df._append(new_row, ignore_index=True)
            viewed_numbers.add(number_document)
            count += 1
    except:
        print('Произошла ошибка.\n', 'Количество обработанных в ГОЛД', count)
        raise Exception

    finally:
        # Прочитать из xlsx уже проверенные данные, объединить с полученными,
        # записать DataFrame в файл результат.
        old_df = pd.read_excel(file_result, sheet_name=sheet)
        total_df = pd.concat([old_df, new_df])
        with pd.ExcelWriter(file_result, if_sheet_exists='overlay',
                            engine="openpyxl", mode='a') as writer:
            total_df.to_excel(writer, sheet_name=sheet,
                              index=False, columns=COLUMNS_FOR_FINAL_DF)
        # А просмотренные коды товаров в текстовый файл.
        write_viewed_numbers_to_file(VIEWED_IN_FSA_NUMBERS, viewed_numbers)


class BrowserHandler:
    """Класс взаимодействия с браузером."""
    def __init__(self, browser, wait):
        """Инициация объекта. Принимает browser, wait"""
        self.browser = browser
        self.wait = wait
        self.chapter_xpath = X_PATHS['fsa_chapter']

    def make_new_tab(self, url):
        """Открыть новое окно в браузере с определенным
        сайтом и вернуть указатель на него."""
        self.browser.switch_to.new_window('tab')
        self.open_page(url)
        return browser.current_window_handle

    def switch_to_tab(self, tab):
        self.browser.switch_to.window(tab)

    def open_page(self, url) -> None:
        """Открыть страницу"""
        self.browser.get(url)

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

        except:
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
        self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'card-edit-row__content')))
        keys = self.browser.find_elements(By.CLASS_NAME, 'card-edit-row__header')
        values = self.browser.find_elements(By.CLASS_NAME, 'card-edit-row__content')
        for key, value in zip(keys, values):
            inner_elements[key.text + ' ' + chapter] = value.text
        return inner_elements

    def get_data_on_document(self, type_of_doc: str) -> dict:
        """Собрать с WEB страницы данные в словарь по определенным в шаблоне
         колонкам."""

        # Нужные ключи для сбора
        needed_columns = {
            'Статус декларации', 'Полное наименование юридического лица',
            'Сокращенное наименование юридического лица',
            'Основной государственный регистрационный номер юридического лица (ОГРН)',
            'Адрес места нахождения', 'Наименование документа',
            'Обозначение стандарта, нормативного документа'}

        # Создаем словарь для результатов работы, записываем первое значение.
        try:
            status = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, X_PATHS['fsa_doc_status']))).text
        except:
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
        for i in range(1, number_of_last_chapter + 1):
            try:
                # Кликаем слева по подразделу.
                needed_chapter = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, self.chapter_xpath + f'[{i}]/a')))
                needed_chapter.click()
                # Имя подзаголовка, берем из ссылки перед нажатием.
                chapter = needed_chapter.get_attribute('href')
                chapter = chapter[chapter.rfind('/') + 1:]

            except Exception as e:
                break

            headers = self.browser.find_elements(By.CLASS_NAME, "info-row__header")  # Ключи
            texts = self.browser.find_elements(By.CLASS_NAME, "info-row__text")  # Значения

            # Преобразуем данные в словарь.
            for header, text in zip(headers, texts):
                key = header.text.strip()
                # Берем только те ключи и значения, который в списке необходимых колонок.
                if key in needed_columns:
                    value = text.text.strip()

                    # Если ключ уже есть в словаре, то добавляем к ключу строку - название подраздела.
                    if key == 'Основной государственный регистрационный номер юридического лица (ОГРН)':
                        data['ОГРН' + ' ' + chapter] = value
                    else:
                        data[key + ' ' + chapter] = value

                continue

            # Для сертификатов изъятие данных отличается. Собираются внутренние элементы.
            if chapter in {'applicant', 'manufacturer'} and type_of_doc == 'certificate':
                inner_data = self.get_inner_elements(chapter)
                data.update(inner_data)

        # Возвращение на страницу для ввода номера документа.
        if type_of_doc == 'declaration':
            self.return_to_input_document_number(X_PATHS['fsa_return_declaration'])
        else:
            self.return_to_input_document_number(X_PATHS['fsa_return_certificate'])

        if data:
            data['Наличие ДОС'] = 'Да'
            data['Соответствие с сайтом'] = 'Соответствует'

        return data


# Ввод переменных от пользователя.
# path_to_checking_file = get_path_for_existing_file(MESSAGE_FOR_USER_VERIFIABLE_FILE)
# path_to_results_file = get_path_for_existing_file(MESSAGE_FOR_USER_RESULT_FILE)
# month = get_string_from_user(MESSAGE_FOR_USER_INPUT_SHEET_NAME)

# Создать лист в excel файл.
# create_sheet_write_codes_and_names(path_to_checking_file, path_to_results_file, month)

# data_of_checking(path_to_results_file, month)
launch_checking_data(r'C:\Users\RIMinullin\PycharmProjects\someProject\monitoring\temp_df.xlsx',
                    r'C:\Users\RIMinullin\PycharmProjects\someProject\monitoring\Мониторинг АМ (2023).xlsx',
                    'декабрь')
