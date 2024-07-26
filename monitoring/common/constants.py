"""
Константы и структуры данных с постоянными значениями.
"""
import os
from datetime import datetime
from enum import Enum

from common.work_with_files_and_dirs import return_or_create_dir
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
USERNAME = os.getenv('USERNAME')

# Пути к файлам.
PATH_TO_DRIVER = BASE_DIR.parent / 'chromedriver.exe'
PATH_TO_TESSERACT = f'C:\\Users\\{USERNAME}\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract'

# Связанные с датой.
MONTH_AND_YEAR = datetime.now().strftime('%B_%Y')
DATE_TODAY = datetime.now().strftime('%Y-%m-%d')

# Процессы.
FIREFOX_PROC = "firefox.exe"
JAVA_PROC = "java.exe"

# Директории.
PATH_TO_DESKTOP = f"c:\\Users\\{USERNAME}\\Desktop\\"

# Папка, в которой будут храниться файлы, связанные с текущей ежемесячной проверкой.
DIR_CURRENT_MONTH = return_or_create_dir(BASE_DIR.parent / f'files_{MONTH_AND_YEAR}')
SCR_DIR = BASE_DIR / 'gold' / 'screenshots'  # SCREENSHOTS_DIR
DIR_COPIES = return_or_create_dir(DIR_CURRENT_MONTH / 'copies_of_files')
COPIES_WEB = return_or_create_dir(DIR_COPIES / 'copies_of_web')
COPIES_GOLD = return_or_create_dir(DIR_COPIES / 'copies_of_gold')


##########################################################################
# Классы Enum.
##########################################################################
class Files(Enum):
    """ Пути к используемым в коде файлам"""
    LAST_VIEWED_IN_WEB_NUMB = DIR_CURRENT_MONTH / f'viewed_in_web_numbers_{MONTH_AND_YEAR}.txt'
    LAST_VIEWED_FOR_INTERN = DIR_CURRENT_MONTH / f'viewed_for_international_{MONTH_AND_YEAR}.txt'
    RESULT_FILE = DIR_CURRENT_MONTH / f'result_data_after_web_{MONTH_AND_YEAR}.xlsx'
    LAST_VIEWED_IN_GOLD_NUMB = DIR_CURRENT_MONTH / f'viewed_products_in_gold_{MONTH_AND_YEAR}.txt'
    BEFORE_GOLD = DIR_CURRENT_MONTH / f'before_check_in_gold_{MONTH_AND_YEAR}.xlsx'
    GOLD = DIR_CURRENT_MONTH / f'gold_data_{MONTH_AND_YEAR}.xlsx'
    APPLICANTS_CODES_AND_NAME = BASE_DIR / 'gold' / 'dict_applicant.json'
    INTERN_DOCS = DIR_CURRENT_MONTH / f'intern_docs_{MONTH_AND_YEAR}.xlsx'
    INTERN_DOCS_RESULT = DIR_CURRENT_MONTH.parent.parent / f'международные декларации_{MONTH_AND_YEAR}.xlsx'


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
    INPUT_FIELD: str = "//fgis-text/input"
    SEARCH_BUTTON: str = "//button[contains(text(), 'Найти')]"
    ROW_DOC_ON_SITE: str = "/*//tbody/tr[{row}]/td[{column}]"
    RETURN_BACK_DECL: str = "//fgis-rds-view-declaration-toolbar/div/div[1]"
    RETURN_BACK_CERT: str = "//fgis-rss-view-certificate-toolbar/div/div[1]"
    DOC_STATUS: str = '//fgis-toolbar-status/span'
    DOC_STATUS_IN_MENU: str = "/*//tbody/tr[2]/td[2]"
    LAST_CHAPTER: str = '//fgis-links-list/div/ul/li'
    ERROR_403: str = "//*[contains(text(), '403 Forbidden')]"
    SERV_NOT_AVAILABLE: str = "//*[contains(text(), 'Сервис временно недоступен')]"
    SERV_NOT_AVAILABLE_BUTTON: str = "//*[contains(text(), 'OK')]"
    NO_MATCHING_RECORDS: str = ("//*[contains(text(), "
                                "'Нет записей, удовлетворяющих поиску')]")
    NOT_VALID_DECLARATION: str = "/*//tbody/tr[2]/td[2]//*[@alt]"
    STATUS_ON_IMAGE: str = "/*//tbody/tr[{row}]/td[{column}]//*[@alt]"
    COUNT_OF_PAGE: str = r'/*//tbody//tr//*[@alt]'


class NSIXPaths(Enum):
    """XPATH для сайта проверки СГР"""
    FILTER: str = '//div[3]//th[2]//button//span'
    INPUT_FIELD: str = '/html/body/div[3]/div[1]/div/input'
    CHECK_MARK: str = '/html/body/div[3]/div[2]/button[2]/span[1]'
    STATUS_DOC: str = '//tbody/tr/td[3]/div/div/a/div/span'
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


