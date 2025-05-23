"""
Модуль с классами и функциями для получения адресов юридических лиц с вебсайтов
и их проверки на соответствие.

    Функции:
        - check_downloading_file:
            проверить, что в директории нет активных загрузок.

        - get_text_from_pdf:
            вернуть строкой весь текст из файла формата pdf.

        - name_of_downloaded_file:
            функция для получения последнего загруженного файла в директории загрузок

    Классы:
        - BaseAddressChecker(ABC):
            базовый абстрактный класс для классов проверки адресов.

        - RusprofileAddressChecker(BaseAddressChecker):
            класс для сбора данных с сайта rusprofile.

        - EgrulAddressChecker(BaseAddressChecker):
            класс для сбора данных с сайта egrul.
"""
import os
import re
import time
from abc import ABC, abstractmethod

import PyPDF2

from common.constants import (RusProfileXPaths, REMOVE_ADDRESS_PARTS,
                              EgrulXPaths, PATH_TO_DOWNLOAD_DIR)
from common.file_worker import random_delay


def check_downloading_file(path_to_download_dir: str = PATH_TO_DOWNLOAD_DIR,
                           time_for_loading: int = 20):
    """ Проверить, что в директории нет активных загрузок. """
    time.sleep(.5)
    all_loaded = False
    start_of_checking = time.time()
    while not all_loaded and time.time() - start_of_checking < time_for_loading:
        types_of_file = set()
        for file_name in os.listdir(path_to_download_dir):
            types_of_file.add(file_name[file_name.rfind('.')+1:])
        if not 'crdownload' in types_of_file:
            all_loaded = True
    if not all_loaded:
        raise Exception('Файл не загружен')
    return True


