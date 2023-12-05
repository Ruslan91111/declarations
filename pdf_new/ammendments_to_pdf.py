"""Дополнительные классы и методы, которые помогут преобразовать данные из ПДФ
в словарь."""
import re

def append_tech_regulations(text_from_pdf: str, dict_from_text: dict):
    """'Технические регламенты' должны включать все TP."""
    start_tech_reg = text_from_pdf.find('ТР ТС')
    end_tech_reg = text_from_pdf.find('Группа продукции')
    value = text_from_pdf[start_tech_reg:end_tech_reg]
    dict_from_text['Технические регламенты'] = value
    return dict_from_text


def append_OGRN_INN(text_from_pdf: str, dict_from_text: dict):
    """Найти и добавить ОГРН с ИНН."""
    # Добавить ОГРН.
    start_ogrn = text_from_pdf.find('(ИНН)') + 5
    end_ogrn = start_ogrn + 13
    ogrn = text_from_pdf[start_ogrn:end_ogrn]
    dict_from_text[('Основной государственный регистрационный '
                    'номер юридического лица (ОГРН)')] = ogrn
    # Добавить ИНН.
    start_inn = end_ogrn + 1
    end_inn = start_inn + 10
    inn = text_from_pdf[start_inn:end_inn]
    dict_from_text[('ИНН')] = inn

    return dict_from_text

def append_address_applicant_and_manufacturer_and_production(text_from_pdf: str, dict_from_text: dict):
    """Adjust value for 'Адрес места нахождения заявителя'"""
    start_address = text_from_pdf.find('Адрес места нахождения') + 23
    end_address = text_from_pdf.find('Адрес', start_address, -1)
    value = text_from_pdf[start_address:end_address]
    dict_from_text['Адрес места нахождения заявителя'] = value.replace('\n', ' ').rstrip(' ')

    start_address_manufacturer = text_from_pdf.find('Адрес места нахождения', end_address, - 1) + 23
    end_address_manufacturer = text_from_pdf.find('Контактные', start_address_manufacturer, -1)
    value = text_from_pdf[start_address_manufacturer:end_address_manufacturer]
    dict_from_text['Адрес места нахождения изготовителя'] = value.replace('\n', ' ').rstrip(' ')

    start_address_implementation = text_from_pdf.find('Адрес места осуществления деятельности') + 39
    end_address_manufacturer = text_from_pdf.find('Контактные', start_address_implementation, -1)
    value = text_from_pdf[start_address_implementation:end_address_manufacturer]
    dict_from_text['Адрес места осуществления деятельности'] = value.replace('\n', ' ').rstrip(' ')

    start_address_production = text_from_pdf.find('Адрес производства продукции') + 29
    end_address_production = text_from_pdf.find('+', start_address_production, -1)
    value = text_from_pdf[start_address_production:end_address_production]
    dict_from_text['Адрес производства продукции'] = value.replace('\n', ' ').rstrip(' ')

    return dict_from_text


def remove_extra_indent(text):
    """Заменить ненужные переносы между предлогами."""
    x = text
    for_range = text.count('о\nсоответствииЕАЭС')
    for i in range(for_range):
        new_text = text.replace('о\nсоответствии', 'о соответствии ')
        text = new_text
    text = text.replace('об\nаккредитованном', 'об аккредитованном')
    return text


def remove_space_in_phone_number(text):
    """Убрать пробелы в '+7 89'"""
    pattern = r'\+7\s(\d{10})'  # Шаблон для поиска номеров в формате +7 1234567890
    text = re.sub(pattern, r'+7\1', text)  # Замена пробела после "+7" на пустой символ
    return text


def remove_substrings(string):
    pattern = (r'(Выписка от \d{2}.\d{2}.\d{4}\. Идентификатор выписки [a-zA-Z0-9-]+)'
               r'|(Страница \d+ Декларации о соответствии)')
    return re.sub(pattern, '', string)


def separate_int_and_str(text: str) -> str:
    """В тексте разделить слова и цифры там, где они написаны слитно."""
    # - (\b\w+) - первая группа символов, которая идет перед датой.
    # \b обозначает границу слова, а \w+ соответствует одному или более буквенно-цифровым символам.
    # - (\d{2}\.\d{2}\.\d{4}\b) - вторая группа символов,
    # которая представляет дату в формате дд.мм.гггг. \d{2} соответствует двум цифрам,
    # \. обозначает точку, а \b обозначает границу слова.
    # Функция re.sub(pattern, repl, text) заменяет все найденные совпадения на \1 \2,
    # где \1 - первая группа символов, а \2 - вторая группа символов, разделенные пробелом.
    pattern = r'(\b\w+)(\d{2}\.\d{2}\.\d{4}\b)'
    repl = r'\1 \2'
    result = re.sub(pattern, repl, text)
    return result


def append_indents_before_contact_and_common(text):
    """Добавить абзац перед 'контактные' и 'общее наименование'"""
    contact_indent = text.find('Контактные')
    text = text[:contact_indent]+'\n'+text[contact_indent:]
    common_indent = text.find('Общее наименование')
    text = text[:common_indent]+'\n'+text[common_indent:]
    return text


def append_code_tn(text: str, dict_from_text: dict):
    start = text.find("Код ТН")
    dict_from_text['Код ТН ВЭД ЕАЭС'] = text[start-11:start-1]
    return dict_from_text


def append_space_after_lab(text: str):
    """Append space after 'лаборатории'"""
    number = text.count('лаборатории')
    start_for_search = 0
    for i in range(number):
        start = text.find('лаборатории', start_for_search, -1)
        end = start + 11
        text = text[:end] + ' ' + text[end:]
        start_for_search = end
    return text


def append_name_of_applicant_and_manufacturer(text: str, dict_from_text: dict):
    """Adjust value for 'Адрес места нахождения заявителя'"""
    start = text.find('Полное наименование юридического лица') + 38
    end = text.find('\n', start, -1)
    value = text[start:end]
    dict_from_text['Полное наименование заявителя'] = value
    start = text.find('Полное наименование юридического лица', end, -1) + 38
    end = text.find('\n', start, -1)
    value = text[start:end]
    dict_from_text['Полное наименование изготовителя'] = value
    return dict_from_text


def append_test_carried(text: str, dict_from_text: dict):
    """Adjust value for 'Испытание продукции'"""
    if dict_from_text['Наименование испытательной лаборатории']:
        dict_from_text['Испытания продукции'] = 'Испытания проводились в аккредитованной в ЕАЭС лаборатории'
        return dict_from_text
    else:
        dict_from_text['Наименование испытательной лаборатории'] = 'Испытания не проводились'

    return dict_from_text


def append_condition_of_storage(text: str, dict_from_text: dict):
    """Adjust value for 'Испытание продукции'"""
    end = text.find('Общие условия хранения продукции')
    start = text.find('\n', end, 1)
    print(text[start:end])

    # dict_from_text['Наименование (обозначение) продукции'] =

    return dict_from_text