class ScrForGold(Enum):
    """ Пути к скриншотам для работы с программой GOLD. """
    DIR_DECL_STATUS = BASE_DIR / 'gold' / 'screenshots' / 'the_declarations_status'
    # Связанные с меню
    FIREFOX_ICON: str = str(SCR_DIR / 'appicon3.png')
    FIREFOX_ICON_PANEL: str = str(SCR_DIR / 'firefox_icon_panel.png')
    MENU_IN_GOLD: str = str(SCR_DIR / 'menu_icon.png')
    GOLD_LOADED: str = str(SCR_DIR / 'gold_loaded.png')
    STOCK_11: str = str(SCR_DIR / 'gold_11.png')
    LOGIN_PLACE: str = str(SCR_DIR / 'login_place.png')
    PASSWORD_PLACE: str = str(SCR_DIR / 'password_place.png')
    ENTER_LOGIN: str = str(SCR_DIR / 'enter.png')
    MENU_33: str = str(SCR_DIR / 'menu_33.png')
    MENU_33_4: str = str(SCR_DIR / '33-4.png')
    TO_SEAL_OVERDUE: str = str(SCR_DIR / 'seal_overdue.png')

    # Связанные с вводом и работой карточек товаров
    PROD_INPUT_FIELD: str = str(SCR_DIR / 'product_input_number.png')
    DECLARATION_CARD: str = str(SCR_DIR / 'declaration_card.png')

    # Скриншоты для выбора действующих деклараций
    GREEN_STATUS_DECL: str = str(DIR_DECL_STATUS / 'valid_declaration_green.png')
    GRAY_STATUS_DECL: str = str(DIR_DECL_STATUS / 'valid_declaration_transp.png')
    GRAY_APPROACHING_DECL: str = str(DIR_DECL_STATUS / 'approaching_certification.png')

    # Скриншот загрузки данных
    LOADING_PRODUCT: str = str(SCR_DIR / 'loading_product.png')

    # Серое сообщение "Данные не найдены"
    MESSAGE_DATA_NOT_FOUND: str = str(SCR_DIR / 'data_not_found.png')
    OK_BUTTON_NOT_FOUND: str = str(SCR_DIR / 'ok_data_not_found.png')

    # Сообщение о крахе Java
    CRASH_JAVA: str = str(SCR_DIR / 'crash_java.png')
    SAVE_MODE: str = str(SCR_DIR / 'launch_in_save_mode.png')
    APPLICANT_CODE: str = str(SCR_DIR / 'applicant_code.png')


class ProductCardFields(Enum):
    """ Пути к скриншотам в карточке товара """
    REG_NUMBER_FIELD = str(SCR_DIR / 'reg_numb.png')
    APPLICANT_CODE = str(SCR_DIR / 'applicant_code.png')
    MANUF_FIELD = str(SCR_DIR / 'manufacturer_field.png')
    DATE_OF_END = str(SCR_DIR / 'date_of_end.png')


class IndicatorsForInternDocs(Enum):
    """ Xpaths для работы с сайтом проверки международных документов."""
    EXTENDED_COUNTRY_FIELD: str = '//ng-component//p-multiselect/div/p-overlay/div/div/div/div[1]'
    CLICK_TO_PICK_THE_COUNTRY: str = "//*[contains(text(), 'Страна')]"
    COUNTRY_INPUT_FIELD: str = "//p-multiselect/div/p-overlay//div[1]/div[2]/input"
    FOR_PICK_REQUIRED_COUNTRY: str = "//*[contains(text(), '{0}')]"
    PREVIOUS_COUNTRY: str = ('//ng-component//div/form/div[2]/div/div[1]/div/div[2]'
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
    NOT_AVAILABLE_SERV: str = "//*[contains(text(), 'Сервис временно недоступен')]"
    CLOSE_NOT_AVAIL_ERR: str = "//*[contains(text(), 'Закрыть')]"


##########################################################################
# Структуры данных с постоянными значениями
##########################################################################
# Подстроки, которые необходимо удалить из адресов перед их сравнением.
REMOVE_ADDRESS_PARTS = (
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

COLS_FOR_GOLD_DF = [
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
REQUIRED_DATA_KEYS_FSA = {
    'Основной государственный регистрационный номер юридического лица (ОГРН)',
    'Адрес места нахождения',
    'Наименование документа',
    'Обозначение стандарта, нормативного документа'
}

# Названия колонок для финального DataFrames, формируемого и записываемого в result_data.
COLS_FOR_RESULT_DF = [
    'Порядковый номер АМ',
    'Код товара',
    'Наименование товара',
    'ДОС',
    'Дата окончания',
    'Изготовитель',
    'Заявитель',
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

NSI_PATTERNS = {'name': r'^.*?\"(.*?)\"',
                'post_index': r'\d{6}',
                'address_in_brackets': r'\[_ЮРАДРЕС_:_([^_]+)_\]',
                'ogrn': r'\d{13}'}

PATTERN_GOST = r"ГОСТ\s\b\d{4,5}-\d{2,4}\b"

MESSAGE_TO_INPUT_FILE = (
    'Убедитесь, что файл Excel, нуждающийся в проверке, находится на рабочем столе.\n'
    'Введите название файла, без пути и расширения, после чего нажмите <Enter>.\n'
    'Надежнее всего скопировать наименование файла в свойствах файла\n'
    'или скопировать наименование файла при переименовании\n>>>')


class EgrulXPaths(Enum):
    """XPATH для сайта rusprofile - проверка адресов юр.лиц"""
    INPUT_FIELD: str = "//input[contains(@placeholder, 'Укажите ИНН')]"
    SEARCH_BUTTON: str = "//button[contains(text(), 'Найти')]"
    GET_RECORD: str = "//button[contains(text(), 'Получить выписку')]"


PATH_TO_DOWNLOAD_DIR = f'C:\\Users\\{USERNAME}\\Downloads'
