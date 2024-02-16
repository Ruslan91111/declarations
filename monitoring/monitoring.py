from datetime import datetime
import re
import pandas as pd
import pyautogui
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service

from selenium.common.exceptions import TimeoutException


from selenium_through.supporting_functions import write_viewed_numbers_to_file, read_viewed_numbers_of_documents


URL_FSA_DECLARATION = "https://pub.fsa.gov.ru/rds/declaration"
URL_FSA_CERTIFICATE = "https://pub.fsa.gov.ru/rss/certificate"
URL_EGRUL = "https://egrul.nalog.ru/"
URL_GOST = "https://etr-torgi.ru/calc/check_gost/"

PATH_TO_DRIVER = (r'C:\Users\RIMinullin\PycharmProjects'
                  r'\someProject\selenium_through\chromedriver.exe')

VIEWED_IN_FSA_NUMBERS = r'.\viewed_in_fsa_numbers.txt'

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

X_PATHS = {
    'chapter': '//fgis-links-list/div/ul/li',
    'input_field': "//fgis-text/input",
    'search_button': "//button[contains(text(), 'Найти')]",
    'pick_document': "//*/div[1]/div/div/div/table/tbody/tr[2]/td[3]"
                     "/a/fgis-h-table-limited-text-cell/div[1]",
    'return_declaration': "//fgis-rds-view-declaration-toolbar/div/div[1]",
    'return_certificate': "//fgis-rss-view-certificate-toolbar/div/div[1]",
    'doc_status_on_fsa': '//fgis-toolbar-status/span',
    'last_iter': '//fgis-links-list/div/ul/li',
    'egrul_input': '//*[@id="query"]',
    'search_button_egrul': '//*[@id="btnSearch"]',
}

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
wait = WebDriverWait(browser, 30)


##################################################################################
# Работа с адресами - проверяем адреса юридических лиц, взятые с сайта ФСА.
# Дополнительно берем адреса по ОГРН с сайта ЕГРЮЛ и сравниваем между собой.
##################################################################################
def _compare_addresses(data: dict) -> dict:
    """Сравнить строки - адреса: с сайта ФСА и ЕГРЮЛ."""
    elements_to_be_removed = PARTS_TO_BE_REMOVED  # Элементы, которые нужно убрать из строк.

    def prepare_addresses(string: str) -> list:
        """Подготовить адреса перед сравнением - убрать сокращения, лишние знаки."""
        string = string.upper().replace('.', ' ').replace('(', '').replace(')', '').replace(',', ' ')
        # Убираем сокращения и обозначения.
        for i in elements_to_be_removed:
            string = string.replace(i, ' ')
        string = string.replace(' ', '')
        result = sorted(string)
        return result

    try:
        # Привести адреса к единому виду - отсортированные списки строк.
        applicant = prepare_addresses(data['Адрес места нахождения applicant'])
        applicant_egr = prepare_addresses(data['Адрес места нахождения applicant ЕГРЮЛ'])
        manufacturer = prepare_addresses(data['Адрес места нахождения manufacturer'])
        manufacturer_egr = prepare_addresses(data['Адрес места нахождения manufacturer ЕГРЮЛ'])

        if applicant == applicant_egr and manufacturer == manufacturer_egr:
            data['Соответствие адресов с ЕГРЮЛ'] = 'Соответствует'
        else:
            data['Соответствие адресов с ЕГРЮЛ'] = 'Не соответствует'

    except:
        pass

    return data


def get_addresses_from_egrul(data_web, browser, wait):
    """Проверить адреса с ЕГРЮЛ. Открыть сайт ЕГРЮЛ, ввести номер ОГРН
    заявителя, взять адрес, сравнить с адресом с сайта Росаккредитации.
    Аналогично для изготовителя."""

    # Перейти на сайт ЕГРЮЛ.
    browser.get(URL_EGRUL)

    #  Выполнить две итерации для заявителя и изготовителя.
    applicant_and_manufacturer = ('applicant', 'manufacturer')
    for i in applicant_and_manufacturer:
        needed_element = wait.until(EC.element_to_be_clickable((By.XPATH, X_PATHS['egrul_input'])))
        needed_element.click()

        # Проверяем есть ли ОГРН у юр.лица, по которому можно проверить адрес на сайте ЕГРЮЛ.
        if f'Основной государственный регистрационный номер юридического лица (ОГРН) {i}' in data_web.keys():
            # Ввести ОГРН
            needed_element.send_keys(
                data_web[f'Основной государственный регистрационный номер юридического лица (ОГРН) {i}'])

            # Нажать найти
            button_search = wait.until(EC.element_to_be_clickable((By.XPATH, X_PATHS['search_button_egrul'])))
            button_search.click()

            # Сохраняем адрес с сайта ЕГРЮЛ
            element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'res-text')))
            text = element.text
            data_web[f'Адрес места нахождения {i} ЕГРЮЛ'] = text[:text.find('ОГРН')].strip(' ,')
            browser.refresh()

        # Если ОГРН у юр.лица нет.
        else:
            data_web[f'Адрес места нахождения {i} ЕГРЮЛ'] = 'Нет ОГРН'

    # Если у поставщика или изготовителя не было ОГРН.
    if 'Нет ОГРН' in data_web.values():
        data_web['Соответствие адресов с ЕГРЮЛ'] = 'НЕТ ОГРН'

    # Вызвать функцию сравнения
    data_web = _compare_addresses(data_web)
    return data_web


