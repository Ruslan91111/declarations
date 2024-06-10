""" Классы scrapeer - классы для сбора данных с сайтов и их сохранения в модель Document.
BaseScrapper - абстрактный класс. Остальные классы для работы по сбору информации
с конкретными сайтами. """
import random
import re
import time
from abc import ABC, abstractmethod

from selenium.common import TimeoutException, NoSuchElementException


from monitoring.constants import (PATTERN_GOST, GostXPaths, RusProfileXPaths,
                                  PARTS_TO_BE_REMOVED_FROM_ADDRESS, FsaXPaths,
                                  REQUIRED_KEYS_TO_GET_FROM_FSA, NSIXPaths, PATTERNS_FOR_NSI)
from monitoring.exceptions import (NotLoadedDocumentsOnFsaForNewNumberException, Server403Exception,
                                   StopMonitoringException)
from monitoring.functions_for_work_with_files_and_dirs import random_delay_from_1_to_3
from monitoring.logger_config import logger
from monitoring.document_dataclass import Document


class BaseScrapper(ABC):
    """ Базовый класс для сборщиков информации с интернет - ресурсов. """

    def __init__(self, browser_worker, document: Document):
        self.browser_worker = browser_worker
        self.document = document

    @abstractmethod
    def process_get_data_on_document(self):
        pass

    def check_the_validity_of_all_gost_numbers(self) -> None:
        """ Если в документе есть ГОСТ, то проверить его статус на сайте проверки ГОСТ."""
        self.browser_worker.switch_to_tab(self.browser_worker.tabs['gost'])
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
            statuses_of_all_gost_numbers.add(self._check_a_gost_number_on_site(gost_number))
            # Сохранить значения с сайта ГОСТ
        self.document.status_of_regulatory_documentation = " ".join(statuses_of_all_gost_numbers)

    def _check_a_gost_number_on_site(self, gost_number: str) -> str:
        """ Проверить на сайте один ГОСТ."""
        self.browser_worker.input_in_field(GostXPaths.INPUT_FIELD.value, 'ГОСТ ' + gost_number)
        self.browser_worker.wait_and_click_element(GostXPaths.SEARCH_BUTTON.value)
        text_from_site = self.browser_worker.get_text_from_element_by_xpath(GostXPaths.GOST_STATUS.value)
        return text_from_site

    def _get_an_address_from_rusprofile(self, ogrn: str, address_field: str) -> None:
        """ Получить адрес с сайта https://www.rusprofile.ru/ по ОГРН.
        Если ОГРН отсутствует, то записать соответствующее сообщение."""

        if not ogrn or ogrn == 'Нет ОГРН':
            setattr(self.document, address_field, 'Нет ОГРН')
            return None

        random_delay_from_1_to_3()
        self.browser_worker.input_in_field(RusProfileXPaths.INPUT_FIELD.value, ogrn)
        random_delay_from_1_to_3()
        self.browser_worker.wait_and_click_element(RusProfileXPaths.SEARCH_BUTTON.value)
        address = self.browser_worker.get_text_from_element_by_xpath(RusProfileXPaths.ADDRESS_PLACE.value)
        setattr(self.document, address_field, address if address else 'Адрес не найден')

    def compare_the_addresses(self) -> None:
        """ Сравнить строки - адреса: 1) с сайта и 2) rusprofile.
        Предварительно из строк(адресов) убрать обозначения, наподобие: ул. гор. и т.д.
        затем сравнить что останется в строках. """
        elements_to_be_removed_from_address = PARTS_TO_BE_REMOVED_FROM_ADDRESS

        def _prepare_address_for_comparison(string: str) -> list:
            """Подготовить адреса перед сравнением - убрать сокращения,
            лишние знаки, разбить в словарь по символам."""
            string = (string.upper().replace('.', ' ').replace('(', '').replace(')', '').
                      replace(',', ' '))
            # Убираем сокращения и обозначения.
            for elem in elements_to_be_removed_from_address:
                string = string.replace(elem, ' ')
            return sorted(string.replace(' ', ''))

        # Привести адреса к единому виду - отсортированным спискам строк.
        applicant_address = _prepare_address_for_comparison(self.document.address_applicant)
        applicant_address_rusprofile = _prepare_address_for_comparison(self.document.rusprofile_address_applicant)
        manufacturer_address = _prepare_address_for_comparison(self.document.address_manufacturer)
        manufacturer_address_rusprofile = _prepare_address_for_comparison(self.document.rusprofile_address_manufacturer)

        # Сделать и внести в словарь вывод о соответствии адресов.
        if (applicant_address == applicant_address_rusprofile and
                manufacturer_address == manufacturer_address_rusprofile):
            self.document.address_matching = 'Соответствуют'
        else:
            self.document.address_matching = 'Не соответствуют'

    def get_addresses_from_rusprofile_and_make_decision_about_matching(self):
        self._get_an_address_from_rusprofile(self.document.ogrn_applicant, 'rusprofile_address_applicant')
        self._get_an_address_from_rusprofile(self.document.ogrn_manufacturer, 'rusprofile_address_manufacturer')
        self.compare_the_addresses()


