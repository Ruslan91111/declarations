"""Модуль для работы с GOLD.

Запускает ГОЛД, считывает номера кодов товаров и их наименования, вводит коды
товаров поочередно в ГОЛД, выбирает тип документа, кликает по нему,
сохраняет из выбранной карточки документа изготовителя и номер декларации или
иного документа. Добавляет тип документа, номер документа и изготовителя в DataFrame.
DataFrame до проверки всего документа сохраняет в файл './temp_df.xlsx'.
Номера просмотренных кодов товаров сохраняются в файл 'viewed_products.txt',
который также считывается перед проверкой.

"""
import os
import time
import pandas as pd
import pyautogui
import pytesseract
import pyperclip
import psutil
import openpyxl

from config import LOGIN_VALUE, PASSWORD_VALUE
from selenium_through.supporting_functions import (read_viewed_numbers_of_documents,
                                                   write_viewed_numbers_to_file)


# КОНСТАНТЫ - скриншоты: открыть ГОЛД и прокликать по меню.
FIREFOX_ICON = r'.\screenshots\appicon.png'
FIREFOX_ICON_PANEL = r'.\screenshots\firefox_icon_panel.png'
MENU_ICON = r'.\screenshots\menu_icon.png'
GOLD_LOADED = r'.\screenshots\gold_loaded.png'
BACK_ICON_GOLD = r'.\screenshots\back_icon_gold.png'
STOCK_11 = r'.\screenshots\gold_11.png'
LOGIN_PLACE = r'.\screenshots\login_place.png'
PASSWORD_PLACE = r'.\screenshots\password_place.png'
LOGIN = r'.\screenshots\enter.png'
MENU_33 = r'.\screenshots\menu_33.png'
MENU_33_4 = r'.\screenshots\33-4.png'

# Для работы с конкретными карточками деклараций.
PRODUCT_INPUT = r'.\screenshots\product_input_number.png'
DECLARATION_CARD = r'.\screenshots\declaration_card.png'  # Карточка товара.
REG_NUMBER_FIELD = r'.\screenshots\reg_numb.png'
MANUFACTURER_FIELD = r'.\screenshots\manufacturer_field.png'

# Папка со статусами документов.
THE_DECLARATIONS_STATUS = {
    'Действующая декларация ': r'.\screenshots\the_declarations_status\valid_declaration_green.png',
    'Действующая декларация': r'.\screenshots\the_declarations_status\valid_declaration_transp.png',
    'Действующее письмо': r'.\screenshots\the_declarations_status\valid_letter.png',
    'Действующий сертификат': r'.\screenshots\the_declarations_status\valid_certification.png',
    'Подходящий сертификат': r'.\screenshots\the_declarations_status\approaching_certification.png',
    'Просроченное письмо': r'.\screenshots\the_declarations_status\overdue_letter.png',
    'Просроченная декларация': r'.\screenshots\the_declarations_status\overdue_declaration.png'
}
# Скриншот загрузки данных
LOADING_PRODUCT = r'.\screenshots\loading_product.png'
# Серое сообщение "Данные не найдены".
DATA_NOT_FOUND = r'.\screenshots\data_not_found.png'
OK_DATA_NOT_FOUND = r'.\screenshots\ok_data_not_found.png'

# Иные КОНСТАНТЫ
# Для сохранения DataFrame в .xlsx файл до окончания полной проверки.
TEMP_DF = r'.\temp_df.xlsx'
# Просмотренные номера деклараций
VIEWED_GOLD_PRODUCTS = r'.\viewed_products.txt'

# Итоговый файл с результатами мониторинга
RESULT_FILE = r'.\Мониторинг АМ (2023).xlsx'

# Процессы для поиска в Windows.
FIREFOX_PROC = "firefox.exe"
JAVA_PROC = "java.exe"

# Путь к файлам Tesseract OCR и poppler
PATH_TO_TESSERACT = r'C:\Users\RIMinullin\AppData\Local\Programs\Tesseract-OCR\tesseract'
pytesseract.pytesseract.tesseract_cmd = PATH_TO_TESSERACT
path_to_poppler = r'../poppler-23.11.0/Library/bin'


