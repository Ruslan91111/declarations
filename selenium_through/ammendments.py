"""Корректировка словаря данных, полученных с веба, для сравнения"""


def amend_web_data(web_data: dict) -> dict:
    """Внести коррективы в словарь данных из WEB перед сравнением."""
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
            'Наименование документа product')
    elif 'Наименование документа product' in web_data:
        web_data['Наименование документа'] = web_data.pop(
            'Наименование документа product')

    return web_data