##################################################################################
# Работа с ГОСТ.
##################################################################################
def check_gost(data: dict, browser, wait):
    """Проверить ГОСТ, взятый с сайта ФСА на сайте проверки ГОСТ"""

    # Проверяем взяты ли данные ФСА с тех полей, где могут содержаться номера ГОСТ.
    if ('Наименование документа product' in data or
            "Обозначение стандарта, нормативного документа product" in data):

        # Берем непосредственно текст, в котором может быть номер ГОСТ.
        if ('Наименование документа product' in data and
                "Обозначение стандарта, нормативного документа product" in data):
            text = (data['Наименование документа product'] +
                    data["Обозначение стандарта, нормативного документа product"])
        elif 'Наименование документа product' in data:
            text = data['Наименование документа product']
        elif "Обозначение стандарта, нормативного документа product" in data:
            text = data["Обозначение стандарта, нормативного документа product"]

        # Ищем подстроку, совпадающую с паттерном ГОСТ.
        pattern = r"\b\d{5}-\d{2,4}\b"
        result = re.findall(pattern, text)

        # Если в тексте ГОСТ есть.
        if result:
            gost_number = result[0]
            # Открыть сайт проверки ГОСТ.
            browser.get('https://etr-torgi.ru/calc/check_gost/')

            # Ввести номер ГОСТ
            needed_element = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="poisk-form"]/input')))
            needed_element.click()
            needed_element.send_keys('ГОСТ ' + gost_number)

            # Нажать найти
            button_search = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="gost_filter"]')))
            button_search.click()

            # Сохранить статус ГОСТа на сайте.
            element = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="data-box"]/div/div/div/p/b')))
            text = element.text
            data['Статус НД'] = text  # Сохранить значение с сайта ГОСТ
            return data

    data['Статус НД'] = '-'
    return data


##################################################################################
# Небольшие вспомогательные функции.
##################################################################################
def check_number_declaration(number: str) -> tuple | None:
    """Проверить номер декларации из xlsx файла на соответствие паттерну ФСА."""
    pattern_declaration1 = r'(ЕАЭС N RU Д-[\w\.]+)'
    pattern_declaration2 = r'(РОСС RU Д-[\w\.]+)'
    pattern_certificate = r'(ЕАЭС RU С-[\w\.]+)'

    if re.match(pattern_declaration1, number) or re.match(pattern_declaration2, number):
        return number, 'declaration'

    if re.match(pattern_certificate, number):
        return number, 'certificate'

    else:
        return None, None


def make_series_for_result(fsa_data: dict) -> pd.Series:
    """Создать Series для добавления в лист мониторинга."""
    series = pd.Series([
        fsa_data['Сокращенное наименование юридического лица applicant']
        if 'Сокращенное наименование юридического лица applicant' in fsa_data else '-',
        fsa_data['Дата проверки'],
        fsa_data['Наличие ДОС'],
        fsa_data['Соответствие с сайтом'],
        fsa_data['Статус на сайте'],
        fsa_data['Соответствие адресов с ЕГРЮЛ'],
        fsa_data['Адрес места нахождения applicant']

        if 'Адрес места нахождения applicant' in fsa_data else '-',
        fsa_data['Адрес места нахождения applicant ЕГРЮЛ']
        if 'Адрес места нахождения applicant ЕГРЮЛ' in fsa_data else '-',
        fsa_data['Адрес места нахождения manufacturer']
        if 'Адрес места нахождения manufacturer' in fsa_data else '-',
        fsa_data['Адрес места нахождения manufacturer ЕГРЮЛ']
        if 'Адрес места нахождения manufacturer ЕГРЮЛ' in fsa_data else '-',
        fsa_data['Статус НД'],
        fsa_data['ФИО']],

        index=['Поставщик', 'Дата проверки', 'Наличие ДОС',
               'Соответствие с сайтом', 'Статус на сайте',
               'Соответствие адресов с ЕГРЮЛ', 'Адрес заявителя',
               'Адрес заявителя ЕГРЮЛ', 'Адрес изготовителя',
               'Адрес изготовителя ЕГРЮЛ', 'Статус НД', 'ФИО'])

    return series