def get_text_from_pdf(pdf_file: str) -> str:
    """ Вернуть строкой веь текст из файла формата pdf. """
    if os.path.exists(pdf_file):
        with open(pdf_file, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            pdf_text = ""
            for i in range(2):
                pdf_text += reader.pages[i].extract_text()
        return pdf_text


def name_of_downloaded_file(download_path: str) -> str | None:
    """ Функция для получения последнего загруженного файла в директории загрузок """
    files = [file for file in os.listdir(download_path)
             if os.path.isfile(os.path.join(download_path, file))]
    files = sorted(files, key=lambda x: os.path.getmtime(
        os.path.join(download_path, x)), reverse=True)
    return files[0] if files else None


class BaseAddressChecker(ABC):
    """ Базовый абстрактный класс для классов проверки адресов.  """

    def __init__(self, browser_worker, document, ogrn_and_addresses):
        self.browser_worker = browser_worker
        self.document = document
        self.ogrn_and_addresses = ogrn_and_addresses

    @abstractmethod
    def get_address_from_web(self, ogrn: str, address_field: str) -> None:
        """ Получить и сохранить в Document адрес из интернет ресурса."""
        pass

    def compare_the_addresses(self) -> None:
        """ Сравнить строки - адреса: 1) с сайта и 2) rusprofile.
        Предварительно из строк(адресов) убрать обозначения, наподобие: ул. гор. и т.д.
        затем сравнить что останется в строках. """
        elements_for_remove = REMOVE_ADDRESS_PARTS

        def _prepare_address(string: str) -> list:
            """Подготовить адреса перед сравнением - убрать сокращения,
            лишние знаки, разбить в словарь по символам."""
            string = (string.upper().replace('.', ' ').replace('(', '').
                      replace(')', '').replace(',', ' '))

            # Убираем сокращения и обозначения.
            for elem in elements_for_remove:
                string = string.replace(elem, ' ')
            return sorted(string.replace(' ', ''))

        # Привести адреса к единому виду - отсортированным спискам строк.
        appl_address = _prepare_address(self.document.address_applicant)
        web_appl_address = _prepare_address(self.document.address_applicant_from_web)
        manuf_address = _prepare_address(self.document.address_manufacturer)
        web_manuf_address = _prepare_address(self.document.address_manufacturer_from_web)

        # Сделать и внести в словарь вывод о соответствии адресов.
        if appl_address == web_appl_address and manuf_address == web_manuf_address:
            self.document.address_matching = 'Соответствуют'
        else:
            self.document.address_matching = 'Не соответствуют'

    def get_both_addresses_and_compare(self):
        """ Основной метод для получения адресов организация и получении вывода
        о соответствии адресов. """
        self.get_address_from_web(self.document.ogrn_applicant, 'address_applicant_from_web')
        self.get_address_from_web(self.document.ogrn_manufacturer, 'address_manufacturer_from_web')
        self.compare_the_addresses()


class RusprofileAddressChecker(BaseAddressChecker):
    """ Класс для сбора данных с сайта rusprofile. """
    def check_no_organisation(self, timeout=2):
        """ Проверить наличие на странице текста об отсутствии по указанному ОГРН
        юрлица или ИП."""
        start = time.time()
        while time.time() - start < timeout:
            no_organisation = self.browser_worker.find_all_elems_by_xpath(
                RusProfileXPaths.NO_ORGANISATION_FOUND.value)
            if no_organisation:
                return True
        return False

    def get_address_from_web(self, ogrn: str, address_field: str) -> None:
        """ Получить адрес с сайта https://www.rusprofile.ru/ по ОГРН.
        Если ОГРН отсутствует, то записать соответствующее сообщение."""

        if not ogrn or ogrn == 'Нет ОГРН':
            setattr(self.document, address_field, 'Нет ОГРН')
            return None

        # Проверка не проверяли ли данный огрн ранее в процессе мониторинга.
        if ogrn in self.ogrn_and_addresses:
            address = self.ogrn_and_addresses[ogrn]

        else:
            random_delay()
            self.browser_worker.input_in_field(RusProfileXPaths.INPUT_FIELD.value, ogrn)
            random_delay()
            self.browser_worker.wait_and_click_elem(RusProfileXPaths.SEARCH_BUTTON.value)
            no_organisation = self.check_no_organisation()

            if no_organisation:
                address = 'С данным ОГРН не найдено организаций и индивидуальных предпринимателей'
            else:
                address = self.browser_worker.get_text_by_xpath(
                    RusProfileXPaths.ADDRESS_PLACE.value)
                self.ogrn_and_addresses[ogrn] = address

        setattr(self.document, address_field, address if address else 'Адрес не найден')


class EgrulAddressChecker(BaseAddressChecker):
    """ Класс для сбора данных с сайта egrul. """

    def download_pdf_file(self, ogrn: str) -> None:
        """ Ввести номер - огрн на сайте, кликнуть по 'Получить выписку'. """
        self.browser_worker.input_in_field(EgrulXPaths.INPUT_FIELD.value, ogrn)
        self.browser_worker.wait_and_click_elem(EgrulXPaths.SEARCH_BUTTON.value)
        time.sleep(1)
        self.browser_worker.wait_and_click_elem(EgrulXPaths.GET_RECORD.value)
        check_downloading_file()

    def get_address_from_pdf(self, download_path=PATH_TO_DOWNLOAD_DIR) -> str:
        """ Получить адрес юридического лица из pdf файла. """
        downloaded_file = name_of_downloaded_file(PATH_TO_DOWNLOAD_DIR)
        downloaded_file = download_path + '\\' + downloaded_file

        text_from_pdf = get_text_from_pdf(downloaded_file)
        address_pattern = r'(Адрес юридического лица)([\s\S]*?)(\d\s?ГРН)'
        address_value = (re.search(address_pattern, text_from_pdf).
                         group(2).strip(' ').replace('\n', ''))
        os.remove(downloaded_file)  # Удалить файл
        return address_value

    def get_address_from_web(self, ogrn: str, address_field: str) -> None:
        """ Получить адрес с сайта https://www.rusprofile.ru/ по ОГРН.
        Если ОГРН отсутствует, то записать соответствующее сообщение."""

        if not ogrn or ogrn == 'Нет ОГРН':
            setattr(self.document, address_field, 'Нет ОГРН')
            return None

        # Проверка не проверяли ли данный огрн ранее в процессе мониторинга.
        if ogrn in self.ogrn_and_addresses:
            address = self.ogrn_and_addresses[ogrn]

        else:
            self.download_pdf_file(ogrn)
            address = self.get_address_from_pdf()
            self.ogrn_and_addresses[ogrn] = address

        setattr(self.document, address_field, address if address else 'Адрес не найден')
