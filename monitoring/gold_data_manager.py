"""
Модуль для работы с GOLD.
    class ScreenShotWorker: основная задача работа через pyautogui со скриншотами.

    class GoldScreenShotWorker(ScreenShotWorker): - основная задача -
        работа со скриншотами в окне программы GOLD.

    class GoldLauncher(GoldScreenShotWorker): - Основная задача -
        запуск и подготовка для дальнейшей работы программы GOLD

    class ADocDataCollector(GoldScreenShotWorker): - сбор данных в ГОЛД на один документ.

    class GoldCollector(ADocDataCollector, GoldLauncher): - сбор данных в ГОЛД на один документ,
        идет построчно в файле two_columns и собирает по ним данные.

    def launch_gold_module: запуск всего кода в модуле.
"""
import time
import subprocess
import cv2
import numpy as np
import pandas as pd
import pyautogui
import pytesseract
import pyperclip

from config import LOGIN_VALUE, PASSWORD_VALUE
from exceptions import ScreenshotNotFoundException, StopIterationExceptionInGold
from logger_config import log_to_file_info
from monitoring.constants import (PATH_TO_TESSERACT, ScreenShotsForWorkWithGold as ScreenShots,
                                  FIREFOX_PROC, JAVA_PROC, FieldsInProductCardGold,
                                  Files, COLUMNS_FOR_GOLD_DF, DIR_CURRENT_MONTHLY_MONITORING)

from monitoring.functions_for_work_with_files_and_dirs import (
    write_last_viewed_number_to_file, read_last_viewed_number_from_file,
    return_or_create_xlsx_file, read_and_return_dict_from_json_file,
    check_process_in_os, return_or_create_dir)


# Путь к файлам Tesseract OCR и poppler
pytesseract.pytesseract.tesseract_cmd = PATH_TO_TESSERACT
path_to_poppler = r'.././poppler-23.11.0/Library/bin'