##################################################################################
# Главная функция для работы с сайтами через браузер.
##################################################################################
def launch_checking_fsa(file_after_gold: str, file_result: str, sheet: str):
    """Основная функция - работа с данными на сайте Росаккредитации,
    последующее их преобразование и работы с ними в DataFrame."""

    # Просмотренные номера деклараций. Берем из файла.
    viewed_numbers = read_viewed_numbers_of_documents(VIEWED_IN_FSA_NUMBERS)

    # Создаем экземпляр для работы с браузером и 4 вкладки в нем.
    browser_handler = BrowserHandler(browser, wait)  # Класс - для работы с браузером.
    declaration_fsa_window = browser_handler.make_new_tab(URL_FSA_DECLARATION)
    certificate_fsa_window = browser_handler.make_new_tab(URL_FSA_CERTIFICATE)  # Сертификаты.
    egrul_window = browser_handler.make_new_tab(URL_EGRUL)  # ЕГРЮЛ
    gost_window = browser_handler.make_new_tab(URL_GOST)  # ГОСТ

    gold_df = pd.read_excel(file_after_gold)  # Данные из xlsx после ГОЛД

    # Новый DataFrame, в котором будут итоговые данные.
    new_df = pd.DataFrame(columns=[
        '1', 'Код товара', 'Наименование товара', 'ДОС', 'Поставщик',
        'Изготовитель', 'Дата проверки', 'Наличие ДОС', 'Соответствие с сайтом',
        'Статус на сайте', 'Соответствие адресов с ЕГРЮЛ', 'Адрес заявителя',
        'Адрес заявителя ЕГРЮЛ', 'Адрес изготовителя', 'Адрес изготовителя ЕГРЮЛ',
        'Статус НД', 'ФИО', 'Примечание']
    )

    count = 0  # Для подсчета количества операций за цикл.

    try:
        # Перебираем документы.
        for _, row in gold_df.iterrows():
            number_document = row['ДОС']  # Номер документа из старого DataFrame

            # Пропустить итерацию если ранее документ просматривали.
            if number_document in viewed_numbers:
                continue

            # Прогоняем через паттерны, определяем тип документа.
            number_document, type_of_doc = check_number_declaration(number_document)

            # Пропустить итерацию если номер документа не соответствует паттерну номера.
            if number_document is None:
                continue

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
                browser.switch_to.window(egrul_window)
                fsa_data = get_addresses_from_egrul(fsa_data, browser, wait)  # ЕГРЮЛ.
                fsa_data = check_gost(fsa_data, browser, wait)  # ГОСТ.

            else:
                fsa_data = {}
                fsa_data['Наличие ДОС'] = 'Не найдено на ФСА'
                fsa_data['Соответствие с сайтом'] = 'Не найдено на ФСА'
                fsa_data['Статус на сайте'] = 'Не найдено на ФСА'
                fsa_data['Соответствие адресов с ЕГРЮЛ'] = '-'
                fsa_data['Адрес места нахождения applicant'] = '-'
                fsa_data['Статус НД'] = '-'

            fsa_data['ФИО'] = 'Код'
            fsa_data['Дата проверки'] = datetime.now().strftime('%d.%m.%Y-%H.%M.%S')

            # Формируем Series с собранными данными.
            new_series = make_series_for_result(fsa_data)

            # Объединяем со старым Series в один и добавляем в новый DataFrame.
            new_row = row._append(new_series)
            new_df = new_df._append(new_row, ignore_index=True)

            viewed_numbers.add(number_document)
            count += 1
            print(fsa_data)

    except:
        screenshot = pyautogui.screenshot()
        screenshot.save(r".\screenshots\errors\fsa_errors\error_{}.png".format(
            number_document.replace('/', '_')))
        print('Произошла ошибка.\n', 'Количество обработанных в ГОЛД', count)
        raise Exception

    finally:
        # Прочитать из xlsx уже проверенные данные, объединить с полученными,
        # записать DataFrame в файл результат.
        old_df = pd.read_excel(file_result, sheet_name=sheet)
        total_df = pd.concat([old_df, new_df])
        with pd.ExcelWriter(file_result, if_sheet_exists='overlay', engine="openpyxl", mode='a') as writer:
            total_df.to_excel(writer, sheet_name=sheet, index=False, columns=[
                'Код товара', 'Наименование товара', 'ДОС', 'Поставщик',
                'Изготовитель', 'Дата проверки', 'Наличие ДОС', 'Соответствие с сайтом',
                'Статус на сайте', 'Соответствие адресов с ЕГРЮЛ',
                'Адрес заявителя', 'Адрес заявителя ЕГРЮЛ', 'Адрес изготовителя',
                'Адрес изготовителя ЕГРЮЛ', 'Статус НД', 'ФИО'])

        # А просмотренные коды товаров в текстовый файл.
        write_viewed_numbers_to_file(VIEWED_IN_FSA_NUMBERS, viewed_numbers)