# Функции работы со скриншотами.
# ==================================================================
def wait_screenshot(image_path, timeout=5, confidence=.7):
    """ Ожидать появление скриншота в течение заданного времени. """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            time.sleep(0.03)
            image = pyautogui.locateOnScreen(image_path, confidence=confidence)
            # Если скриншот найден кликнуть по нему и вернуть его.
            if image:
                pyautogui.click(image)
                return image
        except pyautogui.ImageNotFoundException:
            pass
    raise Exception(f'{image_path} скриншот не найден')


def handle_error(timeout=1):
    """ Нажать 'ОК' на сообщение об ошибке - отсутствии данных. """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            time.sleep(0.2)
            image = pyautogui.locateOnScreen(DATA_NOT_FOUND, confidence=.7)
            # Если найдено сообщение об ошибке, то ищем "ОК" и кликаем по нему.
            if image:
                ok = pyautogui.locateOnScreen(OK_DATA_NOT_FOUND, confidence=.7)
                pyautogui.click(ok)
                return True
        except pyautogui.ImageNotFoundException:
            pass
    return None


def waiting_disappear_screenshot(screenshot, timeout=10):
    """ Ждем пока скриншот исчезнет с экрана. """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            time.sleep(0.05)
            # Ищем скриншот.
            image = pyautogui.locateOnScreen(screenshot, confidence=.7)
            # Если найден, то продолжаем его находить.
            if image:
                pass
        except pyautogui.ImageNotFoundException:
            return None


def input_in_gold_by_screenshot(screenshot, string_for_input, x_offset):
    """Ввести строку в поле голда. Поиск по скриншоту, смещение по оси x"""
    # Находим положение нужного скриншота(слова).
    input_number = wait_screenshot(screenshot)
    pyautogui.moveTo(input_number)
    x, y = pyautogui.position()
    pyautogui.moveTo(x + x_offset, y)  # Смещаемся по оси x вправо от скриншота, в поле для ввода.
    pyautogui.doubleClick()
    pyautogui.press('backspace')  # Очистить поле
    pyperclip.copy(string_for_input)
    pyautogui.hotkey('ctrl', 'v')  # Вставить значение.


# Функции открытия GOLD.
# ==================================================================
def check_program(process):
    """Проверяет запущен ли процесс в ОС"""
    for proc in psutil.process_iter():  # Перебираем текущие процессы.
        name = proc.name()
        if name == process:
            return proc  # Возвращаем работающий процесс
    return None


def activate_current_firefox(proc):
    """ Раскрыть окно запущенного firefox. """
    if proc is not None:
        wait_screenshot(FIREFOX_ICON_PANEL, confidence=0.9)
        return True
    return None


def activate_current_java(proc):
    """ Раскрыть окно запущенного java."""
    if proc is not None:
        try:
            wait_screenshot(MENU_ICON, confidence=0.9)
        except:
            return None
        return True
    return None


def launch_firefox_for_gold_from_desktop():
    """Найти на рабочем столе иконку firefox и открыть ее."""
    time.sleep(1)
    pyautogui.hotkey('Win', 'd')  # Свернуть все окна.
    wait_screenshot(FIREFOX_ICON)  # Открыть ГОЛД через иконку на раб.столе.
    pyautogui.press('enter')


def activate_or_launch_gold():
    """ Проверка запущенных процессов firefox и java и их
    активирование(раскрытие окон) или запуск Голда по новой, с иконки на рабочем столе."""
    # Запущен ли процессы: firefox и java
    firefox_proc = check_program(FIREFOX_PROC)
    java_proc = check_program(JAVA_PROC)
    # Активны ли окна.
    active_firefox = activate_current_firefox(firefox_proc)
    active_java = activate_current_java(java_proc)

    # Если активны окна firefox и java
    if active_firefox and active_java:
        try:
            wait_screenshot(MENU_33_4)
        except:
            wait_screenshot(MENU_33)
            wait_screenshot(MENU_33_4)

    # Если запущен только firefox
    elif active_firefox and not active_java:
        try:
            wait_screenshot(DECLARATION_CARD)  # Если найдет значит код в карточке товара.
            pyautogui.hotkey('Alt', 'b')
        except:
            pass

    elif not active_firefox and not active_java:
        launch_firefox_for_gold_from_desktop()
        navigate_menu_until_product_number_input()


