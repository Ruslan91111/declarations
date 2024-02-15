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

from selenium_through.supporting_functions import write_viewed_numbers_to_file, read_viewed_numbers_of_documents

URL_FSA_DECLARATION = "https://pub.fsa.gov.ru/rds/declaration"
PATH_TO_DRIVER = (r'C:\Users\RIMinullin\PycharmProjects'
                  r'\someProject\selenium_through\chromedriver.exe')

VIEWED_IN_FSA_NUMBERS = r'.\viewed_in_fsa_numbers.txt'

PARTS_TO_BE_REMOVED = [
    'БУЛЬВАР', 'Б-Р',
    ' ОБЛ ', 'ОБЛАСТЬ',
    'РАЙОН', ' Р-Н ',
    ' П ', ' ПОМ ', 'ПОМЕЩ ', 'ПОМЕЩЕНИЕ',
    ' КАБ ', 'КАБИНЕТ',
    'ГОРОД ', ' Г ',
    ' Д ', 'ДОМ ',
    ' НАБ ', 'НАБЕРЕЖНАЯ ',
    'ШОССЕ ', ' Ш ',
    ' ВН ', ' ТЕР ',
    ' СТР ', 'СТРОЕНИЕ ',
    ' ЭТ ', 'ЭТАЖ ',
    ' КОМ ',
    ' ОФ ', 'ОФИС ',
    'М Р-Н', 'МИКРОРАЙОН', ' МКР ',
    ' УЛ ', 'УЛИЦА ',
    ' ПР-Д ', 'ПРОЕЗД ',
    'РОССИЯ'
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
    browser.get('https://egrul.nalog.ru/index.html')

    #  Выполнить алгоритм два раза для заявителя и изготовителя.
    applicant_and_manufacturer = ('applicant', 'manufacturer')
    for i in applicant_and_manufacturer:
        needed_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="query"]')))
        needed_element.click()

        # Проверяем есть ли ОГРН у юр.лица, по которому можно проверить адрес на сайте ЕГРЮЛ.
        if f'Основной государственный регистрационный номер юридического лица (ОГРН) {i}' in data_web.keys():
            # Ввести ОГРН
            needed_element.send_keys(
                data_web[f'Основной государственный регистрационный номер юридического лица (ОГРН) {i}'])

            # Нажать найти
            button_search = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btnSearch"]')))
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


def check_number_declaration(number: str) -> str | None:
    """Проверить номер декларации из xlsx файла на соответствие паттерну ФСА."""
    pattern1 = r'(ЕАЭС N RU Д-[\w\.]+)'
    pattern2 = r'(РОСС RU Д-[\w\.]+)'
    if re.match(pattern1, number) or re.match(pattern2, number):
        return number
    else:
        return None