class BrowserHandler:
    """Класс взаимодействия с браузером."""
    def __init__(self, browser, wait):
        """Инициация объекта. Принимает browser, wait"""
        self.browser = browser
        self.wait = wait
        self.chapter_xpath = X_PATHS['chapter']

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
            (By.XPATH, X_PATHS['input_field'])))
        input_number_document.clear()
        input_number_document.send_keys(document_number)
        button_search = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, X_PATHS['search_button'])))
        button_search.click()

    def pick_needed_document_in_list(self, document_number: str):
        """Обновить браузер, дождаться список документов,
        кликнуть по нужному документу в списке."""
        try:
            document_number = document_number.strip()
            needed_document_element = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, X_PATHS['pick_document'])))  # Элемент для клика.

            while needed_document_element.text.strip() != document_number:
                needed_document_element = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, X_PATHS['pick_document'])))
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
            'Обозначение стандарта, нормативного документа'
        }

        # Создаем словарь для результатов работы, записываем первое значение.
        data = {'Статус на сайте': self.wait.until(EC.presence_of_element_located(
            (By.XPATH, X_PATHS['doc_status_on_fsa']))).text}

        # Определяем номер последней главы - количество итераций для сбора данных.
        elements = self.wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, X_PATHS['last_iter'])))
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

            # "info-row__header" - ключи для словаря; "info-row__text" - значения.
            headers = self.browser.find_elements(By.CLASS_NAME, "info-row__header")
            texts = self.browser.find_elements(By.CLASS_NAME, "info-row__text")

            # Преобразуем данные в словарь.
            for header, text in zip(headers, texts):
                key = header.text.strip()
                # Берем только те ключи и значения, который в списке необходимых колонок.
                if key in needed_columns:
                    value = text.text.strip()
                    # Если ключ уже есть в словаре, то добавляем к ключу строку - название подраздела.
                    data[key + ' ' + chapter] = value
                continue

            # Для сертификатов изъятие данных отличается. Собираются внутренние элементы.
            if chapter in {'applicant', 'manufacturer'} and type_of_doc == 'certificate':
                inner_data = self.get_inner_elements(chapter)
                data.update(inner_data)

        # Возвращение на страницу для ввода номера документа.

        if type_of_doc == 'declaration':
            self.return_to_input_document_number(X_PATHS['return_declaration'])
        else:
            self.return_to_input_document_number(X_PATHS['return_certificate'])

        if data:
            data['Наличие ДОС'] = 'Да'
            data['Соответствие с сайтом'] = 'Соответствует'

        else:
            data['Наличие ДОС'] = '-'
            data['Соответствие с сайтом'] = '-'

        return data


# Ввод переменных от пользователя.
# path_to_checking_file = get_path_for_existing_file(MESSAGE_FOR_USER_VERIFIABLE_FILE)
# path_to_results_file = get_path_for_existing_file(MESSAGE_FOR_USER_RESULT_FILE)
# month = get_string_from_user(MESSAGE_FOR_USER_INPUT_SHEET_NAME)

# Создать лист в excel файл.
# create_sheet_write_codes_and_names(path_to_checking_file, path_to_results_file, month)

# data_of_checking(path_to_results_file, month)
launch_checking_fsa(r'C:\Users\RIMinullin\PycharmProjects\someProject\monitoring\temp_df.xlsx',
                    r'C:\Users\RIMinullin\PycharmProjects\someProject\monitoring\Мониторинг АМ (2023).xlsx',
                    'декабрь')