# Конкретные функции для работы с товарами и декларациями.
# ==================================================================
def navigate_menu_until_product_number_input():
    """ В окне firefox открыть меню ГОЛД и пройти по нему
    до ввода номера товара, до пункта 33.4 """
    wait_screenshot(GOLD_LOADED)  # Проверка загрузки и активности firefox.
    wait_screenshot(STOCK_11)  # Кликнуть по stock 11
    input_in_gold_by_screenshot(LOGIN_PLACE, LOGIN_VALUE, 20)  # Ввести логин.
    input_in_gold_by_screenshot(PASSWORD_PLACE, PASSWORD_VALUE, 20)  # Ввести пароль.
    wait_screenshot(LOGIN)  # Войти.
    menu_33 = wait_screenshot(MENU_33)  # 33 пункт меню
    pyautogui.doubleClick(menu_33)
    menu_33_4 = wait_screenshot(MENU_33_4)  # 33.4 пункт меню
    pyautogui.doubleClick(menu_33_4)


def _pick_valid_declaration(image_paths, confidence=0.7):
    """ После ввода кода товара, дождаться появления списка деклараций,
    выбрать действующее из списка. Если действующая не найдена
    вернуть словарь data со значениями по умолчанию. """

    data = {'Изготовитель': 'не найдено',
            'ДОС': 'не найдено',
            'Тип выбранного документа': 'Нет документа'}

    # Проверка на ошибку "нет данных".
    error = handle_error()

    if error:
        # Если ошибка данных, вернуть словарь со значениями не найдено.
        return data

    for key, value in image_paths.items():  # Ищем поочередно скриншоты из папки.
        try:
            found_screenshot = wait_screenshot(value, timeout=1, confidence=confidence)

            if found_screenshot is not None:
                pyautogui.doubleClick(found_screenshot)
                # Возвращаем координаты бокса изображения и название документа, по которому выбрали.
                return found_screenshot, key
        except:
            pass
    return data  # Вернуть словарь со значениями не найдено.


def input_number_and_pick_declaration(product_code: str):
    """ Ввести код товара, нажать поиск, выбрать декларацию из списка. """

    # Ввести номер кода товара
    input_in_gold_by_screenshot(PRODUCT_INPUT, product_code, 120)
    pyautogui.hotkey('Alt', 't')  # Поиск.
    waiting_disappear_screenshot(LOADING_PRODUCT)  # Дождаться, когда прогрузится страница

    # Щелкнуть по декларации из списка. Ищем по скриншотам в папке.
    valid_declaration = _pick_valid_declaration(THE_DECLARATIONS_STATUS)

    # Если не один из скриншотов не найден возвращает словарь со значениями "не найдено"
    if type(valid_declaration) is dict:
        return valid_declaration

    # Иначе кликаем по найденному скриншоту.
    pyautogui.moveTo(valid_declaration[0])
    pyautogui.click()
    # Ждем скриншот карточки товара, чтобы понять, что мы провалились в нее.
    wait_screenshot(DECLARATION_CARD)
    return valid_declaration[1]


def take_product_data_from_fields(product_code: str) -> dict:
    """Найти место для ввода кода товара. Ввести, кликнуть по документу.
    Сохранить номер Документа(декларации)
    и наименование изготовителя в словарь"""
    data = {}
    # Ввести код и кликнуть по карточке/декларации. Если деклараций не будет или будет
    # ошибка даты данных, то вернется соответсвующий словарь и функция закончится.
    result_of_input_number = input_number_and_pick_declaration(product_code)
    if isinstance(result_of_input_number, dict):
        return result_of_input_number

    # Поля, из которых нужно собрать данные.
    needed_fields = {'REG_NUMBER': REG_NUMBER_FIELD,
                     'MANUFACTURER_FIELD': MANUFACTURER_FIELD}

    for key, value in needed_fields.items():
        field = wait_screenshot(value)  # Ищем скриншот.

        pyautogui.moveTo(field)
        x, y = pyautogui.position()
        pyautogui.moveTo(x + 120, y)  # Смещаемся в поле для ввода
        pyautogui.doubleClick()
        pyautogui.click()

        # Скопировать содержимое поля.
        pyperclip.copy("")
        pyautogui.hotkey('Ctrl', 'c')
        field_value = pyperclip.paste()

        # Заполнить словарь соответствующими значениями.
        if field_value == '' and key == 'REG_NUMBER':
            data['ДОС'] = '-'
        elif field_value and key == 'REG_NUMBER':
            data['ДОС'] = field_value
        elif field_value == '' and key == 'MANUFACTURER_FIELD':
            data['Изготовитель'] = '-'
        elif field_value and key == 'MANUFACTURER_FIELD':
            data['Изготовитель'] = field_value
    data['Тип выбранного документа'] = result_of_input_number
    return data


