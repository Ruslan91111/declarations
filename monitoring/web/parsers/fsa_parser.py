"""
Классы для сбора данных с сайта FSA.

Классы:

    - FSADeclParser(BaseParser):
        Класс для сбора данных по декларациям с сайта ФСА.

    - FSACertParser(FSADeclParser):
        Класс для сбора данных по сертификатам на сайте FSA.
"""
import random
import re
import time

from selenium.common import ElementClickInterceptedException, TimeoutException

from common.constants import FsaXPaths, REQUIRED_DATA_KEYS_FSA
from common.logger_config import logger
from common.work_with_files_and_dirs import random_delay_from_1_to_3
from common.exceptions import Server403Exception, NotLoadedForNewDocException
from web.parsers.base_parser import BaseParser


class FSADeclParser(BaseParser):
    """Класс для сбора данных по декларациям с сайта ФСА."""

    def __init__(self, browser_worker, document, ogrn_and_addresses: dict):
        super().__init__(browser_worker, document, ogrn_and_addresses)
        self.template_for_chapter_xpath = FsaXPaths.CHAPTER.value
        self.required_keys_for_collect = REQUIRED_DATA_KEYS_FSA
        self.request_time = 0
        self.browser.switch_to_tab(self.browser.tabs['declaration'])

    def prepare_numb_for_input(self):
        """ Убрать начало номера декларации до точки. """
        return self.document.number[self.document.number.find('.'):]

    def input_doc_numb(self):
        """ Ввести номер документа на сайте ФСА. """
        self.browser.input_and_press_search(FsaXPaths.INPUT_FIELD.value,
                                            self.prepare_numb_for_input(),
                                            FsaXPaths.SEARCH_BUTTON.value)

    def return_for_input_doc_numb(self, xpath=FsaXPaths.RETURN_BACK_DECL.value):
        """ После просмотра документа вернуться на страницу для ввода номера. """
        random_delay_from_1_to_3()
        self.browser.wait_and_click_elem(xpath)

    def click_chapter(self, item: int) -> str:
        """ Переключить подраздел и вернуть его наименование. """
        try:
            chapter = self.browser.wait_and_click_elem(
                self.template_for_chapter_xpath + f'[{item}]/a')
        except ElementClickInterceptedException:
            chapter = self.browser.wait_elem_clickable(
                self.template_for_chapter_xpath + f'[{item}]/a')
            self.browser.browser.execute_script("arguments[0].scrollIntoView(true);", chapter)
            chapter.click()
        chapter = chapter.get_attribute('href')
        chapter_name = chapter[chapter.rfind('/') + 1:]
        return chapter_name

    def get_last_chapter_numb(self) -> int:
        """ Определить номер последней главы - соответственно количество итераций. """
        elements = self.browser.wait_all_located_by_xpath(
            FsaXPaths.LAST_CHAPTER.value)
        number_of_last_chapter = len(elements)  # Номер последней итерации.
        return number_of_last_chapter

    def get_data_from_chapter(self, data: dict, chapter_name: str) -> dict:
        """Собрать данные с одного подраздела на сайте ФСА."""
        headers = self.browser.find_all_elems_by_class("info-row__header")
        texts = self.browser.find_all_elems_by_class("info-row__text")
        # Преобразуем данные в словарь.
        for header, text in zip(headers, texts):
            key = header.text.strip()
            if key in self.required_keys_for_collect:  # Берем только необходимые колонки.
                value = text.text.strip()
                data[key + ' ' + chapter_name] = value
        return data

    def click_chapter_get_data(self, data: dict, item: int) -> dict:
        """ Кликнуть по подразделу и собрать с него данные. """
        chapter_name = self.click_chapter(item)
        data = self.get_data_from_chapter(data, chapter_name)
        return data

    def save_status_from_site(self):
        """ Сохранить статус документа. """
        self.document.status_on_site = (self.browser.get_text_by_xpath(
            FsaXPaths.DOC_STATUS.value))

    def check_403_error(self) -> bool:
        """ Проверка нет ли на экране сообщения об ошибке 403."""
        return bool(self.browser.find_all_elems_by_xpath(FsaXPaths.ERROR_403.value))

    def check_not_available_error(self):
        """ Проверка нет ли на экране сообщения о недоступности сервиса,
        если есть кликнуть 'ok'. """
        start = time.time()
        while time.time() - start < 2:

            error = self.browser.find_all_elems_by_xpath(FsaXPaths.SERV_NOT_AVAILABLE.value)

            if error:
                logger.error("Ошибка - сообщение на странице: 'Сервис недоступен'.")
                random_delay_from_1_to_3()
                self.browser.press_elem_through_chain(
                    FsaXPaths.SERV_NOT_AVAILABLE_BUTTON.value)
                self.browser.refresh_browser()

    def is_doc_number_loaded(self, timeout=5) -> bool:
        """ Проверить прогрузились ли документы на новый введенный номер документа. """
        start = time.time()
        while time.time() - start < timeout:
            loaded_number_on_site = self.browser.get_text_by_xpath(
                FsaXPaths.ROW_DOC_ON_SITE.value.format(row=2, column=3))
            loaded_number_on_site = re.search(r'\d{5}', loaded_number_on_site).group()
            number_from_gold = re.search(r'\d{5}', self.document.number).group()

            if loaded_number_on_site == number_from_gold:
                return True

        return False

    def no_matching_records(self):
        """ Проверить прогрузились ли документы на новый введенный номер документа. """
        no_records_matching_the_search = self.browser.get_text_by_xpath(
            FsaXPaths.NO_MATCHING_RECORDS.value)
        if no_records_matching_the_search:
            self.document.status_on_site = "Нет записей, удовлетворяющих поиску"


    def _is_document_appropriate(self, document_number, expiration_date):
        """ Проверка, соответствует ли документ заданному номеру и дате. """
        return (document_number == self.document.number and
                expiration_date == self.document.expiration_date)

    def _update_document_status(self, row):
        """ Обновить статус документа. """
        image_with_status = self.browser.wait_elem_clickable(
                FsaXPaths.STATUS_ON_IMAGE.value.format(row=row, column=2))
        self.document.status_on_site = image_with_status.get_property('alt')

    def _scroll_to_next_row(self, row):
        """ Прокрутить к следующей строке документа. """
        next_row_on_page = self.browser.wait_elem_clickable(
            FsaXPaths.ROW_DOC_ON_SITE.value.format(row=row, column=3))
        self.browser.browser.execute_script(
            "arguments[0].scrollIntoView(true);", next_row_on_page)

    def click_correct_doc(self, row) -> bool:
        """ Кликнуть по документу, который подходит по дате окончания и номеру. """
        # Находим номер и дату истечения документа на странице
        fsa_doc_numb = self.browser.wait_elem_clickable(
            FsaXPaths.ROW_DOC_ON_SITE.value.format(row=row, column=3))
        text_fsa_doc_numb = fsa_doc_numb.text
        fsa_expiration_date = self.browser.get_text_by_xpath(
            FsaXPaths.ROW_DOC_ON_SITE.value.format(row=row, column=5))

        if self._is_document_appropriate(text_fsa_doc_numb, fsa_expiration_date):
            self._update_document_status(row)

            # Кликаем и проваливаемся только по действующим декларациям.
            if self.document.status_on_site in {'Действует', 'Возобновлён'}:
                fsa_doc_numb.click()
                self.request_time = time.time()
                return True
            self.browser.browser.execute_script(
                "arguments[0].scrollIntoView(true);", fsa_doc_numb)

        if row == 4:
            # Прокрутить страницу к следующим документам.
            self._scroll_to_next_row(row)

        return False

    def search_correct_document(self) -> bool:
        """ Поиск на странице подходящего документа. """
        def search_cycle(last_row: int) -> bool:
            """ Цикл для поиска корректного документа."""
            for i in range(1, last_row):
                if self.click_correct_doc(i):
                    return True
            return False

        count_of_rows = len(
            self.browser.find_all_elems_by_xpath(FsaXPaths.COUNT_OF_PAGE.value))
        last_row = 3 if count_of_rows == 1 else min(count_of_rows + 2, 5)

        # Документ был найден в первом цикле.
        if search_cycle(last_row):
            return True

        # Если количество строк больше 4, пробуем еще один цикл.
        if count_of_rows >= 5 and search_cycle(last_row):
            return True

        # Проверка на действительный статус.
        if count_of_rows == 1 and not self.check_not_valid_status():
            logger.info(f'Не найдено подходящего по номеру и дате истечения '
                        f'документа для № {self.document.number} на сайте ФСА.'
                        f'Возможно указана неверная дата')
            self.document.status_on_site = 'Не найден на сайте, проверьте номер и дату'

        return False

    def check_not_valid_status(self) -> bool:
        """ Проверка, что статус у декларации отличный от 'Недействителен'. """
        fsa_doc_number = self.browser.get_text_by_xpath(
            FsaXPaths.ROW_DOC_ON_SITE.value.format(row=2, column=3))
        status_on_page = self.browser.wait_elem_clickable(
            FsaXPaths.STATUS_ON_IMAGE.value.format(row=2, column=2))
        status_of_document = status_on_page.get_property('alt')
        self.document.status_on_site = status_of_document

        if (fsa_doc_number == self.document.number and
                self.document.status_on_site == 'Недействителен'):
            return True
        return False

    def _get_data_on_document(self) -> dict | None:
        """ Собрать данные по документу. Сначала - ввод и проверки:
        доступности сервера, наличия и доступности данных. Затем непосредственно
         сбор данных. """
        data = {}

        if self.check_403_error():  # Проверка доступности сервера.
            raise Server403Exception('403 на странице')

        # Ввод номера декларации.
        self.input_doc_numb()
        random_delay_from_1_to_3()

        # Проверка загрузки документов под введенный номер и наличия данных.
        try:
            if not self.is_doc_number_loaded():
                raise NotLoadedForNewDocException(self.document.number)
        except TimeoutException:
            self.no_matching_records()

        if self.document.status_on_site == "Нет записей, удовлетворяющих поиску":
            return None

        # Выбрать подходящую декларацию.
        if not self.search_correct_document():
            return None

        # Проверка доступности сервера.
        self.check_not_available_error()
        if self.document.status_on_site != 'Действует':
            self.return_for_input_doc_numb()
            return None

        # Определяем номер последней главы - количество итераций для сбора данных.
        count_of_iterations = self.get_last_chapter_numb()

        # Перебираем и кликаем по подразделам на странице.
        for item in range(1, count_of_iterations + 1):
            random_delay_from_1_to_3()
            data.update(self.click_chapter_get_data(data, item))

        self.return_for_input_doc_numb()  # Возвращение на страницу для ввода номера.
        return data

    def process_get_data_on_doc(self):
        """ Организация процесса - сбора данных по документу. """
        data_from_web = self._get_data_on_document()

        if data_from_web:
            self.document.save_attrs_from_parser(data_from_web)
            address_checker = self.choose_address_checker()
            address_checker = address_checker(self.browser,
                                              self.document,
                                              self.ogrn_and_addresses)
            address_checker.get_both_addresses_and_compare()
            self.document = address_checker.document
            self.ogrn_and_addresses = address_checker.ogrn_and_addresses
            self.browser.switch_to_tab(self.browser.tabs['gost'])
            self.verify_gost_numbers()


