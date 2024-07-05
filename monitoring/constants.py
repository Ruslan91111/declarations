"""
Константы и структуры данных с постоянными значениями.
"""
import os
from datetime import datetime
from enum import Enum
import time
import random

from functions_for_work_with_files_and_dirs import return_or_create_dir


# Пути к файлам.
PATH_TO_DRIVER = r'..\chromedriver.exe'
PATH_TO_TESSERACT = r'C:\Users\impersonal\AppData\Local\Programs\Tesseract-OCR\tesseract'

# Связанные с датой.
MONTH_AND_YEAR = datetime.now().strftime('%B_%Y')
DATE_TODAY = datetime.now().strftime('%Y-%m-%d')

# Процессы.
FIREFOX_PROC = "firefox.exe"
JAVA_PROC = "java.exe"

USERNAME = os.getenv('USERNAME')
# Директории.
PATH_TO_DESKTOP = f"c:\\Users\\{USERNAME}\\Desktop\\"

# Папка, в которой будут храниться файлы, связанные с текущей ежемесячной проверкой.
DIR_CURRENT_MONTHLY_MONITORING = return_or_create_dir(
    r'./monitoring_for_%s' % MONTH_AND_YEAR)

RANDOM_SLEEP = time.sleep(random.randint(1, 3))


##########################################################################
# Классы Enum.
##########################################################################
class Files(Enum):
    """ Пути к используемым в коде файлам"""
    LAST_VIEWED_IN_WEB_NUMBER = r'.\%s\viewed_in_web_numbers_%s.txt' % (
        DIR_CURRENT_MONTHLY_MONITORING, MONTH_AND_YEAR)
    LAST_VIEWED_FOR_INTERNATIONAL = r'.\%s\viewed_for_international_%s.txt' % (
        DIR_CURRENT_MONTHLY_MONITORING, MONTH_AND_YEAR)
    RESULT_FILE = r'.\%s\result_data_after_web_%s.xlsx' % (
        DIR_CURRENT_MONTHLY_MONITORING, MONTH_AND_YEAR)
    LAST_VIEWED_IN_GOLD_NUMBER = r'.\%s\viewed_products_in_gold_%s.txt' % (
        DIR_CURRENT_MONTHLY_MONITORING, MONTH_AND_YEAR)
    BEFORE_GOLD = r'.\%s\before_check_in_gold_%s.xlsx' % (
        DIR_CURRENT_MONTHLY_MONITORING, MONTH_AND_YEAR)
    GOLD = r'.\%s\gold_data_%s.xlsx' % (DIR_CURRENT_MONTHLY_MONITORING, MONTH_AND_YEAR)
    APPLICANTS_CODES_AND_NAME_FROM_GOLD = r'dict_applicant.json'


class Urls(Enum):
    """ Url адреса"""
    FSA_DECLARATION: str = "https://pub.fsa.gov.ru/rds/declaration"
    FSA_CERTIFICATE: str = "https://pub.fsa.gov.ru/rss/certificate"
    EGRUL: str = "https://egrul.nalog.ru/"
    RUSPROFILE: str = "https://www.rusprofile.ru/"
    GOST: str = "https://etr-torgi.ru/calc/check_gost/"
    NSI: str = f'https://nsi.eaeunion.org/portal/1995?date={DATE_TODAY}'
    INTERNATIONAL_DOCS: str = \
        r'https://tech.eaeunion.org/registers/35-1/ru/registryList/conformityDocs'