def check_or_create_temporary_xlsx(temp_df: str) -> str:
    """Проверить есть ли xlsx файл для временного хранения данных,
    если да - открыть его, если нет_ создать."""
    temp_file = temp_df
    if os.path.isfile(temp_file):
        return temp_file
    workbook = openpyxl.Workbook()
    workbook.save(temp_file)
    return temp_file


def add_declaration_number_and_manufacturer(file: str, sheet: str):
    """Основная, связующая функция модуля.
    Добавить в листе мониторинга тип документа,
    номер декларации и изготовителя из ГОЛД."""

    # Просмотренные коды товаров.
    set_of_viewed_numbers = read_viewed_numbers_of_documents(VIEWED_GOLD_PRODUCTS)

    # Читаем проверяемый файл с кодом товара и наименования товара.
    df = pd.read_excel(file, sheet_name=sheet)

    # TEMP_DF - временный файл xlsx, в котором хранятся строки с ДОС и изготовителем.
    temp_df = check_or_create_temporary_xlsx(TEMP_DF)

    if temp_df is None:  # Если файл пустой, создаем DataFrame.
        new_df = pd.DataFrame(columns=[
            'Код товара', 'Наименование товара',
            'Тип выбранного документа', 'ДОС', 'Изготовитель'])
    else:
        new_df = pd.read_excel(temp_df)

    # Запустить ГОЛД.
    activate_or_launch_gold()
    count = 0  # Для количества обработанных кодов товаров за вызов функции.
    try:
        # Перебираем построчно данные из excel.
        for index, row in df.iterrows():
            # Читаем номер товара с листа.
            product_number = row.loc['Код товара']
            # Проверяем не просматривали ли его ранее
            if product_number in set_of_viewed_numbers:
                pass
            # Если не просматривали.
            else:
                data_from_gold = take_product_data_from_fields(product_number)
                new_ser = pd.Series([data_from_gold['ДОС'],
                                     data_from_gold['Изготовитель'],
                                     data_from_gold['Тип выбранного документа']],
                                    index=data_from_gold.keys())
                # Новый Series на 5 колонок с типом документа, ДОС и изготовителем
                new_row = row._append(new_ser)
                # Добавляем в DataFrame
                new_df = new_df._append(new_row, ignore_index=True)
                # Возврат к вводу кода товара в ГОЛД.
                pyautogui.hotkey('Alt', 'b')
                # Добавляем в просмотренне
                set_of_viewed_numbers.add(product_number)
                count += 1
    except:
        screenshot = pyautogui.screenshot()
        screenshot.save(r".\screenshots\errors\error_{}.png".format(product_number))
        print('Произошла ошибка.\n', 'Количество обработанных в ГОЛД', count)
        raise Exception

    finally:
        # Записать DataFrame во временный xlsx файл.
        new_df.to_excel(temp_df, index=False)
        # А просмотренные коды товаров в текстовой файл.
        write_viewed_numbers_to_file(VIEWED_GOLD_PRODUCTS, set_of_viewed_numbers)


def launch_gold_module(attempts_for_range):
    """Запустить код из модуля."""
    for _ in range(attempts_for_range):
        try:
            all = time.time()
            add_declaration_number_and_manufacturer(RESULT_FILE, 'декабрь')
        except:
            print(time.time() - all)


if __name__ == '__main__':
    launch_gold_module(4)
