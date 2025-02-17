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
        self.status = ""
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
            self.get_belorus_status()

    def get_belorus_status(self):
        """ Получить статус белорусского документа """
        # Ввести номер документа на странице.
        self.browser.input_in_field(BelarusXPATH.INPUT_FIELD.value, self.number)
        time.sleep(0.5)
        # Кнопка поиска.
        self.browser.wait_and_click_elem(BelarusXPATH.SEARCH_BUTTON.value)
        # Кнопку применить для поиска нужного документа.
        self.browser.wait_and_click_elem(BelarusXPATH.APPLY_BUTTON.value)
        # Ждем пока страница полностью прогрузится.
        self.browser.wait_till_page_loaded(BelarusXPATH.LOADING_ELEM.value)

        found_doc = False
        numb_from_page = False
        # Пытаемся найти на странице зеленную карточку документа.
        try:
            numb_from_page = self.browser.get_text_by_xpath(BelarusXPATH.SUCCESS_DOC.value)
            found_doc = True
        except (NoSuchElementException, TimeoutException):
            print('Нет документа с валидным статусом.')

        # Пытаемся найти на странице красную карточку документа.
        if not found_doc:
            try:
                numb_from_page = self.browser.get_text_by_xpath(BelarusXPATH.WRONG_DOC.value)
                found_doc = True
            except (NoSuchElementException, TimeoutException):
                print('Нет документа с невалидным статусом.')


        # Если была зеленая или красная карточка документа.
        if found_doc:
            # Берем номер документа.
            # numb_from_page = self.browser.get_text_by_xpath(BelarusXPATH.SUCCESS_DOC.value)
            # Проверяем, что документ, загруженный на странице по номеру соответствует проверяемому.
            if not numb_from_page == self.number:
                return 'Декларация на странице не обнаружена.'
            # Ищем и выдрезаем статус документа.
            doc_status_place = self.browser.wait_elem_located(BelarusXPATH.STATUS_PLACE.value)
            full_text = doc_status_place.text
            # Сохраняем статус документа.
            self.status_doc = re.search(r'\(\d{2}\)\s*\w+', full_text, re.IGNORECASE).group()


        # Если не было ни зеленой, ни красной карточки документа.
        else:
            try:
                data_loading_error = self.browser.find_elem_by_xpath("//*[contains(@class, 'alert')]")
                if data_loading_error:
                    time.sleep(10)
                    raise DataLoadingError()
            except (NoSuchElementException, TimeoutException):
                pass

            no_doc = self.browser.get_text_by_xpath(BelarusXPATH.NO_DOCS.value)
            if 'Отображено с 1 по 10 из 0 записей' in no_doc:
                self.status_doc = 'На сайте нет документа.'

        # Вернуться на страницу ввода номера документа.
        self.browser.browser.back()





# if __name__ == '__main__':
#     number_test_by = 'ЕАЭС № BY/112 11.01. ТР021 018 05361'
#     number_test_kg = 'ЕАЭС KG417/024.Д.0013077'
#
#     parser = InternDocParser()
#     parser.get_status_from_web(number_test)
#     print(parser.number)

    # def input_and_choice_country(self):
    #     """ Ввести и выбрать на странице нужную страну."""
    #     self.check_country_on_page()
    #     # Кликнуть по полю для выбора страны.
    #     self.browser.press_elem_through_chain(self.indicators.CLICK_TO_PICK_THE_COUNTRY.value)
    #     self.page_loaded_check()
    #     self.check_extended_country_field()
    #     # Ввести название страны.
    #     self.browser.input_in_field(self.indicators.COUNTRY_INPUT_FIELD.value, self.doc_country)
    #     random_delay()
    #     # Выбрать нужную страну
    #     self.browser.wait_and_click_elem(
    #         self.indicators.FOR_PICK_REQUIRED_COUNTRY.value.format(self.doc_country))
    #     self.page_loaded_check()
    #
    # def check_country_on_page(self):
    #     """ Если страна не введена или не совпадает с текущей. """
    #     country_on_page = self.browser.get_text_by_xpath(self.indicators.PREVIOUS_COUNTRY.value)
    #     self.doc_country = determine_country_of_doc(self.number)
    #     if country_on_page != self.doc_country and country_on_page != '':
    #         self.browser.refresh_browser()
    #         self.page_loaded_check()
    #
    # def check_extended_country_field(self):
    #     """ Проверка, что окно для выбора страны полностью раскрылось. """
    #     if not self.browser.find_all_elems_by_xpath(
    #             self.indicators.EXTENDED_COUNTRY_FIELD.value):
    #         self.browser.press_elem_through_chain(
    #             self.indicators.CLICK_TO_PICK_THE_COUNTRY.value)
    #
    # def input_reg_number(self):
    #     """ Нажать на фильтры, ввести номер, нажать применить."""
    #     self.filters_check()
    #     # Ввести регистрационный номер
    #     self.browser.wait_and_click_elem(self.indicators.REG_NUMBER_FIELD.value)
    #     random_delay()
    #     self.browser.input_in_field(self.indicators.REG_NUMBER_FIELD.value, self.number)
    #     # Кликнуть по кнопке применить.
    #     self.browser.wait_and_click_elem(self.indicators.BUTTON_APPLY_FILTERS.value)
    #     self.page_loaded_check()
    #
    # def filters_check(self):
    #     """ Проверить, что фильтры открыты, если не открыты, то кликнуть по ним. """
    #     if not self.browser.find_all_elems_by_xpath(self.indicators.HIDE_FILTERS.value):
    #         self.browser.wait_and_click_elem(self.indicators.SHOW_FILTERS.value)
    #
    # def save_status_from_page(self):
    #     """ Сохранить статус документа со страницы"""
    #
    #     try:
    #         self.browser.find_all_elems_by_xpath(self.indicators.DOC_LOADED_ON_PAGE.value.format(self.number))
    #
    #         self.status = self.browser.get_text_by_xpath(
    #             self.indicators.STATUS_OF_DOC_ON_PAGE.value.format(self.number))
    #
    #     except:
    #         if self.browser.find_all_elems_by_xpath(self.indicators.NO_DATA_ABOUT_DOC.value):
    #             self.status = 'Нет данных'
    #
    # def page_loaded_check(self):
    #     """ Проверить, что содержимое страницы полностью загружено. """
    #     start = time.time()
    #     loading = None
    #     while time.time() - start < 240:
    #         loading = self.browser.find_all_elems_by_xpath(
    #             self.indicators.LOADING_PROCESS.value)
    #         if not loading:
    #             break
    #         time.sleep(3)
    #     if loading:
    #         raise Exception('Декларации не прогрузились')
    #
    # def check_not_available_serv(self):
    #     """ Проверить на наличие сообщения о недоступности сервиса."""
    #     error = self.browser.find_all_elems_by_xpath(self.indicators.NOT_AVAILABLE_SERV.value)
    #     if error:
    #         print("Ошибка - сообщение на странице: 'Сервис недоступен'.")
    #         self.browser.press_elem_through_chain(self.indicators.CLOSE_NOT_AVAIL_ERR.value)
    #         time.sleep(60 * 10)
