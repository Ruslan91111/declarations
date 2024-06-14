"""
Модуль для проверки статусов международных документов.

Этот модуль содержит класс InternationalScrapper, который обрабатывает входной XLSX файл,
перебирает строки, определяет номера международных документов и проверяет их статусы на сайте.

Классы:
    InternationalScrapper:
        Класс для проверки статусов международных документов.

Функции:
    find_required_doc(number: str) -> bool:
        Проверяет, соответствует ли документ паттерну международного документа.

    determine_country_of_doc(number: str) -> str:
        Определяет страну документа из его номера.

Использование:
    1. Создайте экземпляр InternationalScrapper, передав путь к файлу результатов,
       класс для работы с браузером и файл для записи последнего проверенного номера.
    2. Вызовите метод check_statuses_of_international_docs_from_xlsx_file() для
       начала процесса проверки статусов.

Пример:
    international_scrapper = InternationalScrapper(Files.RESULT_FILE.value, BrowserWorker,
                                                    Files.LAST_VIEWED_FOR_INTERNATIONAL.value)
    international_scrapper.check_statuses_of_international_docs_from_xlsx_file()
"""
import time
import re

import pandas as pd

from monitoring.constants import Files, IndicatorsForInternationalDocs, Urls

from monitoring.functions_for_work_with_files_and_dirs import read_last_viewed_number_from_file, \
    write_last_viewed_number_to_file
from monitoring.monitoring_in_web import make_wait, BrowserWorker, make_browser


