"""
Модуль содержит функцию, которая в ГОЛД перебирает и сохраняет в словарь коды и
наименования поставщиков. В последующем записывает их в файл json формата.
"""

import json

import pyautogui
import pyperclip
import time

from monitoring.gold_data_manager import (wait_and_click_screenshot, APPLICANT_CODE,
                                          activate_current_gold_or_launch_new_gold,
                                          input_in_gold_by_screenshot,
                                          PRODUCT_INPUT,
                                          waiting_disappear_screenshot,
                                          LOADING_PRODUCT,
                                          handle_error_no_data_in_web,
                                          search_coords_of_all_declarations_on_page_in_gold,
                                          DECLARATION_CARD)

PRODUCT_NUMBER = '2000269222'
APPLICANTS_CODES_AND_NAME = 'dict_applicant.json'


def get_all_applicant_and_codes_from_gold():
    """
    Сохранить в json файл словарь с кодами предприятий и их наименования.

    Коды предприятий и их наименования берутся из программы ГОЛД с карточки товара.
    Находится поле "Держ. серт" кликается значение, далее нажатием стрелки вниз перебираются
    значения и сохраняются в словарь, который по окончании записывается в словарь.
    Словарь по окончании записывается в файл формата json.
    В среднем около 6500 наименований, обрабатывается за 90 минут.

    """
    # Запустить или раскрыть окно ГОЛД.
    activate_current_gold_or_launch_new_gold()
    # Ввести номер кода товара.
    input_in_gold_by_screenshot(PRODUCT_INPUT, PRODUCT_NUMBER, 120)
    # Нажать поиск.
    pyautogui.hotkey('Alt', 't')
    # Дождаться, загрузки страницы
    waiting_disappear_screenshot(LOADING_PRODUCT)
    # Проверить на наличие сообщения на экране об отсутствии данных.
    error_no_data = handle_error_no_data_in_web()
    if error_no_data:
        print('Нет такого номера товара в ГОЛД. Попробуйте другой.')
        return None

    # Поиск координат документа.
    centres = search_coords_of_all_declarations_on_page_in_gold()
    # Кликаем по первому документу
    pyautogui.doubleClick(centres[0])
    # Дождаться, загрузки страницы
    waiting_disappear_screenshot(LOADING_PRODUCT)
    wait_and_click_screenshot(DECLARATION_CARD)
    # Очищаем буфер под копирование.
    pyperclip.copy("")
    applicant_dict = {}  # Словарь для данных.
    # Кликаем на список поставщиков и их коды.
    wait_and_click_screenshot(APPLICANT_CODE)
    x, y = pyautogui.position()
    pyautogui.moveTo(x + 80, y)
    time.sleep(0.2)
    pyautogui.doubleClick()
    time.sleep(3)

    row_applicant = 'a'  # Переменная для текущего кода и поставщика.
    prev_applicant = ''  # Переменная для хранения предыдущего поставщика.

    try:
        # Берем через цикл с ГОЛД данные о поставщиках и помещаем их в словарь.
        while row_applicant != prev_applicant:
            prev_applicant = row_applicant
            # Копируем текст из поля.
            pyautogui.hotkey('Ctrl', 'c')
            row_applicant = pyperclip.paste()
            list_from_row = row_applicant.split('\t')
            applicant_dict[list_from_row[0]] = list_from_row[1]
            time.sleep(0.2)
            pyperclip.copy("")
            time.sleep(0.2)
            # Переход к следующей позиции в списке поставщиков.
            pyautogui.hotkey('down')

    except Exception:
        print('Произошла ошибка в обработке поставщиков.', Exception)

    finally:
        # Записать в файл JSON
        with open(APPLICANTS_CODES_AND_NAME, 'w') as f:
            json.dump(applicant_dict, f)


# def read_dict_from_json()

if __name__ == '__main__':
    get_all_applicant_and_codes_from_gold()
