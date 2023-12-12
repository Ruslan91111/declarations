"""
Конвертеры

Содержит функции, приводящие данные из xlsx файла к нужному формату.
"""
from datetime import datetime


def convert_date_format(date_str: str) -> str:
    """Привести строку с датой к определенному виду"""
    # Строку из xlsx вида 2020-10-20 00:00:00 привести к виду 20.10.2020
    try:
        # Преобразование строки в объект datetime
        date = datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S')
        # Преобразование объекта datetime в нужный формат
        formatted_date = date.strftime('%d.%m.%Y')
        return formatted_date
    except ValueError:
        return date_str


def remove_decimal_from_xlsx(number: str):
    """Убрать у числа точку и значения после точки."""
    # В xlsx файле есть поля, где точка с цифрами
    # передается при чтении xlsx файла pandas.
    try:
        return int(float(number))
    except ValueError:
        return number


def amend_phone_number(number: str):
    """Привести разное написание номера мобильного телефона
    к написанию, которое используется в WEB."""
    number = (str(number).replace('\n', '').replace('+', '').replace('-', '').
              replace(' ', '').replace('(', '').replace(')', ''))
    # либо number = re.sub(r'[+\-\s\(\)\n]', '', number)
    first_part = '+7 '
    second_part = number[1:]
    return first_part + second_part


def amend_protocols(protocols: str):
    """'Номер протокола'привести к виду как в WEB версии"""
    protocols = str(protocols).replace(' ', '').replace('\n', ', ')
    return protocols


def amend_date_protocols(protocols: str):
    """'Дата протокола' привести к виду как в WEB версии"""
    protocols = amend_protocols(convert_date_format(protocols))
    return protocols