class InternationalScrapper:
    """ Класс для проверки данных по международным документам. """

    def __init__(self, result_file: str, browser_worker=BrowserWorker,
                 file_for_last_number=Files.LAST_VIEWED_FOR_INTERNATIONAL.value):
        self.result_file = result_file
        browser = make_browser(0)
        wait = make_wait(browser, 40)
        self.browser_worker = browser_worker(browser, wait)
        self.browser_worker.make_new_tab(Urls.INTERNATIONAL_DOCS.value)
        self.df = pd.read_excel(self.result_file)
        self.last_checked_in_web_number = read_last_viewed_number_from_file(file_for_last_number)
        self.number = ''
        self.indicators = IndicatorsForInternationalDocs

    def check_statuses_of_international_docs_from_xlsx_file(self):
        """ Перебрать строки в xlsx файле с результатами мониторинга,
        найти номера, подпадающие под паттерн международных документов и проверить их
        на сайте. """
        try:
            for iteration, row in self.df.iloc[self.last_checked_in_web_number:].iterrows():
                international_doc = find_required_doc(row['ДОС'])
                if international_doc:
                    self.number = row['ДОС']
                    print(self.number)
                    status = self.check_the_status_of_doc_in_web()
                    self.df.at[iteration, 'Статус на сайте'] = status
                    self.last_checked_in_web_number = row.name
        finally:
            self.write_df_and_last_checked_number_in_files()

    def check_the_status_of_doc_in_web(self):
        """ Проверить статус одного документа на странице сайта. """
        self.input_and_choice_country()
        self.input_reg_number()
        return self.get_the_status_of_doc()

    def input_and_choice_country(self):
        """ Ввести и выбрать на странице нужную страну."""
        old_country_on_page = self.browser_worker.get_text_from_element_by_xpath(
            self.indicators.EARLY_PICKED_COUNTRY.value)
        country_of_current_doc = determine_country_of_doc(self.number)

        if old_country_on_page is not None and old_country_on_page != country_of_current_doc:
            self.browser_worker.refresh_browser()
        self.check_that_page_loaded()

        # Кликнуть по полю для выбора страны.
        self.browser_worker.wait_and_press_element_through_chain(
            self.indicators.CLICK_TO_PICK_THE_COUNTRY.value)

        # Проверка, что окно для выбора страны полностью раскрылось.
        extended_country_field = self.browser_worker.find_elements_by_xpath(
            self.indicators.EXTENDED_COUNTRY_FIELD.value)
        if not extended_country_field:
            self.browser_worker.wait_and_press_element_through_chain(
                self.indicators.CLICK_TO_PICK_THE_COUNTRY.value)

        # Ввести название страны.
        self.browser_worker.input_in_field(self.indicators.COUNTRY_INPUT_FIELD.value,
                                           country_of_current_doc)
        # Выбрать нужную страну
        self.browser_worker.wait_and_click_element(
            self.indicators.FOR_PICK_REQUIRED_COUNTRY.value.format(country_of_current_doc))

    def input_reg_number(self):
        """ Нажать на фильтры, ввести номер, нажать применить."""
        # Выбрать фильтры
        filters = self.browser_worker.find_elements_by_xpath(self.indicators.HIDE_FILTERS.value)
        if not filters:
            self.browser_worker.wait_and_click_element(self.indicators.SHOW_FILTERS.value)
        # Ввести регистрационный номер
        self.browser_worker.wait_and_click_element(self.indicators.REG_NUMBER_INPUT_FIELD.value)
        self.browser_worker.input_in_field(
            self.indicators.REG_NUMBER_INPUT_FIELD.value, self.number)
        # Кликнуть по кнопке применить.
        self.browser_worker.wait_and_click_element(self.indicators.BUTTON_APPLY_FILTERS.value)
        self.check_that_page_loaded()

    def get_the_status_of_doc(self):
        """ Получить статус документа со страницы"""
        no_data = self.browser_worker.find_elements_by_xpath(
            self.indicators.NO_DATA_ABOUT_DOC.value)

        if no_data:
            status = 'Не найдено на сайте'
        else:
            self.browser_worker.find_elements_by_xpath(
                self.indicators.DOC_LOADED_ON_PAGE.value.format(self.number))
            status = self.browser_worker.get_text_from_element_by_xpath(
                self.indicators.STATUS_OF_DOC_ON_PAGE.value)

        return status

    def write_df_and_last_checked_number_in_files(self):
        """ Записать dataframe и последний просмотренный номер row в файлы. """
        self.df.to_excel(self.result_file, index=False)
        write_last_viewed_number_to_file(Files.LAST_VIEWED_FOR_INTERNATIONAL.value,
                                         self.last_checked_in_web_number)

    def check_that_page_loaded(self):
        """ Проверить, что содержимое страницы полностью загружено. """
        start = time.time()
        while time.time() - start < 90:
            loading = self.browser_worker.find_elements_by_xpath(
                self.indicators.LOADING_PROCESS.value)
            if loading:
                time.sleep(0.5)
            else:
                break


def find_required_doc(number: str):
    """ Проверить соответствует ли документ паттерну международного документа. """
    pattern = 'ЕАЭС (№ ?)?(KZ|BY|KG|AM)[\\w\\/\\.\\s-]+'
    match = re.match(pattern, number)
    if match:
        return True
    return False


def determine_country_of_doc(number: str):
    """ Определить страну документа."""
    countries_from_number = {
        'ЕАЭС (№ ?)?(KZ)[\\w\\/\\.\\s-]+': 'Казахстан',
        'ЕАЭС (№ ?)?(BY)[\\w\\/\\.\\s-]+': 'Беларусь',
        'ЕАЭС (№ ?)?(KG)[\\w\\/\\.\\s-]+': 'Кыргызстан',
        'ЕАЭС (№ ?)?(AM)[\\w\\/\\.\\s-]+': 'Армения'}

    for key, value in countries_from_number.items():
        match = re.match(key, number)
        if match:
            return value


if __name__ == '__main__':
    international_scrapper = InternationalScrapper(Files.RESULT_FILE.value, BrowserWorker,
                     Files.LAST_VIEWED_FOR_INTERNATIONAL.value)
    international_scrapper.check_statuses_of_international_docs_from_xlsx_file()
