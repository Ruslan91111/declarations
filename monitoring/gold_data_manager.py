"""Модуль для работы с GOLD.

Запускает ГОЛД, либо активируя работающий процесс, либо запуская сначала
от иконки на рабочем столе. Проходит по всему меню ГОЛД до ввода кода товара,
ставит галочку на 'скрыть просроченные'. Считывает номера кодов товаров и
их наименования из существующего xlsx файла, вводит коды
товаров поочередно в ГОЛД, кликает по каждому действующему документу,
сохраняет из выбранной карточки документа: наименование изготовителя
и номер декларации или иного документа.
Добавляет тип документа, номер документа и изготовителя в DataFrame.
DataFrame сохраняет в файл './temp_df.xlsx'.
Номера просмотренных кодов товаров сохраняются в файл 'viewed_products_in_gold.txt',
который также считывается перед проверкой.

"""
import logging
import os
import time

import cv2
import numpy as np
import openpyxl
import pandas as pd
import pyautogui
import pytesseract
import pyperclip
import psutil
from datetime import datetime

from config import LOGIN_VALUE, PASSWORD_VALUE
from exceptions import ScreenshotNotFoundException, StopIterationExceptionInGold

##################################################################################
# КОНСТАНТЫ - скриншоты
##################################################################################
# открыть ГОЛД и прокликать по меню.
FIREFOX_ICON = r'.\screenshots\appicon3.png'
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
TO_SEAL_OVERDUE = r'.\screenshots\seal_overdue.png'

# Для работы с конкретными карточками деклараций.
PRODUCT_INPUT = r'.\screenshots\product_input_number.png'
DECLARATION_CARD = r'.\screenshots\declaration_card.png'  # Карточка товара.
REG_NUMBER_FIELD = r'.\screenshots\reg_numb.png'
MANUFACTURER_FIELD = r'.\screenshots\manufacturer_field.png'

# Скриншоты для выбора действующих деклараций.
GREEN_DECLARATION = r'.\screenshots\the_declarations_status\valid_declaration_green.png'
GRAY_DECLARATION = r'.\screenshots\the_declarations_status\valid_declaration_transp.png'

# Скриншот загрузки данных
LOADING_PRODUCT = r'.\screenshots\loading_product.png'
# Серое сообщение "Данные не найдены".
DATA_NOT_FOUND = r'.\screenshots\data_not_found.png'
OK_DATA_NOT_FOUND = r'.\screenshots\ok_data_not_found.png'


##################################################################################
# Иные КОНСТАНТЫ
##################################################################################
# Файлы
VIEWED_GOLD_PRODUCTS = r'.\viewed_products_in_gold.txt'  # Просмотренные номера деклараций
TWO_COLUMNS_FILE = r'.\after1.xlsx'  # Итоговый файл с результатами мониторинга
LOGGING_FILE = r'.\monitoring.log'

MONTH = datetime.now().strftime('%B')  # Определяем месяц
FILE_GOLD = r'./gold_data_{}.xlsx'.format(MONTH)
FILE_FOR_TWO_COLUMNS = r'.\two_columns_%s.xlsx' % MONTH

# Процессы для поиска в Windows.
FIREFOX_PROC = "firefox.exe"
JAVA_PROC = "java.exe"

# Путь к файлам Tesseract OCR и poppler
PATH_TO_TESSERACT = r'C:\Users\impersonal\AppData\Local\Programs\Tesseract-OCR\tesseract'
pytesseract.pytesseract.tesseract_cmd = PATH_TO_TESSERACT
path_to_poppler = r'.././poppler-23.11.0/Library/bin'

STARS = '*' * 40


##################################################################################
# Логгирование.
##################################################################################
logging.basicConfig(
    level=logging.INFO,
    filename=LOGGING_FILE,
    filemode="a",
    encoding='utf-8',
    format="%(asctime)s %(levelname)s %(message)s",
)


##################################################################################
# Функции работы со скриншотами.
##################################################################################
def wait_and_click_screenshot(image_path: str,
                              timeout: int = 5,
                              confidence: float = 0.7) -> str | None:
    """ Ожидать появление скриншота в течение заданного времени.
     При обнаружении кликнуть один раз."""
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
    raise ScreenshotNotFoundException(image_path)


def handle_error_no_data_in_web(timeout: int = 1) -> bool | None:
    """ При сообщении об ошибке в виде: 'Отсутствия данных' нажать 'ОК'. """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            time.sleep(0.1)
            image = pyautogui.locateOnScreen(DATA_NOT_FOUND, confidence=.7)
            # Если найдено сообщение об ошибке, то ищем "ОК" и кликаем по нему.
            if image:
                ok = pyautogui.locateOnScreen(OK_DATA_NOT_FOUND, confidence=.7)
                pyautogui.click(ok)
                return True
        except pyautogui.ImageNotFoundException:
            pass
    return None


