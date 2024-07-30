"""
Модуль для сбора данных по документам из программы GOLD.

Функции:
    - launch_gold_module:
        запуск всего кода в модуле
    - check_if_everything_is_checked:
        проверка, проверены ли все номера в ГОЛД.

Классы:
    - ADocDataCollector(GoldScreenShotWorker):
        сбор данных в ГОЛД на один документ.

    - GoldCollector(ADocDataCollector, GoldLauncher):
        сбор данных в ГОЛД для всех документов, идет построчно в файле two_columns
        и собирает по ним данные.
"""
import pandas as pd
import pyautogui
import pytesseract

from common.exceptions import StopIterationInGoldException
from common.logger_config import logger
from common.constants import (PATH_TO_TESSERACT, ScrForGold as ScreenShots,
                              FIREFOX_PROC, ProductCardFields,
                              Files, COLS_FOR_GOLD_DF, MsgForUser)

from common.work_with_files_and_dirs import (
    write_numb_to_file, read_numb_from_file,
    return_or_create_xlsx, dict_from_json_file,
    terminate_the_proc, create_copy_of_file, prepare_df_for_work)
from gold.launch_and_navigate import GoldMenuNavigator, GoldProcess

# Путь к файлам Tesseract OCR и poppler
pytesseract.pytesseract.tesseract_cmd = PATH_TO_TESSERACT
path_to_poppler = r'../../poppler-23.11.0/Library/bin'


class DocDataCollector(GoldMenuNavigator):
    """ Сбор данных в ГОЛД на один документ. """

    def get_data_about_doc(self, applicants_codes_and_name: dict) -> dict:
        """ Собираем данные в ГОЛД по одному документу из соответствующих полей."""
        doc_data = {}
        # Проверка, что провалились в декларацию.
        self.search_and_click(ScreenShots.DECLARATION_CARD.value, timeout=3)

        # Действия по сохранению данных в словарь, исходя из наименования поля.
        actions_for_fields = {
            ProductCardFields.REG_NUMBER_FIELD:
                lambda value: doc_data.update({'ДОС': '-' if value == '' else value}),
            ProductCardFields.MANUF_FIELD:
                lambda value: doc_data.update({'Изготовитель': '-' if value == '' else value}),
            ProductCardFields.DATE_OF_END:
                lambda value: doc_data.update({'Дата окончания': value.replace('/', '.')}),
            ProductCardFields.APPLICANT_CODE:
                lambda value: doc_data.update(
                    {'Заявитель': applicants_codes_and_name.get(str(value), 'Нет в JSON')})}

        # Цикл по полям карточки продукта.
        for field in ProductCardFields:
            self.search_and_click(field.value)
            x, y = pyautogui.position()
            pyautogui.click(x + 150, y)
            # Доп действие для кода заявителя.
            if field != ProductCardFields.APPLICANT_CODE:
                pyautogui.doubleClick()
            field_value = self.select_text_and_copy()
            # Сразу вызываем действие, полученное из словаря, и передаем в него field_value.
            actions_for_fields.get(field, lambda value: None)(field_value)

        return doc_data


