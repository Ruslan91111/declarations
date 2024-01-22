"""Корректировка словаря данных, полученных с веба, для сравнения"""


def amend_web_data_declarations(web_data: dict) -> dict:
    """Внести коррективы в словарь данных из WEB перед сравнением
    для декларации"""

    if 'Адрес места нахождения' in web_data:
        web_data['Адрес места нахождения заявителя'] = web_data.pop('Адрес места нахождения')

    if 'Полное наименование юридического лица applicant' in web_data:
        web_data['Полное наименование юридического лица заявителя'] = web_data.pop(
            'Полное наименование юридического лица applicant')
    elif 'Полное наименование applicant' in web_data:
        web_data['Полное наименование юридического лица заявителя'] = web_data.pop(
            'Полное наименование applicant')

    if 'Полное наименование юридического лица manufacturer' in web_data:
        web_data['Полное наименование изготовителя'] = web_data.pop(
            'Полное наименование юридического лица manufacturer')
    elif 'Полное наименование manufacturer' in web_data:
        web_data['Полное наименование изготовителя'] = web_data.pop(
            'Полное наименование manufacturer')

    if 'Адрес места нахождения manufacturer' in web_data:
        web_data['Адрес места нахождения изготовителя'] = web_data.pop(
            'Адрес места нахождения manufacturer')

    if 'Номер записи в РАЛ испытательной лаборатории' in web_data:
        web_data['Номер аттестата аккредитации испытательной лаборатории'] = web_data.pop(
            'Номер записи в РАЛ испытательной лаборатории')

    if 'Номер документа product' in web_data:
        web_data['Наименование документа'] = web_data.pop(
            'Номер документа product')
    elif 'Наименование документа product' in web_data:
        web_data['Наименование документа'] = web_data.pop(
            'Наименование документа product')

    return web_data


def amend_web_data_certificates(web_data: dict) -> dict:
    """Внести коррективы в словарь данных из WEB перед сравнением.
    Для сертификатов."""

    if 'Полное наименование юридического лица applicant' in web_data:
        web_data['Полное наименование юридического лица'] = web_data.pop(
            'Полное наименование юридического лица applicant')
    elif 'Полное наименование applicant' in web_data:
        web_data['Полное наименование юридического лица'] = web_data.pop(
            'Полное наименование applicant')

    if 'Фамилия руководителя' in web_data:
        web_data['Фамилия руководителя юридического лица'] = web_data.pop(
            'Фамилия руководителя')

    if 'Имя руководителя' in web_data:
        web_data['Имя руководителя юридического лица'] = web_data.pop(
            'Имя руководителя')

    if 'Отчество руководителя' in web_data:
        web_data['Отчество руководителя юридического лица'] = web_data.pop(
            'Отчество руководителя')

    if 'Адрес места нахождения applicant' in web_data:
        web_data['Адрес места нахождения заявителя'] = web_data.pop(
            'Адрес места нахождения applicant')

    if 'Адрес места осуществления деятельности applicant' in web_data:
        web_data['Адрес места осуществления деятельности'] = web_data.pop(
            'Адрес места осуществления деятельности applicant')

    if 'Номер телефона applicant' in web_data:
        web_data['Номер телефона'] = web_data.pop(
            'Номер телефона applicant')

    if 'Адрес электронной почты applicant' in web_data:
        web_data['Адрес электронной почты'] = web_data.pop(
            'Адрес электронной почты applicant')

    if 'Полное наименование юридического лица manufacturer' in web_data:
        web_data['Полное наименование изготовителя'] = web_data.pop(
            'Полное наименование юридического лица manufacturer')
    elif 'Полное наименование manufacturer' in web_data:
        web_data['Полное наименование изготовителя'] = web_data.pop(
            'Полное наименование manufacturer')

    if 'Адрес места нахождения manufacturer' in web_data:
        web_data['Адрес места нахождения изготовителя'] = web_data.pop(
            'Адрес места нахождения manufacturer')

    if 'Адрес производства продукции manufacturer' in web_data:
        web_data['Адрес производства продукции '] = web_data.pop(
            'Адрес производства продукции manufacturer')

    if 'Наименование испытательной лаборатории' in web_data:
        web_data['Наименование лаборатории'] = web_data.pop(
            'Наименование испытательной лаборатории')

    if 'Номер записи в РАЛ испытательной лаборатории' in web_data:
        web_data['Номер записи в РАЛ'] = web_data.pop(
            'Номер записи в РАЛ испытательной лаборатории')

    if 'Бланк сертификата' in web_data:
        web_data['Номер бланка'] = web_data.pop(
            'Бланк сертификата')

    if 'Обозначение стандарта, нормативного документа' in web_data:
        web_data['Наименование документа'] = web_data.pop(
            'Обозначение стандарта, нормативного документа')

    if 'Наименование испытательной лаборатории' in web_data:
        web_data['Испытания продукции'] = 'Да'
    web_data['Испытания продукции'] = 'Нет'

    return web_data
