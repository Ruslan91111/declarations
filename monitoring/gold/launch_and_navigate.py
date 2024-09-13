"""
Модуль с классами для запуска программы gold и навигации по его меню.

Классы:
    - GoldMenuNavigator(ScreenshotWorker):
        Навигация по меню программы GOLD.

    - GoldLauncher(GoldMenuNavigator):
        Запуск и подготовка для дальнейшей работы программы GOLD.
        Через определение текущего состояния программы(процесса, браузера, окна)
        и дальнейшая навигация.

"""



import subprocess
import time

import pyautogui

from common.config import LOGIN_VALUE, PASSWORD_VALUE
from common.constants import ScrForGold as ScreenShots, FIREFOX_PROC, JAVA_PROC
from common.file_worker import check_process_in_os
from common.exceptions import ScreenshotNotFoundException
from gold.screenshot_work import ScreenshotWorker


class GoldMenuNavigator(ScreenshotWorker):
    """ Навигация по меню программы GOLD. """

    @staticmethod
    def press_search_in_gold():
        """ Нажать поиск после ввода номера продукта. """
        pyautogui.hotkey('Alt', 't')

    @staticmethod
    def press_back_in_gold():
        """ Нажать вернуться назад из карточки продукта. """
        pyautogui.hotkey('Alt', 'b')

    def handle_error_no_data(self, timeout: int = 2) -> bool | None:
        """ При сообщении об ошибке в виде: 'Отсутствия данных' нажать 'ОК'. """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                image = self._locate_and_click(ScreenShots.MESSAGE_DATA_NOT_FOUND.value)
                if image:  # Если найдено сообщение об ошибке, то ищем "ОК" и кликаем по нему.
                    self._locate_and_click(ScreenShots.OK_BUTTON_NOT_FOUND.value)
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
                    command = "taskkill /F /IM firefox.exe"  # Команда для закрытия Firefox.
                    subprocess.run(command, shell=True)  # Выполнение команды
            finally:
                pass

    def handle_error_launch_in_save_mode(self, timeout: int = 2) -> bool | None:
        """ При сообщении об ошибке в виде: 'Отсутствия данных' нажать 'ОК'. """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                image = self._locate_and_click(ScreenShots.SAVE_MODE.value)
                if image:  # Если найдено сообщение об ошибке, то ищем "ОК" и кликаем по нему.
                    self._locate_and_click(ScreenShots.OK_BUTTON_NOT_FOUND.value)
                    return True

            except pyautogui.ImageNotFoundException:
                pass

    def navigate_menu_from_start(self) -> None:
        """ В окне firefox открыть меню ГОЛД и пройти по нему
        до ввода номера товара, до пункта 33.4 """
        # Проверка загрузки firefox.
        self.search_and_click(ScreenShots.GOLD_LOADED.value)
        self.search_and_click(ScreenShots.STOCK_11.value)
        self.input_using_offset(
            ScreenShots.LOGIN_PLACE.value, LOGIN_VALUE, 20)
        self.input_using_offset(
            ScreenShots.PASSWORD_PLACE.value, PASSWORD_VALUE, 20)
        self.search_and_click(ScreenShots.ENTER_LOGIN.value)  # Нажать войти.
        menu_33 = self.search_and_click(
            ScreenShots.MENU_33.value, timeout=30)
        pyautogui.doubleClick(menu_33)
        menu_33_4 = self.search_and_click(ScreenShots.MENU_33_4.value)
        pyautogui.doubleClick(menu_33_4)
        self.search_and_click(ScreenShots.TO_SEAL_OVERDUE.value)
        x, y = pyautogui.position()
        pyautogui.click(x - 80, y)

    def navigate_menu_from_middle(self):
        """Пройти по меню при открытом меню java"""
        try:
            self.search_and_click(ScreenShots.MENU_33_4.value)

        except ScreenshotNotFoundException:
            self.check_crash_java()
            self.search_and_click(ScreenShots.MENU_33.value)
            self.search_and_click(ScreenShots.MENU_33_4.value)

    def navigate_from_product_card(self):
        """ Если программа в карточке товара."""
        try:  # Если найдет значит код в карточке товара.
            self.search_and_click(ScreenShots.DECLARATION_CARD.value)
            pyautogui.hotkey('Alt', 'b')
        except ScreenshotNotFoundException:
            pass


class GoldProcess(GoldMenuNavigator):
    """ Запуск и подготовка для дальнейшей работы программы GOLD.
    Через определение текущего состояния программы(процесса, браузера, окна)
    и дальнейшая навигация. """

    def activate_current_firefox(self, proc) -> bool | None:
        """ Раскрыть окно запущенного firefox. """
        if proc is not None:
            self.search_and_click(ScreenShots.FIREFOX_ICON_PANEL.value, confidence=0.8)
            return True

    def activate_current_java(self, proc) -> bool | None:
        """ Раскрыть окно запущенного java."""
        if proc is not None:
            try:
                self.search_and_click(ScreenShots.MENU_IN_GOLD.value, confidence=0.8)
                return True
            except ScreenshotNotFoundException:
                pass

    def launch_gold_from_desktop(self) -> None:
        """Найти на рабочем столе иконку firefox и открыть ее."""
        # Переключить на английскую раскладку
        time.sleep(1)
        pyautogui.hotkey('Win', 'd')  # Свернуть все окна.
        # Открыть через иконку на столе.
        self.search_and_click(ScreenShots.FIREFOX_ICON.value)
        pyautogui.press('enter')
        self.handle_error_launch_in_save_mode()

    def activate_or_launch_gold(self) -> None:
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

    def search_coords_of_all_docs(self) -> list | None:
        """ После ввода кода товара в ГОЛД, ищет и возвращает координаты
        всех декларации и свидетельств, которые есть на экране по данному коду товара."""
        centers = []  # Центры деклараций.

        # Координаты документа с серым статусом, координаты центра добавляем в centers.
        try:
            gray_doc_x, gray_doc_y = self.find_coords_of_scr_center(
                ScreenShots.GRAY_STATUS_DECL.value)
        except:
            gray_doc_x, gray_doc_y = self.find_coords_of_scr_center(
                ScreenShots.GRAY_APPROACHING_DECL.value)

        centers.append((gray_doc_x, gray_doc_y))

        # Координаты документов с зеленым статусом, координаты центров добавляем в centers.
        centers_of_green_docs = self.find_centers_on_template(
            ScreenShots.GREEN_STATUS_DECL.value)
        centers.extend(centers_of_green_docs)
        return centers