class GoldCollector(DocDataCollector, GoldProcess):
    """ Сбор всех данных в GOLD. Читает построчно данные из TwoColumnsFile
    и собирает данные из ГОЛД."""

    def __init__(self, two_columns_file, gold_file, file_for_last_number):
        self.origin_df = pd.read_excel(two_columns_file)
        self.gold_file = return_or_create_xlsx(gold_file)
        self.last_viewed_numb = read_numb_from_file(file_for_last_number)
        self.new_df = prepare_df_for_work(self.gold_file, COLS_FOR_GOLD_DF)
        self.appl_codes_and_names = dict_from_json_file(
            Files.APPLICANTS_CODES_AND_NAME.value)

    def make_copy_of_gold_file(self, row_name):
        """ Сделать копию ГОЛД файла"""
        create_copy_of_file('copies_of_gold', row_name, self.new_df)

    def handle_no_data_error(self, row):
        """ При сообщении нет данных добавление соответствующей строки в результат"""
        new_ser = pd.Series(['Нет данных в GOLD'], index=['ДОС'])
        new_row = row._append(new_ser)  # Добавляем в DataFrame.
        self.new_df = self.new_df._append(new_row, ignore_index=True)  # Добавляем в DataFrame

    def get_data_from_all_docs_on_product(self, centres, row):
        """ Собрать информацию по всем документам на один код продукта. """
        item = 0  # Переменная для итерации по списку центров.
        while item < len(centres):
            pyautogui.doubleClick(centres[item])
            one_doc_data = self.get_data_about_doc(self.appl_codes_and_names)
            new_ser = pd.Series([one_doc_data['ДОС'], one_doc_data['Дата окончания'],
                                 one_doc_data['Изготовитель'], one_doc_data['Заявитель']],
                                index=['ДОС', 'Дата окончания', 'Изготовитель', 'Заявитель', ])
            # Новый Series добавляем в новый DF.
            new_row = row._append(new_ser)
            self.new_df = self.new_df._append(new_row, ignore_index=True)  # Добавляем в DataFrame
            self.press_back_in_gold()
            item += 1

    def append_data_to_result_df(self):
        """Получение данных из Gold по строкам через цикл."""
        # Перебираем построчно данные из файла с кодами и наименованиями продуктов .
        for _, row in self.origin_df[self.last_viewed_numb:].iterrows():

            # На каждой 500 строке сделать копию GOLD-файла(DataFrame)
            if row.name % 500 == 0 and row.name != 0:
                self.make_copy_of_gold_file(row.name)

            # Ввести номер кода товара
            product_number = row.loc['Код товара']  # Код товара из файла.
            self.input_using_offset(ScreenShots.PROD_INPUT_FIELD.value,
                                    product_number, 120)
            self.press_search_in_gold()

            # Дождаться загрузки страницы
            self.wait_scr_gone(ScreenShots.LOADING_PRODUCT.value)

            # Проверить и обработать сообщение на экране об отсутствии данных.
            error_no_data = self.handle_error_no_data()
            if error_no_data:
                self.handle_no_data_error(row)
                self.last_viewed_numb = row.name
                continue

            centres_of_docs = self.search_coords_of_all_docs()
            if centres_of_docs:  # Если найдены центры деклараций, то получаем данные.
                self.get_data_from_all_docs_on_product(centres_of_docs, row)

            self.last_viewed_numb = row.name
        write_numb_to_file(Files.LAST_VIEWED_IN_GOLD_NUMB.value,
                           self.last_viewed_numb)
        terminate_the_proc(FIREFOX_PROC)

    def process_append_data_to_result_df(self):
        """ Запустить код сбора данных через конструкцию try/except """
        try:
            self.activate_or_launch_gold()
            self.append_data_to_result_df()
        except Exception as error:
            if hasattr(error, 'msg'):
                logger.error(error.msg)
            else:
                logger.error(error)

            raise StopIterationInGoldException from error

        finally:
            self.new_df.to_excel(self.gold_file, index=False)
            write_numb_to_file(Files.LAST_VIEWED_IN_GOLD_NUMB.value,
                               self.last_viewed_numb)
            terminate_the_proc(FIREFOX_PROC)


def everything_is_checked(two_columns_file: str) -> bool | None:
    """ Проверка, проверены ли все номера в ГОЛД. """
    try:
        two_columns = pd.read_excel(two_columns_file)
        if two_columns.iloc[-1].name == read_numb_from_file(
                Files.LAST_VIEWED_IN_GOLD_NUMB.value):
            return True
        return False
    except (KeyError, FileNotFoundError):
        return None


def launch_gold_module(attempts_for_range: int, two_columns_file: str, gold_file: str) -> None:
    """ Запуск всего кода модуля. """
    for _ in range(attempts_for_range):
        if everything_is_checked(two_columns_file):
            logger.info(MsgForUser.ALL_IN_GOLD_CHECKED.value)
            print(MsgForUser.ALL_IN_GOLD_CHECKED.value)
            break

        try:
            logger.info(MsgForUser.NOT_ALL_IN_GOLD_CHECKED.value)
            print(MsgForUser.NOT_ALL_IN_GOLD_CHECKED.value)
            gold_collector = GoldCollector(two_columns_file,
                                           gold_file,
                                           Files.LAST_VIEWED_IN_GOLD_NUMB.value)
            gold_collector.process_append_data_to_result_df()
            print(MsgForUser.ALL_IN_GOLD_CHECKED.value)

        except StopIterationInGoldException as error:
            print(MsgForUser.CHECKED_NUMBER.value, gold_collector.last_viewed_numb)
            logger.error(error.msg)
