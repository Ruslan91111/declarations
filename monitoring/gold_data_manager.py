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
import time

import cv2
import numpy as np
import pandas as pd
import pyautogui
import pytesseract
import pyperclip
import psutil

from config import LOGIN_VALUE, PASSWORD_VALUE
from exceptions import ScreenshotNotFoundException, StopIterationExceptionInGold
from selenium_through.supporting_functions import (read_viewed_numbers_of_documents,
                                                   write_viewed_numbers_to_file,
                                                   check_or_create_temporary_xlsx)


##################################################################################
# КОНСТАНТЫ - скриншоты
##################################################################################
# открыть ГОЛД и прокликать по меню.
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
TEMP_DF = r'.\temp_df.xlsx'  # Для сохранения DataFrame в .xlsx файл.
VIEWED_GOLD_PRODUCTS = r'.\viewed_products_in_gold.txt'  # Просмотренные номера деклараций
RESULT_FILE = r'.\Мониторинг АМ (2023).xlsx'  # Итоговый файл с результатами мониторинга
LOGGING_FILE = r'.\gold_data_log.log'

# Процессы для поиска в Windows.
FIREFOX_PROC = "firefox.exe"
JAVA_PROC = "java.exe"

# Путь к файлам Tesseract OCR и poppler
PATH_TO_TESSERACT = r'C:\Users\RIMinullin\AppData\Local\Programs\Tesseract-OCR\tesseract'
pytesseract.pytesseract.tesseract_cmd = PATH_TO_TESSERACT
path_to_poppler = r'../poppler-23.11.0/Library/bin'

