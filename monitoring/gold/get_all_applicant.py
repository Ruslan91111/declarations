"""
Модуль содержит функции и класс, для сбора в json файл кодов и наименований заявителей.

ГОЛД перебирает и сохраняет в словарь в качестве ключа - код, в качестве значения -
наименование поставщиков. В последующем записывает словарь в файл json формата.

Класс:

    - CodesAndNamesExtractor:
        Сборщик кодов и наименований заявителей.

    - CodeAndNamesManager:
        Организация сбора данных по кодом и наименованиям заявителей и сохранение в файл.

        Основные методы:
            - code_manager.process_collect_from_current() - сбор данных с первого кода
            - code_manager.process_collect_from_none() - сбор данных с текущего кода


Пример использования:
    - Создание экземпляра класса:
        code_manager = CodeAndNamesManager(MAIN_CODES_AND_NAME, NEW_CODES_AND_NAME)
    - Вызов одного из двух методов:
        - code_manager.process_collect_from_current()
        - code_manager.process_collect_from_none()

"""
import json
import time
import pyautogui
import pyperclip

from common.constants import ScrForGold
from common.work_with_files_and_dirs import dict_from_json_file
from gold.launch_and_navigate import GoldProcess


PRODUCT_NUMB_FOR_START = '2000269222'
MAIN_CODES_AND_NAME = 'dict_applicant.json'
NEW_CODES_AND_NAME = 'dict_applicant_new.json'


class CodesAndNamesExtractor(GoldProcess):
    """ Сборщик кодов и наименований заявителей. """

    def __init__(self, start_prod_numb=None):
        self.start_prod_numb = start_prod_numb
        self.appl_dict = {}
        self.code_and_name = []

    def start_gold(self):
        """ Запуска программы ГОЛД"""
        self.activate_or_launch_gold()

    def prepare_for_collect(self):
        """ Выполнить подготовительные действия для сбора кодов и наименований организаций.
         То есть, пройти от меню до карточки товара, включительно. """
        self.input_using_offset(ScrForGold.PROD_INPUT_FIELD.value,
                                self.start_prod_numb, 120)
        self.press_search_in_gold()
        self.wait_scr_gone(ScrForGold.LOADING_PRODUCT.value)

        if self.handle_error_no_data():
            print('Данного номера товара в ГОЛД. Попробуйте другой.')
            raise ValueError("Product number does not exist in GOLd")

        centres = self.search_coords_of_all_docs()
        # Кликаем по первому документу
        pyautogui.doubleClick(centres[0])
        # Дождаться, загрузки страницы
        self.wait_scr_gone(ScrForGold.LOADING_PRODUCT.value)
        self.wait_scr_gone(ScrForGold.DECLARATION_CARD.value)

    def clear_buffer(self):
        """ Очистить буфер перед копированием. """
        pyperclip.copy("")

    def click_on_applicant(self):
        """ Кликнуть на список поставщиков и их коды. """
        self.search_and_click(ScrForGold.APPLICANT_CODE.value)
        x, y = pyautogui.position()
        pyautogui.moveTo(x + 80, y)
        time.sleep(0.2)
        pyautogui.doubleClick()
        time.sleep(3)

    def get_code_and_name(self):
        """ Сохранить код и наименование заявителя. """
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        row_applicant = pyperclip.paste()
        self.code_and_name = row_applicant.split('\t')

    def collect_codes_and_names(self):
        """ Сбор всех кодов и наименований через прокрутку в приложении ГОЛД. """

        self.clear_buffer()
        self.click_on_applicant()

        current_applicant = 'a'  # Переменная для текущего кода и поставщика.
        prev_applicant = ''  # Переменная для хранения предыдущего поставщика.

        while current_applicant != prev_applicant:
            time.sleep(0.2)
            prev_applicant = current_applicant

            self.get_code_and_name()

            if len(self.code_and_name) < 2:
                continue

            current_applicant = self.code_and_name
            self.appl_dict[self.code_and_name[0]] = self.code_and_name[1]
            self.clear_buffer()
            pyautogui.hotkey('down')
            time.sleep(0.2)

    def save_to_json(self, output_json):
        """ Сохранить коды и наименования в json файл. """
        with open(output_json, 'w') as file:
            json.dump(self.appl_dict, file)


class CodeAndNamesManager:
    """ Организация сбора данных по кодом и наименованиям заявителей и с охранение в
    файл. """
    def __init__(self, main_json: str, new_json: str):
        self.handler = CodesAndNamesExtractor()
        self.main_json = main_json
        self.new_json = new_json

    def get_codes_from_none(self):
        """ Набор действий для полного сбора данных,
        начиная с запуска программы ГОЛД. """
        self.handler.start_prod_numb = PRODUCT_NUMB_FOR_START
        self.handler.start_gold()
        self.handler.prepare_for_collect()
        self.handler.collect_codes_and_names()

    def get_codes_from_current(self) -> None:
        """ Набор действий для сбора данных, с текущего кода заявителя. """
        self.handler.collect_codes_and_names()

    def save_results(self):
        """ Набор действий по сохранению и вывод последнего кода. """
        self.handler.save_to_json(self.new_json)
        self.union_old_and_new_json()
        last = list(self.handler.appl_dict.keys())[-1]
        print(f'Последний обработанный код {last}')

    def process_collect_from_none(self) -> None:
        """ Организовать сбор всех кодов и наименований заявителей c самого начала. """
        try:
            self.get_codes_from_none()

        except Exception as e:
            print(f'Произошла ошибка в обработке поставщиков: {e}')

        finally:
            self.save_results()

    def process_collect_from_current(self) -> None:
        """ Организовать сбор всех кодов и наименований заявителей c текущего кода. """
        try:
            self.get_codes_from_current()

        except Exception as e:
            print(f'Произошла ошибка в обработке поставщиков: {e}')

        finally:
            self.save_results()

    def union_old_and_new_json(self):
        """ Объединить старый и новый набор кодов и записать в файл. """
        old = dict_from_json_file(self.main_json)
        new = dict_from_json_file(self.new_json)
        old.update(new)
        with open(self.main_json, 'w') as file:
            json.dump(old, file)