class ScreenShotWorker:
    """ Класс - основная задача работа через pyautogui со скриншотами."""
    @staticmethod
    def _locate_and_click(screenshot: str, confidence: float = 0.7) -> str | None:
        """ Получает путь к скриншоту, ищет его на экране и кликает на него.
        Используется как внутренняя функция. """
        time.sleep(0.03)
        screenshot = pyautogui.locateOnScreen(screenshot, confidence=confidence)
        if screenshot:  # Если скриншот найден кликнуть по нему и вернуть его.
            pyautogui.click(screenshot)
            return screenshot

    def click_screenshot(self, screenshot: str, timeout: int = 5,
                         confidence: float = 0.7) -> None | str:
        """ Ожидать появление скриншота в течение заданного времени.
        По появлении кликнуть по нему."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return self._locate_and_click(screenshot, confidence)
            except pyautogui.ImageNotFoundException:
                pass
        raise ScreenshotNotFoundException(screenshot)

    def waiting_disappear_screenshot(self, screenshot: str, timeout: int = 10) -> None:
        """ Ждем пока скриншот, мешающий работе исчезнет с экрана. """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                time.sleep(0.05)
                screenshot = self._locate_and_click(screenshot)
                if screenshot:  # Если найден, то продолжаем его находить.
                    pass
            except pyautogui.ImageNotFoundException:
                return None

    def input_in_field_with_offset(self, screenshot: str, string_for_input: str,
                                   x_offset: int) -> None:
        """Ввести строку в поле голда. Поиск по скриншоту, смещение по оси x"""
        # Находим положение нужного скриншота(слова).
        input_number = self.click_screenshot(screenshot)
        pyautogui.moveTo(input_number)
        x, y = pyautogui.position()
        pyautogui.moveTo(x + x_offset, y)  # Смещаемся по оси x вправо, в поле для ввода.
        pyautogui.doubleClick()
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')  # Очистить поле
        pyperclip.copy(string_for_input)
        pyautogui.hotkey('ctrl', 'v')  # Вставить значение.

    @staticmethod
    def select_and_copy() -> str:
        """Выделить весь текст, где стоит курсор, скопировать в буфер."""
        pyautogui.hotkey('Alt', 'a')
        pyperclip.copy("")
        pyautogui.hotkey('Ctrl', 'c')
        value = pyperclip.paste()
        return value

    def find_center_of_screenshot(self, screenshot: str):
        """ Найти и вернуть координаты центра нужного скриншота по x и y. """
        screenshot = self.click_screenshot(screenshot, timeout=1, confidence=0.6)
        center_x = screenshot.left + screenshot.width // 2
        center_y = screenshot.top + screenshot.height // 2
        return center_x, center_y

    @staticmethod
    def make_screenshot_for_multiple_searches():
        """ Сделать скриншот экрана, и подготовить его для поиска множества изображений. """
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        return screenshot

    def find_centers_of_copies_of_template(self, template: str) -> list:
        """ Найти координаты центров всех копий шаблона. """
        centers = []
        template = cv2.imread(template, 0)  # Шаблон (скриншот который нужно найти).
        template_weight, template_height = template.shape[::-1]
        # Скрин экрана, на котором будем искать шаблон
        screenshot_for_searches = self.make_screenshot_for_multiple_searches()
        # Ищем шаблон на скриншоте экрана.
        results_of_searches = cv2.matchTemplate(screenshot_for_searches,
                                                template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.6  # Устанавливаем порог сходства.
        locations = np.where(results_of_searches >= threshold)  # Координаты всех совпадений.

        # Перебираем все совпадения и добавляем центра каждого из них в centers.
        for point in zip(*locations[::-1]):
            center_x = point[0] + template_weight // 2
            center_y = point[1] + template_height // 2
            centers.append((center_x, center_y))

        return centers


class GoldScreenShotWorker(ScreenShotWorker):
    """ Класс - основная задача - работа со скриншотами в окне программы GOLD. """

    @staticmethod
    def press_search_in_gold():
        """ Нажать поиск после ввода номера продукта. """
        pyautogui.hotkey('Alt', 't')

    @staticmethod
    def press_back_in_gold():
        """ Нажать вернуться назад из карточки продукта. """
        pyautogui.hotkey('Alt', 'b')

    def handle_error_no_data_in_web(self, timeout: int = 2) -> bool | None:
        """ При сообщении об ошибке в виде: 'Отсутствия данных' нажать 'ОК'. """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                image = self._locate_and_click(ScreenShots.MESSAGE_DATA_NOT_FOUND.value)
                if image:  # Если найдено сообщение об ошибке, то ищем "ОК" и кликаем по нему.
                    self._locate_and_click(ScreenShots.FOR_CLICK_OK_ON_DATA_NOT_FOUND.value)
                    return True

            except pyautogui.ImageNotFoundException:
                pass

    def check_crash_java(self, timeout: int = 1) -> None:
        """ Проверка на наличие сообщение о крахе Java. Если оно есть, то закрыть Firefox. """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                screenshot = self._locate_and_click(ScreenShots.CRASH_JAVA.value)
                if screenshot:  # Если сообщение о крахе Java, то закрываем браузер.
                    command = "taskkill /F /IM firefox.exe"  # Команда для завершения процессов браузера Firefox.
                    subprocess.run(command, shell=True)  # Выполнение команды
            finally:
                pass

    def navigate_menu_from_start(self) -> None:
        """ В окне firefox открыть меню ГОЛД и пройти по нему
        до ввода номера товара, до пункта 33.4 """

        self.click_screenshot(ScreenShots.GOLD_LOADED.value)  # Проверка загрузки firefox.
        self.click_screenshot(ScreenShots.STOCK_11.value)  # Кликнуть по stock 11
        self.input_in_field_with_offset(ScreenShots.LOGIN_PLACE.value, LOGIN_VALUE, 20)
        self.input_in_field_with_offset(ScreenShots.PASSWORD_PLACE.value, PASSWORD_VALUE, 20)
        self.click_screenshot(ScreenShots.ENTER_LOGIN.value)  # Нажать войти.
        menu_33 = self.click_screenshot(ScreenShots.MENU_33.value, timeout=30)  # 33 пункт меню
        pyautogui.doubleClick(menu_33)
        menu_33_4 = self.click_screenshot(ScreenShots.MENU_33_4.value)  # 33.4 пункт меню
        pyautogui.doubleClick(menu_33_4)
        self.click_screenshot(ScreenShots.TO_SEAL_OVERDUE.value)  # Включить-скрыть просроченные.
        x, y = pyautogui.position()
        pyautogui.click(x - 80, y)

    def navigate_menu_from_middle(self):
        """Пройти по меню при открытом меню java"""
        try:
            self.click_screenshot(ScreenShots.MENU_33_4.value)

        except ScreenshotNotFoundException:
            self.check_crash_java()
            self.click_screenshot(ScreenShots.MENU_33.value)
            self.click_screenshot(ScreenShots.MENU_33_4.value)

    def navigate_from_product_card(self):
        """ Если программа в карточке товара."""
        try:  # Если найдет значит код в карточке товара.
            self.click_screenshot(ScreenShots.DECLARATION_CARD.value)
            pyautogui.hotkey('Alt', 'b')
        except ScreenshotNotFoundException:
            pass


class GoldLauncher(GoldScreenShotWorker):
    """ Основная задача - запуск и подготовка для дальнейшей работы программы GOLD.
    Через определение текущего состояния программы(процесса, браузера, окна)
    и дальнейшая навигация. """

    def activate_current_firefox(self, proc) -> bool | None:
        """ Раскрыть окно запущенного firefox. """
        if proc is not None:
            self.click_screenshot(ScreenShots.FIREFOX_ICON_PANEL.value, confidence=0.8)
            return True

    def activate_current_java(self, proc) -> bool | None:
        """ Раскрыть окно запущенного java."""
        if proc is not None:
            try:
                self.click_screenshot(ScreenShots.MENU_IN_GOLD.value, confidence=0.8)
                return True
            except ScreenshotNotFoundException:
                pass

    def launch_gold_from_desktop(self) -> None:
        """Найти на рабочем столе иконку firefox и открыть ее."""
        # Переключить на английскую раскладку
        time.sleep(1)
        pyautogui.hotkey('Win', 'd')  # Свернуть все окна.
        self.click_screenshot(ScreenShots.FIREFOX_ICON.value)  # Открыть через иконку на столе.
        pyautogui.press('enter')

    def activate_current_gold_or_launch_new_gold(self) -> None:
        """ Основная функция запуска. Определение на каком этапе
        находится ГОЛД и выбор дальнейшей навигации по нему."""
        # Проверка запущены ли процессы: firefox и java
        firefox_proc = check_process_in_os(FIREFOX_PROC)
        java_proc = check_process_in_os(JAVA_PROC)
        # Проверка активны ли окна.
        active_firefox = self.activate_current_firefox(firefox_proc)
        active_java = self.activate_current_java(java_proc)

        if active_firefox and active_java:  # Если активны окна firefox и java
            self.navigate_menu_from_middle()
        elif active_firefox and not active_java:  # Если запущен только firefox
            self.navigate_from_product_card()
        elif not active_firefox and not active_java:  # Весь путь с иконки на рабочем столе.
            self.launch_gold_from_desktop()
            self.navigate_menu_from_start()


class ADocDataCollector(GoldScreenShotWorker):
    """ Задача - сбор данных в ГОЛД на один документ. """

    def get_data_about_one_doc_in_gold(self, applicants_codes_and_name: dict) -> dict:
        """ Собираем данные в ГОЛД по одному документу из соответствующих полей."""
        doc_data = {}
        # Проверка, что провалились в декларацию.
        self.click_screenshot(ScreenShots.DECLARATION_CARD.value, timeout=1)

        # Действия по сохранению данных в словарь, исходя из наименования поля.
        actions_for_fields = {
            FieldsInProductCardGold.REG_NUMBER_FIELD:
                lambda value: doc_data.update({'ДОС': '-' if value == '' else value}),
            FieldsInProductCardGold.MANUFACTURER_FIELD:
                lambda value: doc_data.update({'Изготовитель': '-' if value == '' else value}),
            FieldsInProductCardGold.DATE_OF_END:
                lambda value: doc_data.update({'Дата окончания': value.replace('/', '.')}),
            FieldsInProductCardGold.APPLICANT_CODE:
                lambda value: doc_data.update(
                    {'Заявитель ГОЛД': applicants_codes_and_name.get(value, 'Нет в JSON')})}

        # Цикл по полям карточки продукта.
        for field in FieldsInProductCardGold:
            self.click_screenshot(field.value)
            x, y = pyautogui.position()
            pyautogui.click(x + 100, y)
            # Доп действие для кода заявителя.
            if field != FieldsInProductCardGold.APPLICANT_CODE:
                pyautogui.doubleClick()

            field_value = self.select_and_copy()
            # Сразу вызываем действие, полученное из словаря, и передаем в него field_value.
            actions_for_fields.get(field, lambda value: None)(field_value)

        return doc_data


class GoldCollector(ADocDataCollector, GoldLauncher):
    """ Основная задача - сбор всех данных в GOLD.
    Читает построчно данные из TwoColumnsFile и собирает данные из ГОЛД."""

    def __init__(self, two_columns_file, gold_file, last_number_file):
        self.two_columns_df = pd.read_excel(two_columns_file)
        self.gold_df = return_or_create_xlsx_file(gold_file)
        self.last_viewed_number_in_gold = read_last_viewed_number_from_file(
            last_number_file)
        self.new_df = self.return_or_create_new_df()
        self.applicants_codes_and_names = read_and_return_dict_from_json_file(
            Files.APPLICANTS_CODES_AND_NAME_FROM_GOLD.value)

    def return_or_create_new_df(self):
        """Вернуть или создать DataFrame для итогового результата. """
        if self.gold_df is None:  # Если файл пустой, создаем DataFrame.
            new_df = pd.DataFrame(columns=COLUMNS_FOR_GOLD_DF)
        else:  # Если нет, то читаем существующий
            new_df = pd.read_excel(self.gold_df)
        return new_df

    def make_copy_of_gold_file(self, row_name):
        """ Сделать копию ГОЛД файла"""
        return_or_create_dir(r'./%s/copies_of_gold' % DIR_CURRENT_MONTHLY_MONITORING)
        copy_xlsx_file = r'./%s/copies_of_gold/copy_lane_%s.xlsx' % (DIR_CURRENT_MONTHLY_MONITORING, row_name)
        total_df = pd.concat([self.two_columns_df, self.new_df])
        total_df.to_excel(copy_xlsx_file, index=False)

    def handle_no_data(self, row):
        """ При сообщении нет данных добавление соответствующей строки в результат"""
        new_ser = pd.Series(['Нет данных в GOLD'], index=['ДОС'])
        new_row = row._append(new_ser)  # Добавляем в DataFrame.
        self.new_df = self.new_df._append(new_row, ignore_index=True)  # Добавляем в DataFrame

    def search_coords_of_all_docs_on_page_in_gold(self) -> list | None:
        """ После ввода кода товара в ГОЛД, ищет и возвращает координаты
        всех декларации и свидетельств, которые есть на экране по данному коду товара."""
        centers = []  # Центры деклараций.
        # Координаты документа с серым статусом, координаты центра добавляем в centers.
        gray_doc_x, gray_doc_y = self.find_center_of_screenshot(
            ScreenShots.GRAY_STATUS_DECLARATION.value)
        centers.append((gray_doc_x, gray_doc_y))
        # Координаты документов с зеленым статусом, координаты центров добавляем в centers.
        centers_of_green_docs = self.find_centers_of_copies_of_template(
            ScreenShots.GREEN_STATUS_DECLARATION.value)
        centers.extend(centers_of_green_docs)
        return centers

    def get_data_by_centres_of_docs(self, centres, row):
        """ Собрать информацию по всем документам на один код продукта. """
        item = 0  # Переменная для итерации по списку центров.
        while item < len(centres):
            pyautogui.doubleClick(centres[item])
            one_doc_data = self.get_data_about_one_doc_in_gold(self.applicants_codes_and_names)
            new_ser = pd.Series([one_doc_data['ДОС'], one_doc_data['Дата окончания'],
                                 one_doc_data['Изготовитель'], one_doc_data['Заявитель ГОЛД']],
                                index=['ДОС', 'Дата окончания', 'Изготовитель', 'Заявитель ГОЛД', ])
            # Новый Series добавляем в новый DF.
            new_row = row._append(new_ser)
            self.new_df = self.new_df._append(new_row, ignore_index=True)  # Добавляем в DataFrame
            self.press_back_in_gold()
            item += 1

    def add_data_from_gold_to_result_df(self):
        """Получение данных по строкам через цикл."""
        # Перебираем построчно данные из файла с кодами и наименованиями продуктов .
        for _, row in self.two_columns_df[self.last_viewed_number_in_gold:].iterrows():

            # На каждой 500 строке сделать копию GOLD-файла(DataFrame)
            if row.name % 500 == 0 and row.name != 0:
                self.make_copy_of_gold_file(row.name)

            # Ввести номер кода товара
            product_number = row.loc['Код товара']  # Код товара из файла.
            self.input_in_field_with_offset(ScreenShots.PRODUCT_INPUT_FIELD.value,
                                            product_number, 120)
            self.press_search_in_gold()
            # Дождаться загрузки страницы
            self.waiting_disappear_screenshot(ScreenShots.LOADING_PRODUCT.value)

            # Проверить и обработать сообщение на экране об отсутствии данных.
            error_no_data = self.handle_error_no_data_in_web()
            if error_no_data:
                self.handle_no_data(row)
                continue

            # for _ in range(5):
            centres_of_docs = self.search_coords_of_all_docs_on_page_in_gold()
            if centres_of_docs:  # Если найдены центры деклараций, то получаем данные.
                self.get_data_by_centres_of_docs(centres_of_docs, row)

            self.last_viewed_number_in_gold = row.loc['Порядковый номер АМ']
        write_last_viewed_number_to_file(Files.LAST_VIEWED_IN_GOLD_NUMBER.value,
                                         self.last_viewed_number_in_gold)

    def process_add_data_from_gold_to_result_df(self):
        """ Запустить код сбора данных через конструкцию try/except """
        self.activate_current_gold_or_launch_new_gold()
        try:
            self.add_data_from_gold_to_result_df()
        except ScreenshotNotFoundException as error:
            log_to_file_info('Скриншот %s не найден' % error.image_path)
            raise StopIterationExceptionInGold
        finally:
            self.new_df.to_excel(self.gold_df, index=False)
            write_last_viewed_number_to_file(Files.LAST_VIEWED_IN_GOLD_NUMBER.value,
                                             self.last_viewed_number_in_gold)


def launch_gold_module(attempts_for_range: int, two_columns_file: str, gold_file: str) -> None:
    """ Запуск всего кода модуля. """
    log_to_file_info("Запуск программы по работе с ГОЛД - 'launch_gold_module'")
    for i in range(attempts_for_range):
        try:
            gold_collector = GoldCollector(two_columns_file,
                                           gold_file,
                                           Files.LAST_VIEWED_IN_GOLD_NUMBER.value)
            gold_collector.process_add_data_from_gold_to_result_df()
        finally:
            two_columns = pd.read_excel(two_columns_file)
            gold = pd.read_excel(gold_file)
            # Проверка, проверены ли все номера в ГОЛД
            try:
                if two_columns.iloc[-1].name == gold.iloc[-1].name:
                    break
            except KeyError:
                pass
    log_to_file_info("Окончание работы программы по работе с ГОЛД - 'launch_gold_module'")
