"""
dataclass Document - используется для хранения данных по каждому документу.

  @dataclass
  class Document: - Класс для хранения данных по документу.

    def save_attrs_from_gold() - преобразовать и сохранить данные из собранных в ГОЛД
    def save_attrs_from_parser() - сохранить данные из собранных в интернете.
    def save_attrs_from_prev_checked() - Сохранить данные из просмотренных ранее документов.
    def convert_document_to_pd_series() - Конвертировать данные из документа в pd.Series

"""
from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class Document:
    """ Класс для хранения данных по документу. """
    # Атрибуты с данными из ГОЛД
    matrix_number: int = 0
    product_code: int = 0
    product_name: str = ''
    number: str = ''
    expiration_date: str = ''
    manufacturer: str = ''
    applicant: str = ''
    # Атрибуты с данными из интернет-ресурса
    status_on_site: str = ''
    ogrn_applicant: str = ''
    ogrn_manufacturer: str = ''
    address_applicant: str = ''
    address_manufacturer: str = ''
    regulatory_document: str = ''
    standard: str = ''
    # Атрибуты с данными с сайта rusprofile
    address_applicant_from_web: str = ''
    address_manufacturer_from_web: str = ''
    # Статус ГОСТ
    status_of_regulatory_documentation: str = ''
    # Атрибуты с дополнительной логикой.
    address_matching: str = ''
    inspector: str = 'Код'
    date_of_inspection: str = ''

    def save_attrs_from_gold(self, doc_data_from_gold: dict) -> None:
        """ Преобразовать и сохранить данные из собранных в ГОЛД. """
        self.matrix_number = doc_data_from_gold.get('Порядковый номер АМ', 0)
        self.product_code = doc_data_from_gold.get('Код товара', 0)
        self.product_name = doc_data_from_gold.get('Наименование товара', '')
        self.number = doc_data_from_gold.get('ДОС', '').strip()
        self.expiration_date = doc_data_from_gold.get('Дата окончания', '')
        if isinstance(self.expiration_date, str):
            self.expiration_date = self.expiration_date[:6] + '20' + self.expiration_date[6:]
        self.manufacturer = doc_data_from_gold.get('Изготовитель', '')
        self.applicant = doc_data_from_gold.get('Заявитель', '')

    def save_attrs_from_parser(self, doc_data_from_web: dict) -> None:
        """ Сохранить данные из собранных парсером в интернете. """
        self.ogrn_applicant = doc_data_from_web.get(
            'Основной государственный регистрационный '
            'номер юридического лица (ОГРН) applicant', 'Нет ОГРН')
        self.ogrn_manufacturer = doc_data_from_web.get(
            'Основной государственный регистрационный '
            'номер юридического лица (ОГРН) manufacturer', 'Нет ОГРН')
        self.address_applicant = doc_data_from_web.get('Адрес места нахождения applicant', '')
        self.address_manufacturer = doc_data_from_web.get('Адрес места нахождения manufacturer', '')
        self.regulatory_document = doc_data_from_web.get('Наименование документа product', '')
        self.standard = doc_data_from_web.get('Обозначение стандарта, нормативного документа', '')

    def save_attrs_from_prev_checked(self, doc_data_from_web: dict) -> None:
        """ Сохранить данные из просмотренных ранее документов. """
        self.save_attrs_from_parser(doc_data_from_web)
        self.status_on_site = doc_data_from_web.get('Статус на сайте', '')
        self.ogrn_applicant = doc_data_from_web.get(
            'ОГРН заявителя', 'Нет ОГРН')
        self.ogrn_manufacturer = doc_data_from_web.get(
            'ОГРН изготовителя', 'Нет ОГРН')
        self.address_applicant = doc_data_from_web.get('Адрес заявителя', '')
        self.address_manufacturer = doc_data_from_web.get('Адрес изготовителя', '')
        self.regulatory_document = doc_data_from_web.get('Наименование документа product', '')
        self.standard = doc_data_from_web.get('Обозначение стандарта, нормативного документа', '')
        self.address_applicant_from_web = doc_data_from_web.get('Адрес заявителя ЕГРЮЛ')
        self.address_manufacturer_from_web = doc_data_from_web.get('Адрес изготовителя ЕГРЮЛ')
        self.status_of_regulatory_documentation = doc_data_from_web.get('Статус НД')
        self.address_matching = doc_data_from_web.get('Соответствие адресов с ЕГРЮЛ')
        self.inspector = doc_data_from_web.get('ФИО')
        self.date_of_inspection = doc_data_from_web.get('Дата проверки')

    def convert_to_pd_series(self) -> pd.Series:
        """ Конвертировать данные из документа в pd.Series """
        data = {
            'Порядковый номер АМ': self.matrix_number,
            'Код товара': self.product_code,
            'Наименование товара': self.product_name,
            'ДОС': self.number,
            'Дата окончания': self.expiration_date,
            'Изготовитель': self.manufacturer,
            'Заявитель': self.applicant,
            'Дата проверки': datetime.now().strftime('%d.%m.%Y-%H.%M.%S'),
            'Статус на сайте': self.status_on_site,
            'ОГРН заявителя': self.ogrn_applicant,
            'ОГРН изготовителя': self.ogrn_manufacturer,
            'Соответствие адресов с ЕГРЮЛ': self.address_matching,
            'Адрес заявителя': self.address_applicant,
            'Адрес заявителя ЕГРЮЛ': self.address_applicant_from_web,
            'Адрес изготовителя': self.address_manufacturer,
            'Адрес изготовителя ЕГРЮЛ': self.address_manufacturer_from_web,
            'Статус НД': self.status_of_regulatory_documentation,
            'ФИО': self.inspector,
        }
        return pd.Series(data)