class FsaXPaths(Enum):
    """XPATH для сайта Росакредитации(ФСА)"""
    CHAPTER: str = '//fgis-links-list/div/ul/li'
    INPUT_FIELD: str =  "//fgis-text/input"
    SEARCH_BUTTON: str = "//button[contains(text(), 'Найти')]"
    ROW_DOCUMENT_ON_SITE: str = "/*//tbody/tr[{row}]/td[{column}]"
    RETURN_BACK_DECLARATION: str = "//fgis-rds-view-declaration-toolbar/div/div[1]"
    RETURN_BACK_CERTIFICATION: str = "//fgis-rss-view-certificate-toolbar/div/div[1]"
    DOCUMENT_STATUS: str = '//fgis-toolbar-status/span'
    DOCUMENT_STATUS_IN_MENU: str = "/*//tbody/tr[2]/td[2]"
    CHAPTER_FOR_LAST_ITERATION: str = '//fgis-links-list/div/ul/li'
    ERROR_403: str = "//*[contains(text(), '403 Forbidden')]"
    SERVICE_NOT_AVAILABLE: str = "//*[contains(text(), 'Сервис временно недоступен')]"
    SERVICE_NOT_AVAILABLE_OK_BUTTON: str = "//*[contains(text(), 'OK')]"
    NO_RECORDS_MATCHING_THE_SEARCH: str = ("//*[contains(text(), "
                                           "'Нет записей, удовлетворяющих поиску')]")
    NOT_VALID_DECLARATION: str = "/*//tbody/tr[2]/td[2]//*[@alt]"
    PLACE_FOR_STATUS_ON_IMAGE: str = "/*//tbody/tr[{row}]/td[{column}]//*[@alt]"
    COUNT_OF_PAGE: str = r'/*//tbody//tr//*[@alt]'

class NSIXPaths(Enum):
    """XPATH для сайта проверки СГР"""
    FILTER: str = '//div[3]//th[2]//button//span'
    INPUT_FIELD: str = '/html/body/div[3]/div[1]/div/input'
    CHECK_MARK: str = '/html/body/div[3]/div[2]/button[2]/span[1]'
    STATUS_DOCUMENT: str = '//tbody/tr/td[3]/div/div/a/div/span'
    NO_DATA: str = '//tbody/tr/td'
    APPLICANT: str = '//tbody/tr/td[8]/div/div/span'
    MANUFACTURER: str = '//tbody/tr/td[7]/div/div/span'
    NORMATIVE_DOCUMENTS: str = '//tbody/tr/td[9]/div/div/span'


class RusProfileXPaths(Enum):
    """XPATH для сайта rusprofile - проверка адресов юр.лиц"""
    INPUT_FIELD: str = "(//input[contains(@placeholder, 'Искать по названию, адресу')])[last()]"
    SEARCH_BUTTON: str = "(//button[@type='submit'])[last()]"
    ADDRESS_PLACE: str = '//address[@class]'
    CAPTCHA_SECTION: str = "//*[contains(@class, 'captcha-section')]"
    CAPTCHA_CHECKBOX: str = "//*[contains(@class,'recaptcha-checkbox-border')]"

    NO_ORGANISATION_FOUND: str = ("//h1[contains(text(), 'По запросу') "
                                  "and contains(., 'найдены 0 организаций "
                                  "и 0 индивидуальных предпринимателей')]")


class GostXPaths(Enum):
    """XPATH для сайта etr-torgi - проверка ГОСТ"""
    INPUT_FIELD: str = '//*[@id="poisk-form"]/input'
    SEARCH_BUTTON: str = '//*[@id="gost_filter"]'
    GOST_STATUS: str = '//*[@id="data-box"]//b'


