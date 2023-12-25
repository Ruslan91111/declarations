"""Корректировка словаря данных, полученных с веба, для сравнения"""


def amend_web_data(web_data: dict) -> dict:
    """Внести коррективы в словарь данных из WEB перед сравнением."""

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

    if 'Адрес места нахождения  applicant' in web_data:
        web_data['Адрес места нахождения'] = web_data.pop(
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

    return web_data