class FSADeclarationScrapper(BaseScrapper):
    """Класс для сбора данных по декларациям с сайта ФСА."""

    def __init__(self, browser_worker, document):
        super().__init__(browser_worker, document)
        self.template_for_chapter_xpath = FsaXPaths.CHAPTER.value
        self.required_keys_for_collect = REQUIRED_KEYS_TO_GET_FROM_FSA
        self.request_time = 0
        self.browser_worker.switch_to_tab(self.browser_worker.tabs['declaration'])

    def prepare_number_to_input_on_site(self):
        """ Убрать начало номера декларации до точки. """
        return self.document.number[self.document.number.find('.'):]

    def input_document_number(self):
        """ Ввести номер документа на сайте ФСА. """
        self.browser_worker.input_in_field_and_press_search_button(
            FsaXPaths.INPUT_FIELD.value,
            self.prepare_number_to_input_on_site(),
            FsaXPaths.SEARCH_BUTTON.value)

    def return_to_input_document_number(self, xpath=FsaXPaths.RETURN_BACK_DECLARATION.value):
        """ После просмотра документа вернуться на страницу для ввода номера. """
        random_delay_from_1_to_3()
        self.browser_worker.wait_and_click_element(xpath)

    def click_chapter(self, item: int) -> str:
        """ Переключить подраздел и вернуть его наименование. """
        chapter = self.browser_worker.wait_and_click_element(self.template_for_chapter_xpath + f'[{item}]/a')
        chapter = chapter.get_attribute('href')
        chapter_name = chapter[chapter.rfind('/') + 1:]
        return chapter_name

    def find_out_the_number_of_last_chapter(self) -> int:
        """ Определить номер последней главы - соответственно количество итераций.  """
        elements = self.browser_worker.wait_until_all_elements_located_by_xpath(
            FsaXPaths.CHAPTER_FOR_LAST_ITERATION.value)
        number_of_last_chapter = len(elements)  # Номер последней итерации.
        return number_of_last_chapter

    def get_data_from_one_chapter(self, data: dict, chapter_name: str) -> dict:
        """Собрать данные с одного подраздела на сайте ФСА."""
        headers = self.browser_worker.find_elements_by_class("info-row__header")
        texts = self.browser_worker.find_elements_by_class("info-row__text")
        # Преобразуем данные в словарь.
        for header, text in zip(headers, texts):
            key = header.text.strip()
            if key in self.required_keys_for_collect:  # Берем только необходимые колонки.
                value = text.text.strip()
                data[key + ' ' + chapter_name] = value
        return data

    def click_chapter_get_data(self, data: dict, item: int) -> dict:
        chapter_name = self.click_chapter(item)
        data = self.get_data_from_one_chapter(data, chapter_name)
        return data

    def save_status_on_site(self):
        """ Сохранить статус документа. """
        self.document.status_on_site = (
            self.browser_worker.get_text_from_element_by_xpath(FsaXPaths.DOCUMENT_STATUS.value))

    def check_403_error(self) -> bool:
        """ Проверка нет ли на экране сообщения об ошибке 403."""
        return bool(self.browser_worker.find_elements_by_xpath(FsaXPaths.ERROR_403.value))

    def check_service_not_available_error(self):
        """ Проверка нет ли на экране сообщения о недоступности сервиса, если есть кликнуть 'ok'. """
        start = time.time()
        while time.time() - start < 2:
            error = self.browser_worker.find_elements_by_xpath(FsaXPaths.SERVICE_NOT_AVAILABLE.value)
            if error:
                logger.error("Ошибка - сообщение на странице: 'Сервис недоступен'.")
                random_delay_from_1_to_3()
                self.browser_worker.wait_and_press_element_through_chain(FsaXPaths.SERVICE_NOT_AVAILABLE_OK_BUTTON.value)
                self.browser_worker.refresh_browser()
                return None

    def check_that_docs_for_new_number_loaded_on_page(self, timeout=5):
        """ Проверить прогрузились ли документы на новый введенный номер документа. """
        start = time.time()
        while time.time() - start < timeout:
            loaded_number_on_site = self.browser_worker.get_text_from_element_by_xpath(
                FsaXPaths.ROW_DOCUMENT_ON_SITE.value.format(row=2, column=3))
            loaded_number_on_site = loaded_number_on_site[loaded_number_on_site.find('.'):]
            number_from_gold = self.prepare_number_to_input_on_site()

            if loaded_number_on_site == number_from_gold:
                return True
        return False

    def _search_correct_document_by_number_and_date(self, row):
        """ Кликнуть по документу, который подходит по дате окончания и номеру.
         Проверяем загрузились ли на странице сайта документы по новому номеру.
         Затем ищем, тот документ, который совпадает по номеру и дате истечения.
         кликаем по нему."""
        fsa_doc_number = self.browser_worker.get_text_from_element_by_xpath(
            FsaXPaths.ROW_DOCUMENT_ON_SITE.value.format(row=row, column=3))
        fsa_expiration_date = self.browser_worker.get_text_from_element_by_xpath(
            FsaXPaths.ROW_DOCUMENT_ON_SITE.value.format(row=row, column=5))

        if (fsa_doc_number == self.document.number and
                fsa_expiration_date == self.document.expiration_date):
            self.browser_worker.wait_and_click_element(FsaXPaths.ROW_DOCUMENT_ON_SITE.value.format(row=row, column=5))
            self.request_time = time.time()
            return True

        return False

    def pick_right_document(self):
        """Обновить браузер, дождаться список документов, кликнуть по нужному документу в списке."""

        picked = False
        i = 1
        try:
            while not picked:
                picked = self._search_correct_document_by_number_and_date(i)
                i += 1
            return True

        except TimeoutException:
            logger.error(f'Не найдено подходящего по номеру и дате истечения '
                         f'документа для № {self.document.number} на сайте ФСА.')
            self.document.status_on_site = 'Не найден на сайте, проверьте номер и дату'
            return False

    def _get_data_on_document(self) -> dict | None:
        """ Собрать данные по документу. """
        data = {}

        if self.check_403_error():
            raise Server403Exception('403 на странице')

        self.input_document_number()
        random_delay_from_1_to_3()

        if not self.check_that_docs_for_new_number_loaded_on_page():
            raise NotLoadedDocumentsOnFsaForNewNumberException(self.document.number)

        picked_doc = self.pick_right_document()
        self.check_service_not_available_error()

        if picked_doc:
            self.save_status_on_site()

        if self.document.status_on_site == 'Не найден на сайте, проверьте номер и дату' or not picked_doc:
            return None
        if self.document.status_on_site != 'ДЕЙСТВУЕТ':
            self.return_to_input_document_number()
            return None

        # Определяем номер последней главы - количество итераций для сбора данных.
        count_of_iterations = self.find_out_the_number_of_last_chapter()
        # Перебираем и кликаем по подразделам на странице.
        for item in range(1, count_of_iterations + 1):
            random_delay_from_1_to_3()
            data.update(self.click_chapter_get_data(data, item))

        # Возвращение на страницу для ввода номера документа.
        self.return_to_input_document_number()
        return data

    def process_get_data_on_document(self):
        data_from_web = self._get_data_on_document()
        if data_from_web:
            self.document.save_attrs_from_scrapper(data_from_web)
            self.browser_worker.switch_to_tab(self.browser_worker.tabs['rusprofile'])
            self.get_addresses_from_rusprofile_and_make_decision_about_matching()
            self.browser_worker.switch_to_tab(self.browser_worker.tabs['gost'])
            self.check_the_validity_of_all_gost_numbers()


