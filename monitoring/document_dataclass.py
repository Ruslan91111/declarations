""" dataclass - Document
для хранения данных по каждому документу, экземпляр создается и используется внутри
класса scrapper
"""
from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class Document:
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
    rusprofile_address_applicant: str = ''
    rusprofile_address_manufacturer: str = ''
    # Статус ГОСТ
    status_of_regulatory_documentation: str = ''
    # Атрибуты с дополнительной логикой.
    address_matching: str = ''
    inspector: str = 'Код'
    date_of_inspection: str = ''

    def convert_and_save_attrs_from_gold(self, doc_data_from_gold: dict) -> None:
        """ Сохранить данные из собранных в ГОЛД. """
        self.matrix_number = doc_data_from_gold.get('Порядковый номер АМ', 0)
        self.product_code = doc_data_from_gold.get('Код товара', 0)
        self.product_name = doc_data_from_gold.get('Наименование товара', '')
        self.number = doc_data_from_gold.get('ДОС', '').strip()
        self.expiration_date = doc_data_from_gold.get('Дата окончания', '')
        if isinstance(self.expiration_date, str):
            self.expiration_date = self.expiration_date[:6] + '20' + self.expiration_date[6:]
        self.manufacturer = doc_data_from_gold.get('Изготовитель', '')
        self.applicant = doc_data_from_gold.get('Заявитель', '')

    def save_attrs_from_scrapper(self, doc_data_from_web: dict) -> None:
        """ Сохранить данные из собранных в интернете. """
        self.ogrn_applicant = doc_data_from_web.get(
            'Основной государственный регистрационный номер юридического лица (ОГРН) applicant', 'Нет ОГРН')
        self.ogrn_manufacturer = doc_data_from_web.get(
            'Основной государственный регистрационный номер юридического лица (ОГРН) manufacturer', 'Нет ОГРН')
        self.address_applicant = doc_data_from_web.get('Адрес места нахождения applicant', '')
        self.address_manufacturer = doc_data_from_web.get('Адрес места нахождения manufacturer', '')
        self.regulatory_document = doc_data_from_web.get('Наименование документа product', '')
        self.standard = doc_data_from_web.get('Обозначение стандарта, нормативного документа', '')

    def convert_document_to_pd_series(self) -> pd.Series:
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
            'Адрес заявителя ЕГРЮЛ': self.rusprofile_address_applicant,
            'Адрес изготовителя': self.address_manufacturer,
            'Адрес изготовителя ЕГРЮЛ': self.rusprofile_address_manufacturer,
            'Статус НД': self.status_of_regulatory_documentation,
            'ФИО': self.inspector,
        }
        return pd.Series(data)