STARS = '*' * 40
##################################################################################
# Логгирование.
##################################################################################
logging.basicConfig(level=logging.INFO,
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


def handle_error(timeout: int = 1) -> bool | None:
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
def check_program(process: str):
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


def launch_firefox_for_gold_from_desktop():
    """Найти на рабочем столе иконку firefox и открыть ее."""
    time.sleep(1)
    pyautogui.hotkey('Win', 'd')  # Свернуть все окна.
    wait_and_click_screenshot(FIREFOX_ICON)  # Открыть ГОЛД через иконку на раб.столе.
    pyautogui.press('enter')


def navigate_menu_until_product_number_input():
    """ В окне firefox открыть меню ГОЛД и пройти по нему
    до ввода номера товара, до пункта 33.4 """
    wait_and_click_screenshot(GOLD_LOADED)  # Проверка загрузки и активности firefox.
    wait_and_click_screenshot(STOCK_11)  # Кликнуть по stock 11
    input_in_gold_by_screenshot(LOGIN_PLACE, LOGIN_VALUE, 20)  # Ввести логин.
    input_in_gold_by_screenshot(PASSWORD_PLACE, PASSWORD_VALUE, 20)  # Ввести пароль.
    wait_and_click_screenshot(LOGIN)  # Войти.
    menu_33 = wait_and_click_screenshot(MENU_33)  # 33 пункт меню
    pyautogui.doubleClick(menu_33)
    menu_33_4 = wait_and_click_screenshot(MENU_33_4)  # 33.4 пункт меню
    pyautogui.doubleClick(menu_33_4)
    wait_and_click_screenshot(TO_SEAL_OVERDUE)  # Поставить галочку на отметку скрыть просроченные.
    x, y = pyautogui.position()
    pyautogui.click(x - 80, y)


def activate_or_launch_gold():
    """ Проверка запущенных процессов firefox и java и их
    активирование(раскрытие окон) или запуск Голда по новой, с иконки на рабочем столе."""
    # Проверяем запущены ли процессы: firefox и java
    firefox_proc = check_program(FIREFOX_PROC)
    java_proc = check_program(JAVA_PROC)

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
        navigate_menu_until_product_number_input()


##################################################################################
# Конкретные функции для работы с товарами и декларациями.
##################################################################################
def search_all_declarations_on_page() -> list | None:
    """После ввода кода товара в ГОЛД, ищем и возвращает координаты центров
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


def get_data_from_one_declaration() -> dict:
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
        wait_and_click_screenshot(field)  # Ищем скриншот поля.
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
            'Код товара', 'Наименование товара', 'ДОС', 'Изготовитель'])
    else:  # Если нет, то читаем существующий файл
        new_df = pd.read_excel(temp_df)

    # Запустить ГОЛД.
    activate_or_launch_gold()
    count = 0  # Для количества обработанных кодов товаров за вызов функции.

    try:
        # Перебираем построчно данные из excel.
        for _, row in df.iterrows():
            # Читаем номер товара из файла.
            product_number = row.loc['Код товара']

            # Проверяем не просматривали ли его ранее
            if product_number in set_of_viewed_numbers:
                pass

            else:  # Если ранее декларацию не просматривали.
                # Ввести номер кода товара
                input_in_gold_by_screenshot(PRODUCT_INPUT, product_number, 120)
                pyautogui.hotkey('Alt', 't')  # Поиск.
                waiting_disappear_screenshot(LOADING_PRODUCT)  # Дождаться, загрузки страницы
                # Проверить на наличие сообщения на экране об отсутствии данных.
                error_no_data = handle_error()
                if error_no_data is None:  # Если сообщения не было, то ищем центры.
                    # Координаты центров всех деклараций, которые есть на странице в ГОЛД.
                    centres = search_all_declarations_on_page()
                else:
                    centres = None

                if centres:  # Если найдены центры деклараций.
                    item = 0  # Переменная для итерации по списку центров.
                    while item < len(centres):
                        pyautogui.doubleClick(centres[item])
                        data_from_gold = get_data_from_one_declaration()
                        new_ser = pd.Series([data_from_gold['ДОС'],
                                             data_from_gold['Изготовитель']],
                                            index=data_from_gold.keys())
                        pyautogui.hotkey('Alt', 'b')  # Возврат к вводу кода товара в ГОЛД.
                        item += 1

                    logging.info("По номеру %s - %d документов." % (product_number, item))

                else:
                    new_ser = pd.Series(['не найдено', 'не найдено'], index=['ДОС', 'Изготовитель'])

                # Новый Series на 4 колонки с ДОС и изготовителем добавляем в новый DataFrame.
                new_row = row._append(new_ser)
                new_df = new_df._append(new_row, ignore_index=True)  # Добавляем в DataFrame

                # Добавляем в просмотренные
                set_of_viewed_numbers.add(product_number)
                count += 1

    except ScreenshotNotFoundException as error:
        screenshot = pyautogui.screenshot()
        screenshot.save(r".\screenshots\error.png")
        logging.error('Скриншот %s не найден', error.image_path)
        raise StopIterationExceptionInGold

    finally:
        # Записать DataFrame во временный xlsx файл.
        new_df.to_excel(temp_df, index=False)
        # А просмотренные коды товаров в текстовой файл.
        write_viewed_numbers_to_file(VIEWED_GOLD_PRODUCTS, set_of_viewed_numbers)
        return count


def launch_gold_module(attempts_for_range: int,
                       file_input,
                       sheet_in_input_file) -> None:
    """Запустить код из модуля."""
    logging.info(STARS)
    logging.info("Запуск программы по работе с ГОЛД - 'launch_gold_module'")
    for i in range(attempts_for_range):
        logging.info("Старт итерации № %d", i)
        start_iter = time.time()
        count = 0
        try:
            count = add_declaration_number_and_manufacturer(file_input,
                                                            sheet_in_input_file)
        finally:
            logging.info("Итерация № %d окончена. Обработано - %d кодов товара. "
                         "Время выполнения %f." % (i, count, time.time() - start_iter))
    logging.info("Окончание работы программы по работе с ГОЛД - 'launch_gold_module'")


if __name__ == '__main__':
    launch_gold_module(5, RESULT_FILE, 'декабрь2')