def waiting_disappear_screenshot(screenshot: str, timeout: int = 10) -> None:
    """ Ждем пока скриншот исчезнет с экрана. """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            time.sleep(0.05)
            # Ищем скриншот.
            image = pyautogui.locateOnScreen(screenshot, confidence=0.7)
            # Если найден, то продолжаем его находить.
            if image:
                pass
        except pyautogui.ImageNotFoundException:
            return None


def input_in_gold_by_screenshot(screenshot: str, string_for_input: str, x_offset: int) -> None:
    """Ввести строку в поле голда. Поиск по скриншоту, смещение по оси x"""
    # Находим положение нужного скриншота(слова).
    input_number = wait_and_click_screenshot(screenshot)
    pyautogui.moveTo(input_number)
    x, y = pyautogui.position()
    pyautogui.moveTo(x + x_offset, y)  # Смещаемся по оси x вправо от скриншота, в поле для ввода.
    pyautogui.doubleClick()
    pyautogui.press('backspace')  # Очистить поле
    pyperclip.copy(string_for_input)
    pyautogui.hotkey('ctrl', 'v')  # Вставить значение.


##################################################################################
# Функции, связанные с открытием GOLD.
##################################################################################
def check_process_in_os(process: str):
    """Проверяет запущен ли процесс в ОС"""
    for proc in psutil.process_iter():  # Перебираем текущие процессы.
        name = proc.name()
        if name == process:
            return proc  # Возвращаем работающий процесс
    return None


def activate_current_firefox(proc) -> bool | None:
    """ Раскрыть окно запущенного firefox. """
    if proc is not None:
        wait_and_click_screenshot(FIREFOX_ICON_PANEL, confidence=0.8)
        return True
    return None


def activate_current_java(proc) -> bool | None:
    """ Раскрыть окно запущенного java."""
    if proc is not None:
        try:
            wait_and_click_screenshot(MENU_ICON, confidence=0.8)
        except ScreenshotNotFoundException:
            return None
        return True
    return None


def launch_firefox_for_gold_from_desktop() -> None:
    """Найти на рабочем столе иконку firefox и открыть ее."""
    time.sleep(1)
    pyautogui.hotkey('Win', 'd')  # Свернуть все окна.
    wait_and_click_screenshot(FIREFOX_ICON)  # Открыть ГОЛД через иконку на раб.столе.
    pyautogui.press('enter')


def navigate_gold_menu_until_product_number_input() -> None:
    """ В окне firefox открыть меню ГОЛД и пройти по нему
    до ввода номера товара, до пункта 33.4 """
    wait_and_click_screenshot(GOLD_LOADED)  # Проверка загрузки и активности firefox.
    wait_and_click_screenshot(STOCK_11)  # Кликнуть по stock 11
    input_in_gold_by_screenshot(LOGIN_PLACE, LOGIN_VALUE, 20)  # Ввести логин.
    input_in_gold_by_screenshot(PASSWORD_PLACE, PASSWORD_VALUE, 20)  # Ввести пароль.
    wait_and_click_screenshot(LOGIN)  # Войти.
    menu_33 = wait_and_click_screenshot(MENU_33, timeout=30)  # 33 пункт меню
    pyautogui.doubleClick(menu_33)
    menu_33_4 = wait_and_click_screenshot(MENU_33_4)  # 33.4 пункт меню
    pyautogui.doubleClick(menu_33_4)
    wait_and_click_screenshot(TO_SEAL_OVERDUE)  # Поставить галочку на отметку скрыть просроченные.
    x, y = pyautogui.position()
    pyautogui.click(x - 80, y)


def activate_current_gold_or_launch_new_gold() -> None:
    """ Проверка запущенных процессов firefox и java и их
    активирование(раскрытие окон) или запуск Голда по новой, с иконки на рабочем столе."""
    # Проверяем запущены ли процессы: firefox и java
    firefox_proc = check_process_in_os(FIREFOX_PROC)
    java_proc = check_process_in_os(JAVA_PROC)

    # Проверяем активны ли окна.
    active_firefox = activate_current_firefox(firefox_proc)
    active_java = activate_current_java(java_proc)

    # Если активны окна firefox и java
    if active_firefox and active_java:
        try:
            wait_and_click_screenshot(MENU_33_4)
        except ScreenshotNotFoundException:
            wait_and_click_screenshot(MENU_33)
            wait_and_click_screenshot(MENU_33_4)

    # Если запущен только firefox
    elif active_firefox and not active_java:
        try:
            # Если найдет значит код в карточке товара.
            wait_and_click_screenshot(DECLARATION_CARD)
            pyautogui.hotkey('Alt', 'b')
        except ScreenshotNotFoundException:
            pass

    # Весь путь с иконки на рабочем столе.
    elif not active_firefox and not active_java:
        launch_firefox_for_gold_from_desktop()
        navigate_gold_menu_until_product_number_input()


