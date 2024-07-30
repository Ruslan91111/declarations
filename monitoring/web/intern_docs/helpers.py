"""

Функции:

    - find_required_doc:
        Проверяет, соответствует ли документ паттерну международного документа.

    - determine_country_of_doc:
        Определяет страну документа из его номера.

"""
import re


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