class FSACertParser(FSADeclParser):
    """ Класс для сбора данных по сертификатам на сайте FSA. """

    def __init__(self, browser_worker, document, ogrn_and_addresses: dict):
        super().__init__(browser_worker, document, ogrn_and_addresses)
        self.browser.switch_to_tab(self.browser.tabs['certificate'])

    def return_for_input_doc_numb(self, xpath=FsaXPaths.RETURN_BACK_CERT.value):
        """ Вернуться на страницу для ввода номера. """
        time.sleep(random.randint(1, 3))
        self.browser.wait_and_click_elem(xpath)

    def get_data_from_chapter(self, data: dict, chapter_name: str) -> dict:
        """ Собрать данные с одной главы. """
        data = super().get_data_from_chapter(data, chapter_name)
        if chapter_name in {'applicant', 'manufacturer'}:
            inner_data = self.get_inner_elements_from_page(chapter_name)
            data.update(inner_data)
        return data

    def get_inner_elements_from_page(self, chapter: str) -> dict:
        """Собрать внутренние элементы на веб-странице. """
        inner_elements = {}
        self.browser.wait_all_located_by_class('card-edit-row__content')
        keys = self.browser.find_all_elems_by_class('card-edit-row__header')
        values = self.browser.find_all_elems_by_class('card-edit-row__content')
        for key, value in zip(keys, values):
            inner_elements[key.text + ' ' + chapter] = value.text
        return inner_elements