def launch_checking_fsa(file_after_gold: str, file_result: str, sheet: str):
    """Основная функция - работа с данными на сайте Росаккредитации,
    последующее их преобразование и работы с ними в DataFrame."""

    # Просмотренные номера деклараций. Берем из файла.
    set_of_viewed_numbers = read_viewed_numbers_of_documents(VIEWED_IN_FSA_NUMBERS)

    # Класс - собиратель данных с ФСА
    scrapper = FsaDataScrapper(browser, wait, URL_FSA_DECLARATION)
    scrapper.open_page()  # Открыть сайт ФСА
    fsa_window = browser.current_window_handle  # Окно ФСА
    browser.switch_to.new_window('tab')
    second_window = browser.current_window_handle  # Второе окно для работы с ЕГРЮЛ и ГОСТ
    browser.switch_to.window(fsa_window)

    gold_df = pd.read_excel(file_after_gold)  # Данные из xlsx после ГОЛД

    # Новый DataFrame, в котором будут итоговые данные.
    new_df = pd.DataFrame(columns=[
        '1', 'Код товара', 'Наименование товара', 'ДОС', 'Поставщик',
        'Изготовитель', 'Дата проверки', 'Наличие ДОС', 'Соответствие с сайтом',
        'Статус на сайте', 'Соответствие адресов с ЕГРЮЛ', 'Адрес заявителя',
        'Адрес заявителя ЕГРЮЛ', 'Адрес изготовителя', 'Адрес изготовителя ЕГРЮЛ',
        'Статус НД', 'ФИО', 'Примечание']
    )

    count = 0  # Для подсчета количества операций.

    try:
        # Перебираем декларации
        for _, row in gold_df.iterrows():
            # Номер декларации из старого DataFrame
            number_declaration = row['ДОС']

            # Пропустить итерацию если ранее декларацию просматривали.
            if number_declaration in set_of_viewed_numbers:
                continue

            # Пропустить итерацию если номер декларации не соответствует паттерну номера с ФСА.
            number_declaration = check_number_declaration(number_declaration)
            if number_declaration is None:
                continue

            # На сайте вводим номер декларации.
            scrapper.input_document_number(number_declaration)
            # Выбираем нужный документ.
            scrapper.pick_needed_document_in_list(number_declaration)

            # Собрать словарь данных по декларации, в том числе ЕГРЮЛ, ГОСТ.
            fsa_data = scrapper.get_data_on_declaration()  # Данные по декларации с сайта
            browser.switch_to.window(second_window)
            fsa_data = get_addresses_from_egrul(fsa_data, browser, wait)  # Работа с ЕГРЮЛ.
            fsa_data = check_gost(fsa_data, browser, wait)  # Работа с ГОСТ.
            browser.switch_to.window(fsa_window)
            fsa_data['ФИО'] = 'Код'
            fsa_data['Дата проверки'] = datetime.now().strftime('%d.%m.%Y-%H.%M.%S')

            # Формируем Series с собранными данными.
            new_series = pd.Series([
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

            # Объединяем со старым Series в один и добавляем в новый DataFrame.
            new_row = row._append(new_series)
            new_df = new_df._append(new_row, ignore_index=True)
            scrapper.browser.switch_to.window(fsa_window)
            scrapper.return_to_input_number()
            set_of_viewed_numbers.add(number_declaration)
            browser.switch_to.window(fsa_window)
            count += 1
            print(fsa_data)

    except:
        screenshot = pyautogui.screenshot()
        screenshot.save(r".\screenshots\errors\fsa_errors\error_{}.png".format(
            number_declaration.replace('/', '_')))

        print('Произошла ошибка.\n', 'Количество обработанных в ГОЛД', count)
        raise Exception

    finally:
        # Прочитать из xlsx уже проверенные данные, объединить с полученными,
        # записать DataFrame проверенных данных в файл результат.
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
        write_viewed_numbers_to_file(VIEWED_IN_FSA_NUMBERS, set_of_viewed_numbers)


class FsaDataScrapper:
    """
    Класс, собирающий данные со страницы росаккредитации. Работает с определенной страницей
    как с декларацией, так и с сертификатом.

    Методы:

    open_page
    input_document_number
    return_to_input_number
    get_needed_document_in_list
    get_protocols
    get_inner_elements
    get_data_on_document_by_columns
    get_all_data
    close_browser
    """

    def __init__(self, browser, wait, url: str):
        self.browser = browser
        self.wait = wait
        self.url = url
        self.chapter_xpath = '//fgis-links-list/div/ul/li'

    def open_page(self) -> None:
        """Открыть страницу"""
        self.browser.get(self.url)

    def input_document_number(self, document_number: str):
        """Открыть страницу с полем для ввода номера документа,
        ввести номер декларации, нажать на кнопку 'найти'."""
        input_number_document = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//fgis-text/input")))
        input_number_document.clear()
        input_number_document.send_keys(document_number)
        button_search = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Найти')]")))
        button_search.click()

    def return_to_input_number(self) -> None:
        """После сохранения данных по декларации нажать на возврат
        для ввода следующего номера декларации."""
        back_to_input = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//fgis-rds-view-declaration-toolbar/div/div[1]")))
        back_to_input.click()

    def pick_needed_document_in_list(self, document_number: str) -> None:
        """Обновить браузер, дождаться список документов,
        кликнуть по нужному документу в списке."""
        document_number = document_number.strip()
        needed_document_element = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*/div[1]/div/div/div/table/tbody/tr[2]"
                       "/td[3]/a/fgis-h-table-limited-text-cell/div[1]")))

        while needed_document_element.text.strip() != document_number:
            needed_document_element = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*/div[1]/div/div/div/table/tbody/tr[2]/td[3]"
                           "/a/fgis-h-table-limited-text-cell/div[1]")))
        needed_document_element.click()

    def get_data_on_declaration(self) -> dict:
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
            (By.XPATH, '//fgis-toolbar-status/span'))).text}

        # Определяем номер последней главы - количество итераций для сбора данных.
        elements = self.wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//fgis-links-list/div/ul/li')))
        number_of_last_chapter = len(elements)  # Номер последней итерации.

        # Перебираем и кликаем по подразделам ФСА.
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

        if data:
            data['Наличие ДОС'] = 'Да'
            data['Соответствие с сайтом'] = 'Соответствует'

        else:
            data['Наличие ДОС'] = '-'
            data['Соответствие с сайтом'] = '-'

        return data

    def close_browser(self):
        """Закрыть браузер."""
        self.browser.quit()


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