class ScreenShotsForWorkWithGold(Enum):
    """ Пути к скриншотам для работы с программой GOLD. """
    # Связанные с меню
    FIREFOX_ICON: str = r'.\screenshots\appicon3.png'
    FIREFOX_ICON_PANEL: str = r'.\screenshots\firefox_icon_panel.png'
    MENU_IN_GOLD: str = r'.\screenshots\menu_icon.png'
    GOLD_LOADED: str = r'.\screenshots\gold_loaded.png'
    BACK_ICON_GOLD: str = r'.\screenshots\back_icon_gold.png'
    STOCK_11: str = r'.\screenshots\gold_11.png'
    LOGIN_PLACE: str = r'.\screenshots\login_place.png'
    PASSWORD_PLACE: str = r'.\screenshots\password_place.png'
    ENTER_LOGIN: str= r'.\screenshots\enter.png'
    MENU_33 = r'.\screenshots\menu_33.png'
    MENU_33_4 = r'.\screenshots\33-4.png'
    TO_SEAL_OVERDUE = r'.\screenshots\seal_overdue.png'
    # Связанные с вводом и работой карточек товаров
    PRODUCT_INPUT_FIELD = r'.\screenshots\product_input_number.png'
    DECLARATION_CARD = r'.\screenshots\declaration_card.png'
    # Скриншоты для выбора действующих деклараций.
    GREEN_STATUS_DECLARATION = r'.\screenshots\the_declarations_status\valid_declaration_green.png'
    GRAY_STATUS_DECLARATION = r'.\screenshots\the_declarations_status\valid_declaration_transp.png'
    # Скриншот загрузки данных
    LOADING_PRODUCT = r'.\screenshots\loading_product.png'
    # Серое сообщение "Данные не найдены".
    MESSAGE_DATA_NOT_FOUND = r'.\screenshots\data_not_found.png'
    FOR_CLICK_OK_ON_DATA_NOT_FOUND = r'.\screenshots\ok_data_not_found.png'
    # Сообщение о крахе Java".
    CRASH_JAVA = r'.\screenshots\crash_java.png'


class FieldsInProductCardGold(Enum):
    """ Пути к скриншотам в карточке товара """
    REG_NUMBER_FIELD = r'.\screenshots\reg_numb.png'
    APPLICANT_CODE = r'.\screenshots\applicant_code.png'
    MANUFACTURER_FIELD = r'.\screenshots\manufacturer_field.png'
    DATE_OF_END = r'.\screenshots\date_of_end.png'


class IndicatorsForInternationalDocs(Enum):
    """ Xpaths для работы с сайтом проверки международных документов."""
    EXTENDED_COUNTRY_FIELD: str = '//ng-component//p-multiselect/div/p-overlay/div/div/div/div[1]'
    CLICK_TO_PICK_THE_COUNTRY: str = "//*[contains(text(), 'Страна')]"
    COUNTRY_INPUT_FIELD: str = "//p-multiselect/div/p-overlay//div[1]/div[2]/input"
    FOR_PICK_REQUIRED_COUNTRY: str = "//*[contains(text(), '{0}')]"
    EARLY_PICKED_COUNTRY: str = ('//ng-component//div/form/div[2]/div/div[1]/div/div[2]'
                                 '/p-multiselect/div/div[2]/div')
    SHOW_FILTERS: str = "//*[contains(text(), 'Показать фильтры')]"
    HIDE_FILTERS: str = "//*[contains(text(), 'Скрыть фильтры')]"
    NO_DATA_ABOUT_DOC: str = "//*[contains(text(), 'Нет данных')]"
    REG_NUMBER_FIELD: str = "//*[contains(text(),'Регистрационный номер документа')]"
    REG_NUMBER_INPUT_FIELD: str = "//ng-component//div/form/div[3]/div/div/div[1]/div[2]/input"
    BUTTON_APPLY_FILTERS: str = "//*[contains(text(),'Применить')]"
    DOC_LOADED_ON_PAGE: str = f"//*[contains(text(), '{0}')]"
    STATUS_OF_DOC_ON_PAGE: str = f"//*[contains(text(),'{0}')]/../..//td[last()]"
    LOADING_PROCESS: str = '//p-progressspinner'