class FSACertificateScrapper(FSADeclarationScrapper):

    def __init__(self, browser_worker, document):
        super().__init__(browser_worker, document)
        self.browser_worker.switch_to_tab(self.browser_worker.tabs['certificate'])

    def return_to_input_document_number(self, xpath=FsaXPaths.RETURN_BACK_CERTIFICATION.value):
        """ Вернуться на страницу для ввода номера. """
        time.sleep(random.randint(1, 3))
        self.browser_worker.wait_and_click_element(xpath)

    def get_data_from_one_chapter(self, data: dict, chapter_name: str) -> dict:
        """ Собрать данные с одной главы. """
        data = super().get_data_from_one_chapter(data, chapter_name)
        if chapter_name in {'applicant', 'manufacturer'}:
            inner_data = self.get_inner_elements_from_page(chapter_name)
            data.update(inner_data)
        return data

    def get_inner_elements_from_page(self, chapter: str) -> dict:
        """Собрать внутренние элементы на веб-странице. """
        inner_elements = {}
        self.browser_worker.wait_until_all_elements_located_by_class('card-edit-row__content')
        keys = self.browser_worker.find_elements_by_class('card-edit-row__header')
        values = self.browser_worker.find_elements_by_class('card-edit-row__content')
        for key, value in zip(keys, values):
            inner_elements[key.text + ' ' + chapter] = value.text
        return inner_elements


