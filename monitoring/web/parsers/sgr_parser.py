"""
Классы для сбора данных с сайта СГР.

Классы:

    - SgrParser(BaseParser):
        Класс для сбора данных по декларациям СГР.

"""
import re
import time

from selenium.common import NoSuchElementException

from common.constants import NSIXPaths, NSI_PATTERNS
from common.document_dataclass import Document
from web.parsers.base_parser import BaseParser


class SgrParser(BaseParser):
    """ Класс для сбора данных по СГР. """

    def __init__(self, browser_worker, document: Document, ogrn_and_addresses: dict):
        super().__init__(browser_worker, document, ogrn_and_addresses)
        self.change_letter_in_numb()
        self.browser.switch_to_tab(self.browser.tabs['nsi'])

    def change_letter_in_numb(self):
        """ Заменить букву в номере СГР. """
        self.document.number = self.document.number.replace('E', 'Е')

    def wait_till_page_loaded(self):
        """ Дождаться загрузки страницы - исчезновения элемента: затемнения на дисплее """
        loaded = False
        while not loaded:
            try:
                time.sleep(0.06)
                self.browser.find_elem_by_class(
                    'p-datatable-loading-overlay')
            except NoSuchElementException:
                loaded = True

    def no_data_message(self) -> bool:
        """ Проверяем есть ли данные. Если данных нет, то будет соответсвующее
        сообщение на странице. Если сообщение об отсутствии данных не найдено, то продолжить."""
        try:
            data_from_nsi = self.browser.get_text_by_xpath(
                NSIXPaths.NO_DATA.value)
            if data_from_nsi == 'Нет данных':
                self.document.status_on_site = 'Нет на сайте'
                return True
        except NoSuchElementException:
            return False

    def append_organisation_data(self, text: str, type_of_org: str,
                                 patterns: dict) -> None:
        """ Добавляем данные об организации в зависимости от того,
        как и что изложено на сайте СГР. """

        name_match = re.match(patterns['name'], text)

        if name_match:
            address_in_brackets_match = re.search(patterns['address_in_brackets'], text)
            index_match = re.search(patterns['post_index'], text)
            address = '-'
            if address_in_brackets_match:
                address = address_in_brackets_match.group(1)
            elif index_match:
                address = text[index_match.start():text.find('[')]
            elif len(text) > len(name_match.group()):
                address = text[name_match.end():text.find('[')]
            setattr(self.document, f'address_{type_of_org}', address)
            ogrn = re.search(patterns['ogrn'], text)
            setattr(self.document, f'ogrn_{type_of_org}', ogrn.group() if ogrn else 'Нет ОГРН')
        else:
            setattr(self.document, f'brief_name_{type_of_org}', text)
            setattr(self.document, f'address_{type_of_org}', text)
            setattr(self.document, f'ogrn_{type_of_org}', 'Нет ОГРН')

    def get_all_data(self) -> None:
        """Собрать данные по свидетельству о государственной регистрации с сайта nsi.
        Вернет либо словарь, достаточный для добавления и последующей записи, либо None"""
        self.wait_till_page_loaded()

        # Найти и нажать на кнопку фильтра - после которой можно ввести номер СГР
        try:
            self.browser.wait_and_click_elem(NSIXPaths.INPUT_NUMB_FIELD.value)
        except Exception:
            time.sleep(3)
            self.browser.wait_and_click_elem(NSIXPaths.INPUT_NUMB_FIELD.value)

        self.wait_till_page_loaded()
        # Дождаться возможности ввода номера СГР, ввести и нажать поиск.
        self.browser.input_and_press_search(
            NSIXPaths.INPUT_NUMB_FIELD.value, self.document.number, NSIXPaths.SEARCH_BUTTON.value)

        if self.no_data_message():
            return None

        try:
            self.document.status_on_site = self.browser.get_text_by_xpath(NSIXPaths.STATUS_DOC.value)
        except:
            if self.no_data_message():
                return None

        if self.document.status_on_site != 'подписан и действует':
            return None

        # Добавляем в документы данные по заявителю.
        text_applicant = self.browser.get_text_by_xpath(NSIXPaths.APPLICANT.value)
        self.append_organisation_data(text_applicant, 'applicant', NSI_PATTERNS)
        # Добавляем в документы данные по производителю.
        text_manufacturer = self.browser.get_text_by_xpath(NSIXPaths.MANUFACTURER.value)
        self.append_organisation_data(text_manufacturer, 'manufacturer', NSI_PATTERNS)
        # Добавляем в документы данные по документации.
        self.document.regulatory_document = self.browser.get_text_by_xpath(
            NSIXPaths.NORMATIVE_DOCUMENTS.value)

    def process_get_data_on_doc(self):
        """ Организация процесса сбора данных по документу СГР. """
        self.get_all_data()
        address_checker = self.choose_address_checker()
        address_checker = address_checker(self.browser,
                                          self.document,
                                          self.ogrn_and_addresses)
        address_checker.get_both_addresses_and_compare()
        self.document = address_checker.document
        self.ogrn_and_addresses = address_checker.ogrn_and_addresses
        self.browser.switch_to_tab(self.browser.tabs['gost'])
        self.verify_gost_numbers()