##################################################################################
# Вспомогательные функции - для работы с файлами.
##################################################################################
def write_last_viewed_number_to_file(text_file: str, number) -> None:
    """Записать номер последнего просмотренного документа в файл."""
    with open(text_file, 'w', encoding='utf-8') as file:
        file.write(str(number))


def read_last_viewed_number_from_file(text_file: str) -> int:
    """Прочитать номер последнего просмотренного документа из файла."""
    if not os.path.isfile(text_file):
        with open(text_file, 'w', encoding='utf-8') as file:
            file.write('')
    with open(text_file, 'r', encoding='utf-8') as file:
        last_number = int(file.read())
        return last_number


def return_existing_xlsx_or_create_new(temp_df: str) -> str:
    """Проверить есть ли xlsx файл для временного хранения данных,
    если да - открыть его, если нет_ создать."""
    temp_file = temp_df
    if os.path.isfile(temp_file):
        return temp_file
    workbook = openpyxl.Workbook()
    logging.info("Создан файл %s", FILE_GOLD)

    workbook.save(temp_file)
    return temp_file


##################################################################################
# Конкретные функции для работы с товарами и декларациями.
##################################################################################
def search_coords_of_all_declarations_on_page_in_gold() -> list | None:
    """После ввода кода товара в ГОЛД, ищет и возвращает координаты центров
    всех декларации и свидетельств, которые есть по данному коду товара."""
    centers = set()  # Множество для центров деклараций.

    # Ищем местоположение серой декларации, вычисляем ее центр и добавляем в centers.
    gray_declaration = wait_and_click_screenshot(GRAY_DECLARATION, timeout=1, confidence=0.6)
    center_x = gray_declaration.left + gray_declaration.width // 2
    center_y = gray_declaration.top + gray_declaration.height // 2
    centers.add((center_x, center_y))

    # Загрузить шаблон (скриншот который нужно найти)
    template = cv2.imread(GREEN_DECLARATION, 0)
    template_weight, template_height = template.shape[::-1]

    # Сделать скриншот экрана(на чем будем искать шаблон), конвертировать в массив.
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    # Ищем шаблон на скриншоте экрана.
    res = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
    # Устанавливаем порог сходства.
    threshold = 0.6
    # Сохраняем координаты всех совпадений.
    locations = np.where(res >= threshold)

    # Перебираем все совпадения и ищем центр каждого из них, добавляем в centers.
    for pt in zip(*locations[::-1]):
        center_x = pt[0] + template_weight // 2
        center_y = pt[1] + template_height // 2
        centers.add((center_x, center_y))

    return list(centers)  # Преобразуем на выходе в список, для дальнейшей итерации по нему.


def get_data_about_one_doc_in_gold() -> dict:
    """
    Непосредственное сохранение данных по одной декларации.
    Сохранить номер Документа(декларации) и наименование изготовителя в словарь.
    """
    data = {}
    # Проверяем, что провалились в декларацию.
    wait_and_click_screenshot(DECLARATION_CARD)
    # Поля, из которых нужно собрать данные.
    needed_fields = (REG_NUMBER_FIELD, MANUFACTURER_FIELD)

    for field in needed_fields:
        wait_and_click_screenshot(field)  # Ищем скриншот нужного поля.
        x, y = pyautogui.position()
        pyautogui.click(x + 120, y)  # Смещаемся в поле для ввода
        pyautogui.doubleClick()
        pyautogui.hotkey('Alt', 'a')  # Выделяем текст
        pyperclip.copy("")
        pyautogui.hotkey('Ctrl', 'c')  # Копируем текст из поля.
        field_value = pyperclip.paste()

        # Заполнить словарь соответствующими значениями.
        if field_value == '' and field == REG_NUMBER_FIELD:
            data['ДОС'] = '-'
        elif field_value and field == REG_NUMBER_FIELD:
            data['ДОС'] = field_value
        elif field_value == '' and field == MANUFACTURER_FIELD:
            data['Изготовитель'] = '-'
        elif field_value and field == MANUFACTURER_FIELD:
            data['Изготовитель'] = field_value

    return data


