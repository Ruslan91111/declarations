"""
    class InternDocParser:
        Класс для взаимодействия с сайтом для проверки международных документов.
"""
import time

from common.constants import Urls, IndicatorsForInternDocs
from common.work_with_files_and_dirs import random_delay_from_1_to_3
from web.intern_docs.helpers import determine_country_of_doc
from web.work_with_browser import create_browser_with_wait, BrowserWorker


class InternDocParser:
    """ Класс для взаимодействия с сайтом для проверки международных документов. """
    def __init__(self):
        self.browser = create_browser_with_wait(0, BrowserWorker, 240)
        self.browser.make_new_tab(Urls.INTERNATIONAL_DOCS.value)
        self.indicators = IndicatorsForInternDocs
        self.status = ""
        self.number = ''

    def get_status_from_web(self):
        """ Проверить статус одного документа на странице сайта. """
        self.input_and_choice_country()
        self.input_reg_number()
        self.save_status_from_page()

    def input_and_choice_country(self):
        """ Ввести и выбрать на странице нужную страну."""
        self.check_country_on_page()
        # Кликнуть по полю для выбора страны.
        self.browser.press_elem_through_chain(self.indicators.CLICK_TO_PICK_THE_COUNTRY.value)
        self.page_loaded_check()
        self.check_extended_country_field()
        # Ввести название страны.
        self.browser.input_in_field(self.indicators.COUNTRY_INPUT_FIELD.value, self.doc_country)
        random_delay_from_1_to_3()
        # Выбрать нужную страну
        self.browser.wait_and_click_elem(
            self.indicators.FOR_PICK_REQUIRED_COUNTRY.value.format(self.doc_country))
        self.page_loaded_check()

    def check_country_on_page(self):
        """ Если страна не введена или не совпадает с текущей. """
        country_on_page = self.browser.get_text_by_xpath(self.indicators.PREVIOUS_COUNTRY.value)
        self.doc_country = determine_country_of_doc(self.number)
        if country_on_page != self.doc_country and country_on_page != '':
            self.browser.refresh_browser()
            self.page_loaded_check()

    def check_extended_country_field(self):
        """ Проверка, что окно для выбора страны полностью раскрылось. """
        if not self.browser.find_all_elems_by_xpath(
                self.indicators.EXTENDED_COUNTRY_FIELD.value):
            self.browser.press_elem_through_chain(
                self.indicators.CLICK_TO_PICK_THE_COUNTRY.value)

    def input_reg_number(self):
        """ Нажать на фильтры, ввести номер, нажать применить."""
        self.filters_check()
        # Ввести регистрационный номер
        self.browser.wait_and_click_elem(self.indicators.REG_NUMBER_INPUT_FIELD.value)
        random_delay_from_1_to_3()
        self.browser.input_in_field(self.indicators.REG_NUMBER_INPUT_FIELD.value, self.number)
        # Кликнуть по кнопке применить.
        self.browser.wait_and_click_elem(self.indicators.BUTTON_APPLY_FILTERS.value)
        self.page_loaded_check()

    def filters_check(self):
        """ Проверить, что фильтры открыты, если не открыты, то кликнуть по ним. """
        if not self.browser.find_all_elems_by_xpath(self.indicators.HIDE_FILTERS.value):
            self.browser.wait_and_click_elem(self.indicators.SHOW_FILTERS.value)

    def save_status_from_page(self):
        """ Сохранить статус документа со страницы"""
        if self.browser.find_all_elems_by_xpath(self.indicators.NO_DATA_ABOUT_DOC.value):
            self.status = 'Нет данных'

        else:
            self.browser.find_all_elems_by_xpath(
                self.indicators.DOC_LOADED_ON_PAGE.value.format(self.number))
            self.status = self.browser.get_text_by_xpath(
                self.indicators.STATUS_OF_DOC_ON_PAGE.value.format(self.number))

    def page_loaded_check(self):
        """ Проверить, что содержимое страницы полностью загружено. """
        start = time.time()
        loading = None
        while time.time() - start < 240:
            loading = self.browser.find_all_elems_by_xpath(
                self.indicators.LOADING_PROCESS.value)
            if not loading:
                break
            time.sleep(3)
        if loading:
            raise Exception('Декларации не прогрузились')

    def check_not_available_serv(self):
        """ Проверить на наличие сообщения о недоступности сервиса."""
        error = self.browser.find_all_elems_by_xpath(self.indicators.NOT_AVAILABLE_SERV.value)
        if error:
            print("Ошибка - сообщение на странице: 'Сервис недоступен'.")
            self.browser.press_elem_through_chain(self.indicators.CLOSE_NOT_AVAIL_ERR.value)
            time.sleep(60 * 10)
