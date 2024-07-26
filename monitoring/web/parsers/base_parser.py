"""
Базовый абстрактный класс парсер с методами, которые используются наследованными
классами, а также абстрактными методами.

Классы:
    - class BaseParser(ABC):
         Базовый класс для сборщиков информации с интернет - ресурсов.

    Методы:
        - process_get_data_on_doc:
            абстрактный метод организации процесса сбора данных по документу.

        - verify_gost_numbers:
            Если в документе есть ГОСТ, то проверить его статус на сайте проверки ГОСТ.

        - verify_a_gost_numb_on_site:
             Проверить на сайте один ГОСТ.

        - check_captcha_error:
             Проверка нет ли на экране капчи.

        - choose_address_checker:
            Выбрать класс для проверки адреса.

"""

import re
from abc import ABC, abstractmethod

from web.verify_addresses import EgrulAddressChecker, RusprofileAddressChecker
from common.constants import PATTERN_GOST, GostXPaths, RusProfileXPaths
from common.document_dataclass import Document


class BaseParser(ABC):
    """ Базовый класс для сборщиков информации с интернет - ресурсов. """

    def __init__(self, browser_worker, document: Document, ogrn_and_addresses: dict):
        self.browser = browser_worker
        self.document = document
        self.ogrn_and_addresses = ogrn_and_addresses

    @abstractmethod
    def process_get_data_on_doc(self):
        """ Организация процесса сбора данных по документу. """

    def verify_gost_numbers(self) -> None:
        """ Если в документе есть ГОСТ, то проверить его статус на сайте проверки ГОСТ."""
        self.browser.switch_to_tab(self.browser.tabs['gost'])
        # Проверяем есть ли данные в тех полях, где могут содержаться номера ГОСТ.
        if not self.document.regulatory_document and not self.document.standard:
            return None
        text_with_possible_gost = self.document.regulatory_document + self.document.standard
        # Ищем подстроки, совпадающие с паттерном ГОСТ.
        all_gost_numbers = set(re.findall(PATTERN_GOST, text_with_possible_gost))
        statuses_of_all_gost_numbers = set()  # Переменная для сбора статусов ГОСТ.
        if not all_gost_numbers:
            return None
        for gost_number in all_gost_numbers:  # Перебираем ГОСТы.
            statuses_of_all_gost_numbers.add(self._verify_a_gost_numb_on_site(gost_number))
            # Сохранить значения с сайта ГОСТ
        self.document.status_of_regulatory_documentation = " ".join(statuses_of_all_gost_numbers)

    def _verify_a_gost_numb_on_site(self, gost_number: str) -> str:
        """ Проверить на сайте один ГОСТ."""
        self.browser.input_in_field(GostXPaths.INPUT_FIELD.value, gost_number)
        self.browser.wait_and_click_elem(GostXPaths.SEARCH_BUTTON.value)
        text_from_site = self.browser.get_text_by_xpath(
            GostXPaths.GOST_STATUS.value)
        return text_from_site

    def check_captcha_error(self) -> bool:
        """ Проверка нет ли на экране сообщения об ошибке 403."""
        element_captcha = self.browser.find_all_elems_by_xpath(
            RusProfileXPaths.CAPTCHA_SECTION.value)
        return bool(element_captcha)

    def choose_address_checker(self):
        """ Выбрать класс для проверки адреса. """
        self.browser.switch_to_tab(self.browser.tabs['rusprofile'])
        if self.check_captcha_error():
            self.browser.switch_to_tab(self.browser.tabs['egrul'])
            return EgrulAddressChecker
        return RusprofileAddressChecker