def add_doc_numbers_and_manufacturers_in_df(input_file: str, output_file: str):
    """Основная, связующая функция модуля.
    Добавить в листе мониторинга тип документа,
    номер декларации и изготовителя из ГОЛД."""

    # Читаем проверяемый файл с порядковым номером, кодом товара и наименования товара.
    old_df = pd.read_excel(input_file)

    # TEMP_DF - временный файл xlsx, в котором хранятся строки с ДОС и изготовителем.
    gold_df = return_existing_xlsx_or_create_new(output_file)

    # Последний порядковый номер из просмотренных в ГОЛД кодов товаров.
    try:
        last_viewed_number = read_last_viewed_number_from_file(VIEWED_GOLD_PRODUCTS)
        if last_viewed_number is None:
            last_viewed_number = 0
    except ValueError:
        last_viewed_number = 0

    if gold_df is None:  # Если файл пустой, создаем DataFrame.
        new_df = pd.DataFrame(columns=[
            'Порядковый номер АМ',
            'Код товара',
            'Наименование товара',
            'ДОС',
            'Изготовитель',])
    else:  # Если нет, то читаем существующий
        new_df = pd.read_excel(gold_df)

    # Запустить ГОЛД.
    activate_current_gold_or_launch_new_gold()
    count = 0  # Для количества обработанных кодов товаров за вызов функции.

    try:
        # Перебираем построчно данные из excel.
        for _, row in old_df[last_viewed_number:].iterrows():
            # Читаем код товара из файла.
            product_number = row.loc['Код товара']

            # Проверяем не просматривали ли его ранее
            if row.loc['Порядковый номер АМ'] <= last_viewed_number:
                continue

            else:  # Если ранее код товара не просматривали.
                # Ввести номер кода товара
                input_in_gold_by_screenshot(PRODUCT_INPUT, product_number, 120)
                pyautogui.hotkey('Alt', 't')  # Поиск.
                waiting_disappear_screenshot(LOADING_PRODUCT)  # Дождаться, загрузки страницы
                # Проверить на наличие сообщения на экране об отсутствии данных.
                error_no_data = handle_error_no_data_in_web()
                if error_no_data is None:  # Если сообщения не было, то ищем центры.
                    # Координаты центров всех деклараций, которые есть на странице в ГОЛД.
                    centres = search_coords_of_all_declarations_on_page_in_gold()
                else:
                    centres = None

                if centres:  # Если найдены центры деклараций.
                    item = 0  # Переменная для итерации по списку центров.
                    while item < len(centres):
                        pyautogui.doubleClick(centres[item])
                        data_from_gold = get_data_about_one_doc_in_gold()
                        new_ser = pd.Series([data_from_gold['ДОС'],
                                             data_from_gold['Изготовитель']],
                                            index=data_from_gold.keys())
                        # Новый Series на 4 колонки с ДОС и изготовителем добавляем в новый DF.
                        new_row = row._append(new_ser)
                        new_df = new_df._append(new_row, ignore_index=True)  # Добавляем в DataFrame

                        pyautogui.hotkey('Alt', 'b')  # Возврат к вводу кода товара в ГОЛД.
                        item += 1

                else:
                    new_ser = pd.Series(['не найдено', 'не найдено'], index=['ДОС', 'Изготовитель'])
                    new_row = row._append(new_ser)  # Добавляем в DataFrame.
                    new_df = new_df._append(new_row, ignore_index=True)  # Добавляем в DataFrame

                count += 1
                last_viewed_number = row.loc['Порядковый номер АМ']

    except ScreenshotNotFoundException as error:
        logging.error('Скриншот %s не найден', error.image_path)
        raise StopIterationExceptionInGold

    finally:
        # Записать DataFrame во временный xlsx файл.
        new_df.to_excel(gold_df, index=False)
        # А просмотренные коды товаров в текстовой файл.
        write_last_viewed_number_to_file(VIEWED_GOLD_PRODUCTS, last_viewed_number)
        return count


def launch_gold_module(attempts_for_range: int, input_file: str, output_file: str) -> None:
    """
    Запустить код из модуля, привести в действие все имеющиеся функции.

    :param attempts_for_range: количество итераций, итерации нужны на случай ошибок
     при работе с ГОЛД, если происходит ошибка, то по новой запускается ГОЛД.
    :param input_file: файл с тремя колонками: порядковый номер АМ, код товара, наименование товара
    :param output_file: файл, в котором будет сохранен датафрейм с данными из ГОЛД.
    """
    logging.info("Запуск программы по работе с ГОЛД - 'launch_gold_module'")
    for i in range(attempts_for_range):
        logging.info("Старт итерации проверки данных в ГОЛД № %d", i)
        start_iter = time.time()
        count = 0
        try:
            count = add_doc_numbers_and_manufacturers_in_df(input_file, output_file)
        finally:
            logging.info("Итерация № %d окончена. Обработано - %d кодов товара. "
                         "Время выполнения %f." % (i, count, time.time() - start_iter))

            two_columns = pd.read_excel(FILE_FOR_TWO_COLUMNS)
            gold = pd.read_excel(FILE_GOLD)
            # Проверка, проверены ли все номера в ГОЛД
            try:
                if two_columns['Порядковый номер АМ'].iloc[-1] == gold['Порядковый номер АМ'].iloc[-1]:
                    break
            except KeyError:
                pass
    logging.info("Окончание работы программы по работе с ГОЛД - 'launch_gold_module'")
