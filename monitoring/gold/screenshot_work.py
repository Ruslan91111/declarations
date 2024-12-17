""" 
Модуль содержит класс - ScreenshotWorker через pyautogui.
"""
import time

import cv2
import numpy as np
import pyautogui
import pyperclip

from common.exceptions import ScreenshotNotFoundException


class ScreenshotWorker:
    """ Задача работа через pyautogui со скриншотами."""
    @staticmethod
    def _locate_and_click(screenshot: str, confidence: float = 0.7) -> str | None:
        """ Поиск скриншота, если найден, то кликнуть по нему. """
        time.sleep(0.03)
        screenshot = pyautogui.locateOnScreen(screenshot, confidence=confidence)
        if screenshot:  # Если скриншот найден кликнуть по нему и вернуть его.
            pyautogui.click(screenshot)
            return screenshot

    def search_and_click(self, screenshot: str, timeout: int = 5,
                         confidence: float = 0.8) -> None | str:
        """ Ожидать появление скриншота в течение заданного времени.
        По появлении кликнуть по нему."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return self._locate_and_click(screenshot, confidence)
            except pyautogui.ImageNotFoundException:
                pass
        raise ScreenshotNotFoundException(screenshot)

    def wait_scr_gone(self, screenshot: str, timeout: int = 10) -> None:
        """ Ждем пока скриншот, мешающий работе исчезнет с экрана. """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                time.sleep(0.05)
                loading = pyautogui.locateOnScreen(screenshot, confidence=0.7)
                if loading:  # Если найден, то продолжаем его находить.
                    pass
            except pyautogui.ImageNotFoundException:
                return None

    def input_using_offset(self, screenshot: str, string_for_input: str,
                           x_offset: int) -> None:
        """Ввести строку в поле голда. Поиск по скриншоту, смещение по оси x"""
        # Находим положение нужного скриншота(слова).
        input_number = self.search_and_click(screenshot)
        pyautogui.moveTo(input_number)
        x, y = pyautogui.position()
        pyautogui.moveTo(x + x_offset, y)  # Смещаемся по оси x вправо, в поле для ввода.
        pyautogui.doubleClick()
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')  # Очистить поле
        pyperclip.copy(string_for_input)
        pyautogui.hotkey('ctrl', 'v')  # Вставить значение.

    @staticmethod
    def select_text_and_copy() -> str:
        """Выделить весь текст, где стоит курсор, скопировать в буфер."""
        pyautogui.hotkey('Alt', 'a')
        pyperclip.copy("")
        pyautogui.hotkey('Ctrl', 'c')
        value = pyperclip.paste()
        return value

    def find_coords_of_scr_center(self, screenshot: str):
        """ Найти и вернуть координаты центра нужного скриншота по x и y. """
        screenshot = self.search_and_click(screenshot, timeout=1, confidence=0.7)
        center_x = screenshot.left + screenshot.width // 2
        center_y = screenshot.top + screenshot.height // 2
        return center_x, center_y

    @staticmethod
    def make_scr_template_for_multiple_searches():
        """ Сделать скриншот экрана, и подготовить его для поиска множества изображений. """
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        return screenshot

    def find_centers_on_template(self, template: str) -> list:
        """ Найти координаты центров всех копий шаблона. """
        centers = []
        template = cv2.imread(template, 0)  # Шаблон (скриншот который нужно найти).
        template_weight, template_height = template.shape[::-1]
        # Скрин экрана, на котором будем искать шаблон
        screenshot_for_searches = self.make_scr_template_for_multiple_searches()
        # Ищем шаблон на скриншоте экрана.
        results_of_searches = cv2.matchTemplate(screenshot_for_searches,
                                                template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8  # Устанавливаем порог сходства.
        locations = np.where(results_of_searches >= threshold)  # Координаты всех совпадений.

        # Перебираем все совпадения и добавляем центра каждого из них в centers.
        for point in zip(*locations[::-1]):
            center_x = point[0] + template_weight // 2
            center_y = point[1] + template_height // 2
            centers.append((center_x, center_y))

        return centers
