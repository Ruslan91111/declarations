"""Корректировка словаря данных, полученных с веба, для сравнения"""


def amend_web_data(web_data):
    """Внести коррективы в словарь данных из WEB перед сравнением."""
    print('before amend', web_data)

    try:
        if 'Адрес места нахождения' in web_data:
            web_data['Адрес места нахождения заявителя'] = web_data.pop('Адрес места нахождения')

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


        if 'Наименование документа custom info' in web_data:
            web_data['Наименование документа'] = web_data.pop(
                'Наименование документа custom info')

    except KeyError as e:
        print(f'Нет поля {str(e)}.')
    print(web_data)
    return web_data
