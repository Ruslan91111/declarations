"""
    class InternDocParser:
        Класс для взаимодействия с сайтом для проверки международных документов.
"""
import re
import time
from enum import Enum

from selenium.common import NoSuchElementException, TimeoutException

from common.constants import Urls, IndicatorsForInternDocs
from common.exceptions import DataLoadingError
from common.file_worker import random_delay
from web.intern_docs.helpers import determine_country_of_doc
from web.work_with_browser import create_browser_with_wait, BrowserWorker, make_browser, make_wait


class EnternlUrls(Enum):
    """ Url адреса"""
    MAIN_PAGE: str = "https://tech.eaeunion.org/tech/registers/35-1/ru"
    ARM: str = "https://armnab.am/MMCertificatesListRU"
    BY: str = "https://tsouz.belgiss.by/"
    # KZ: str = 'https://eokno.gov.kz/public-register/register-ktrm.xhtml'
    KG: str = 'http://swis.trade.kg/Registry/CertificateOfConformity'


class BelarusXPATH(Enum):
    INPUT_FIELD = r'//input[contains(@placeholder, "поиск по регистрационному номеру")]'
    SEARCH_BUTTON = r'//*[contains(text(), "Поиск")]'
    APPLY_BUTTON = r"//*[contains(text(), 'Применить')]"
    LOADING_ELEM = "//*[contains(@class, 'fa fa-refresh')]"
    SUCCESS_DOC = r"//*[contains(@class, 'box-success')]//*[contains(@class, 'box-title')][1]"
    STATUS_PLACE = r"//div[contains(@class, 'expert-tsouz-Doc-Status-Details')]"
    WRONG_DOC = r"//*[contains(@class, 'box-danger')]//*[contains(@class, 'box-title')][1]"
    NO_DOCS = r'//*[contains(@class,"tsouz-paginator-top paginator-top")]'


class MonitoringInternBrowser(BrowserWorker):
    """ Класс для работы с браузером при веб-мониторинге."""
    def __init__(self, browser, wait):
        super().__init__(browser, wait)
        self.tabs = self.make_all_required_tabs()
        time.sleep(1)

    def make_all_required_tabs(self) -> dict:
        """Создать необходимые вкладки в браузере. Вернуть словарь, где каждой стране будет
        соответствовать определенная вкладка для проверки по странам. """
        tabs = {name.name: self.make_new_tab(name.value) for name in EnternlUrls}
        return tabs

    def wait_till_page_loaded(self, xpath):
        loaded = False
        while not loaded:
            try:
                time.sleep(0.06)
                self.find_elem_by_class(xpath)
            except Exception:
                loaded = True


class InternDocParser:
    """ Класс для взаимодействия с сайтом для проверки международных документов. """
    def __init__(self):
        self.browser = create_browser_with_wait(0, MonitoringInternBrowser, 30)
        self.tabs = self.browser.make_new_tab
        self.status_doc = ""
        self.number = ''
        self.country = ''

    def choose_page(self):
        """ Определить страну декларации и переключиться на соответствующую вкладку. """
        self.country = re.search(r'(BY|KZ|ARM|KG)', self.number).group()
        self.browser.switch_to_tab(self.browser.tabs[self.country])

    def get_status_from_web(self):
        """ Проверить статус одного документа на странице сайта. """
        self.choose_page()
        if self.country == 'BY':
            self.doc_getter = BelorusDocGetter(self.browser, self.number)
            self.doc_getter.get_status()
            self.status_doc = self.doc_getter.status_doc


class BelorusDocGetter:

    def __init__(self, browser, number):
        self.browser = browser
        self.number = number
        self.number_from_page = False
        self.found_doc = False

    def input_doc_number(self):
        """ Ввести номер белорусского документа и дождаться загрузки документа."""
        self.browser.input_in_field(BelarusXPATH.INPUT_FIELD.value, self.number)
        time.sleep(0.5)
        # Кнопка поиска.
        self.browser.wait_and_click_elem(BelarusXPATH.SEARCH_BUTTON.value)
        # Кнопку применить для поиска нужного документа.
        self.browser.wait_and_click_elem(BelarusXPATH.APPLY_BUTTON.value)
        # Ждем пока страница полностью прогрузится.
        self.browser.wait_till_page_loaded(BelarusXPATH.LOADING_ELEM.value)

    def check_green_box_valid_doc(self):
        """ Проверить наличие на странице зеленого бокса с валидным документом. """
        try:
            self.number_from_page = self.browser.get_text_by_xpath(BelarusXPATH.SUCCESS_DOC.value)
            self.found_doc = True
        except (NoSuchElementException, TimeoutException):
            print('Нет документа с валидным статусом.')

    def check_red_box_invalid_doc(self):
        """ Проверить наличие на странице красного бокса с невалидным документом. """
        try:
            self.number_from_page = self.browser.get_text_by_xpath(BelarusXPATH.WRONG_DOC.value)
            self.found_doc = True
        except (NoSuchElementException, TimeoutException):
            print('Нет документа с невалидным статусом.')

    def get_status_from_page(self):
        # Если была зеленая или красная карточка документа.
        if self.found_doc:
            # Берем номер документа.
            # numb_from_page = self.browser.get_text_by_xpath(BelarusXPATH.SUCCESS_DOC.value)
            # Проверяем, что документ, загруженный на странице по номеру соответствует проверяемому.
            if not self.number_from_page == self.number:
                self.status_doc = 'Декларация на странице не обнаружена.'
            else:
                # Ищем и выдрезаем статус документа.
                doc_status_place = self.browser.wait_elem_located(BelarusXPATH.STATUS_PLACE.value)
                full_text = doc_status_place.text
                # Сохраняем статус документа.
                self.status_doc = re.search(r'\(\d{2}\)\s*\w+', full_text, re.IGNORECASE).group()

    def check_data_loading_error_and_zero_docs(self):
        """Проверить наличие на странице сообщения об ошибке при загрузке данных."""
        try:
            data_loading_error = self.browser.find_elem_by_xpath("//*[contains(@class, 'alert')]")
            if data_loading_error:
                raise DataLoadingError()
        except (NoSuchElementException, TimeoutException):
            no_doc = self.browser.get_text_by_xpath(BelarusXPATH.NO_DOCS.value)
            if 'Отображено с 1 по 10 из 0 записей' in no_doc:
                self.status_doc = 'На сайте нет документа.'

    def get_status(self):
        """ Получить статус белорусского документа """
        self.input_doc_number()
        # Пытаемся найти на странице зеленную карточку документа.
        self.check_green_box_valid_doc()

        # Если не было зеленого бокса с валидным документом пробуем найти
        # на странице красную карточку документа.
        if not self.found_doc:
            self.check_red_box_invalid_doc()

        # Если на странице был красный или зеленый бокс.
        self.get_status_from_page()

        # Если статус не получили, то проверка на сообщение об ошибке при загрузке данных.
        if not self.status_doc:
            self.check_data_loading_error_and_zero_docs()

        if not self.status_doc:
            raise Exception('Нет статуса')

        self.browser.browser.back()