class SgrScrapper(BaseScrapper):
    """ Класс для сбора данных по СГР. """
    def __init__(self, browser_worker, document: Document):
        super().__init__(browser_worker, document)
        self.change_letter_in_number()
        self.browser_worker.switch_to_tab(self.browser_worker.tabs['nsi'])

    def change_letter_in_number(self):
        self.document.number = self.document.number.replace('E', 'Е')

    def wait_till_page_loaded(self):
        """ Дождаться загрузки страницы - исчезновения элемента: затемнения на дисплее """
        loaded = False
        while not loaded:
            try:
                time.sleep(0.06)
                self.browser_worker.find_an_element_by_class('p-datatable-loading-overlay')
            except NoSuchElementException:
                loaded = True

    def check_no_data_message(self) -> bool:
        """ Проверяем есть ли данные. Если данных нет, то будет соответсвующее
        сообщение на странице. Если сообщение об отсутствии данных не найдено, то продолжить."""
        try:
            data_from_nsi = self.browser_worker.get_text_from_element_by_xpath(
                NSIXPaths.NO_DATA.value)
            if data_from_nsi == 'Нет данных':
                self.document.status_on_site = 'Нет на сайте'
                return True
        except NoSuchElementException:
            return False

    def add_to_document_data_about_org_from_text(self, text: str, type_of_org: str,
                                                 patterns: dict) -> None:
        """ Добавляем данные об организации в зависимости от того, как и что изложено на сайте СГР. """
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

    def get_data_from_nsi_site(self) -> None:
        """Собрать данные по свидетельству о государственной регистрации с сайта nsi.
        Вернет либо словарь, достаточный для добавления и последующей записи, либо None"""
        # Найти и нажать на кнопку фильтра - после которой можно ввести номер СГР
        self.browser_worker.wait_and_click_element(NSIXPaths.FILTER.value)
        # Дождаться возможности ввода номера СГР, ввести и нажать поиск.
        self.browser_worker.input_in_field_and_press_search_button(
            NSIXPaths.INPUT_FIELD.value, self.document.number, NSIXPaths.CHECK_MARK.value)
        self.wait_till_page_loaded()
        no_data = self.check_no_data_message()

        if no_data:
            return None
        self.document.status_on_site = self.browser_worker.get_text_from_element_by_xpath(
            NSIXPaths.STATUS_DOCUMENT.value)
        if self.document.status_on_site != 'подписан и действует':
            return None

        # Добавляем в документы данные по заявителю, производителю, документации и по остальным ключам.
        text_applicant = self.browser_worker.get_text_from_element_by_xpath(NSIXPaths.APPLICANT.value)
        self.add_to_document_data_about_org_from_text(text_applicant, 'applicant', PATTERNS_FOR_NSI)
        text_manufacturer = self.browser_worker.get_text_from_element_by_xpath(NSIXPaths.MANUFACTURER.value)
        self.add_to_document_data_about_org_from_text(text_manufacturer, 'manufacturer', PATTERNS_FOR_NSI)
        self.document.regulatory_document = self.browser_worker.get_text_from_element_by_xpath(
            NSIXPaths.NORMATIVE_DOCUMENTS.value)

    def process_get_data_on_document(self):
        """ Запустить и собрать данные по документу СГР. """
        self.get_data_from_nsi_site()
        self.browser_worker.switch_to_tab(self.browser_worker.tabs['rusprofile'])
        self.get_addresses_from_rusprofile_and_make_decision_about_matching()
        self.browser_worker.switch_to_tab(self.browser_worker.tabs['gost'])
        self.check_the_validity_of_all_gost_numbers()
