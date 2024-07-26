"""

Функции:
    - create_intern_df:
        Создать файл с международными декларациями

    - find_required_doc:
        Проверяет, соответствует ли документ паттерну международного документа.

    - determine_country_of_doc:
        Определяет страну документа из его номера.

"""
import re

import pandas as pd


def create_intern_xlsx(input_xlsx: str, output_xlsx: str):
    """ Создать файл с международными декларациями """
    df = pd.read_excel(input_xlsx)
    # Паттерн для фильтрации
    pattern = r'ЕАЭС (№ ?)?(KZ|BY|KG|AM)[\w\/\.\\s-]+'
    # Фильтрация DataFrame
    filtered_df = df[df['ДОС'].str.contains(pattern)]
    # Запись отфильтрованного DataFrame
    filtered_df.to_excel(output_xlsx, index=False)
    print(f'Международные декларации записаны в отдельный файл {output_xlsx}')


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