##########################################################################
# Структуры данных с постоянными значениями
##########################################################################
# Подстроки, которые необходимо удалить из адресов перед их сравнением.
PARTS_TO_BE_REMOVED_FROM_ADDRESS = (
    ' Б ', 'БУЛЬВАР', 'Б-Р',
    ' В ', ' ВН ',
    'ГОРОД ', ' Г ',
    ' Д ', 'ДОМ ',
    ' З ', ' ЗД ',
    'ИМЕНИ ', ' ИМ ',
    'КАБИНЕТ', ' К ', ' КАБ ',
    ' КОМ ', 'КОМНАТА ',
    ' КОРП ', 'КОРПУС ',
    ' М ', 'М Р-Н', 'МИКРОРАЙОН', ' МКР ',
    ' НАБ ', 'НАБЕРЕЖНАЯ ',
    ' ОБЛ ', 'ОБЛАСТЬ',
    ' О ', ' ОФ ', 'ОФИС ',
    ' П ',
    ' ПЕР ', 'ПЕРЕУЛОК',
    ' ПОМ ', 'ПОМЕЩ ', 'ПОМЕЩЕНИЕ',
    'ПОСЕЛОК ГОРОДСКОГО ТИПА', 'ПОС ', 'ПГТ ',
    ' ПР-Д ', 'ПРОЕЗД ',
    ' РП ', 'РАБОЧИЙ ПОСЕЛОК',
    'РАЙОН', ' Р-Н ',
    'РЕСПУБЛИКА', ' РЕСП ',
    'РОССИЯ', 'РОССИЙСКАЯ ФЕДЕРАЦИЯ',
    ' С ', ' СЕЛО ',
    'СТ-ЦА', 'СТАНИЦА',
    ' СТР ', 'СТРОЕНИЕ ',
    ' Т ', ' ТЕР ', 'ТЕРРИТОРИЯ',
    ' ТУП ', 'ТУПИК',
    ' УЛ ', 'УЛИЦА ',
    ' УЧ ',
    ' Ч ', 'ЧАСТЬ',
    'ШОССЕ ', ' Ш ',
    ' ЭТ ', 'ЭТАЖ ',
)

COLUMNS_FOR_GOLD_DF = [
    'Порядковый номер АМ',
    'Код товара',
    'Наименование товара',
    'ДОС',
    'Дата окончания',
    'Изготовитель',
    'Заявитель'
]

# Словарь с прочерками.
BLANK_DICT_FOR_FILLING = {
    'Соответствие адресов с ЕГРЮЛ': '-',
    'Адрес места нахождения applicant': '-',
    'Статус НД': '-'
}

# Названия колонок для Series, формируемого в результате парсинга веб-сайтов.
TITLE_FOR_SERIES_TO_FINAL_DF = (
    'Сокращенное наименование юридического лица applicant',
    'Дата проверки',
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
)

# Нужные ключи для сбора с ФСА
REQUIRED_KEYS_TO_GET_FROM_FSA = {
    'Основной государственный регистрационный номер юридического лица (ОГРН)',
    'Адрес места нахождения',
    'Наименование документа',
    'Обозначение стандарта, нормативного документа'
}

# Названия колонок для финального DataFrames, формируемого и записываемого в result_data.
COLUMNS_FOR_RESULT_DF = [
    'Порядковый номер АМ',
    'Код товара',
    'Наименование товара',
    'ДОС',
    'Дата окончания',
    'Изготовитель',
    'Заявитель',
    'Поставщик из интернет-ресурса',
    'Дата проверки',
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

PATTERNS_FOR_NSI = {'name': r'^.*?\"(.*?)\"',
            'post_index': r'\d{6}',
            'address_in_brackets': r'\[_ЮРАДРЕС_:_([^_]+)_\]',
            'ogrn': r'\d{13}'}

PATTERN_GOST = r"ГОСТ\s\b\d{4,5}-\d{2,4}\b"

MESSAGE_FOR_USER_TO_INPUT_FILE = (
    'Убедитесь, что файл Excel, нуждающийся в проверке, находится на рабочем столе.\n'
    'Введите название файла, без пути и расширения, после чего нажмите <Enter>.\n'
    'Надежнее всего скопировать наименование файла в свойствах файла\n'
    'или скопировать наименование файла при переименовании\n>>>')


class EgrulXPaths(Enum):
    """XPATH для сайта rusprofile - проверка адресов юр.лиц"""
    INPUT_FIELD: str = "//input[contains(@placeholder, 'Укажите ИНН')]"
    SEARCH_BUTTON: str = "//button[contains(text(), 'Найти')]"
    GET_RECORD: str = "//button[contains(text(), 'Получить выписку')]"


PATH_TO_DOWNLOAD_DIR = r'C:\Users\impersonal\Downloads'
