"""
Модуль для сравнения данных из xlsx и web.

Функции:
- compare_datas: сравнивает два словаря с данными.
- open_xlsx_and_launch_comparison: открывает файл xlsx и запускает сравнение данных через цикл for.
- read_columns_from_xlsx: возвращает названия колонок из файла.
- read_the_viewed_numbers_of_declarations: читает из файла и
возвращает словарем номера проверенных деклараций.
- write_viewed_numbers_to_file: записывает номера просмотренных деклараций в файл.
"""

import pandas as pd
import logging

from selenium_through.ammendments import amend_web_data
from selenium_through.converters_to_xlsx_data import (convert_date_format,
                                                      remove_decimal_from_xlsx,
                                                      amend_phone_number,
                                                      amend_protocols,
                                                      amend_date_protocols)
from selenium_through.data_scrapper import DataScrapper

# Константы
URL = "https://pub.fsa.gov.ru/rds/declaration"
DRIVER_PATH = r"C:\Users\RIMinullin\PycharmProjects\someProject\chromedriver.exe"
XLSX_FILE = r"..\Шаблон для внесения информации по декларациям о соответствии второй.xlsx"
PATH_TO_VIEWED_NUMBERS = 'viewed_numbers.txt'


# Создаем объект логгера.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Форматирование сообщений лога
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# Обработчик для записи логов в файл
file_handler = logging.FileHandler('result_of_comparison_xlsx_and_web.txt')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
# Создаем обработчик для вывода сообщений об ошибках на стандартный поток вывода
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)
stream_handler.setFormatter(formatter)
# Добавляем обработчики к объекту логгера
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def read_columns_from_xlsx(xlsx_template: str) -> list:
    """Вернуть список колонок из xlsx файла."""
    df = pd.read_excel(xlsx_template)
    columns_from_df = df.columns
    return columns_from_df


def write_viewed_numbers_to_file(text_file: str, viewed: list) -> None:
    """Записать номера просмотренных деклараций в файл."""
    with open(text_file, 'a') as file:
        for number in viewed:
            file.write(str(number) + '\n')


def read_the_viewed_numbers_of_declarations(text_file: str) -> dict:
    """Прочитать номера просмотренных деклараций из файла."""
    with open(text_file, 'r') as file:
        list_of_viewed = file.read().split("\n")
        my_dict = {number: 0 for number in list_of_viewed}
        return my_dict


def compare_datas(xlsx_data, web_data):
    """Сравнить данные из xlsx и web."""
    # Названия колонок из xlsx
    columns = read_columns_from_xlsx(XLSX_FILE)[2:]
    i = 1
    # Берем название одной колонки.
    for column in columns:
        try:
            # Берем значения по колонке из xlsx и web.
            xlsx = str(xlsx_data[column]).replace('\n', ' ').replace('  ', ' ').strip(' ').lower()
            web = str(web_data[column]).replace('\n', ' ').replace('  ', ' ').strip(' ').lower()
            # Если значения равны.
            if xlsx == web:
                # logger.info(f'====={i}=====\n'
                #             f'Значения равны по колонке*****{column}*****\n'
                #             f'в EXCEL файле -- {xlsx}\n'
                #             f'в WEB данных  -- {web}\n')
                i += 1
                continue

            # Если значения неравны.
            logger.info(f'====={i}=====\n'
                        f'НЕСООТВЕТСТВИЯ ДАННЫХ ПО КОЛОНКЕ *****{column}*****\n'
                        f'в EXCEL файле -- {xlsx}\n'
                        f'в WEB данных  -- {web}\n')
            i += 1

        except KeyError:
            logger.info(f'====={i}=====\n'
                        f'В WEB ДАННЫХ ОТСУТСТВУЕТ ЗНАЧЕНИЕ ДЛЯ КОЛОНКИ'
                        f'*****{column}*****\n'
                        f'в XLSX файле значение - {str(xlsx_data[column]).strip(" ")}')


def open_xlsx_and_launch_comparison(path_to_excel):
    """Открыть xlsx файл, прочитать его, и запустить сравнения данных
    из xlsx файла и данных web. Функция будет читать значения
    в колонке номера деклараций, создавать экземпляр класса DataScrapper, через него
    сохранять данные с web, и запускать их сравнение."""

    # Читаем общий файл xlsx, попутно убираем из xlsx файла из колонки ОГРН точки с 0.
    df = pd.read_excel(path_to_excel, converters={
        'Основной государственный регистрационный '
        'номер юридического лица (ОГРН)': remove_decimal_from_xlsx,
        'Номер телефона': amend_phone_number,
        'Номер протокола': amend_protocols,
        'Дата протокола':  amend_date_protocols,
        'Дата внесения в реестр сведений об аккредитованном лице': convert_date_format,
        'Дата окончания действия декларации о соответствии': convert_date_format
    })
    dict_of_viewed_numbers = read_the_viewed_numbers_of_declarations(PATH_TO_VIEWED_NUMBERS)
    list_of_viewed_that_will_be_written = []
    scrapper = DataScrapper(URL)
    scrapper.open_page()
    # перебираем номера деклараций в колонке номеров деклараций
    try:
        for index, row in df.iterrows():
            declaration_number = row.iloc[1]
            # Если не передан номер декларации или номер в словаре просмотренных,
            # то пропустить и перейти к следующему номеру.
            if str(declaration_number) == 'nan' or declaration_number in dict_of_viewed_numbers:
                continue
            # открываем декларацию в вебе и собираем данные
            scrapper.input_declaration_number(declaration_number)
            scrapper.get_needed_declaration_in_list(declaration_number)
            data_from_web = scrapper.get_data_on_declaration()
            # Вносим ряд уточнений в словарь для последующего сравнения
            web_data = amend_web_data(data_from_web)
            # Данные по декларации из xlsx файла.
            xlsx_data = row
            # Запускаем сравнение, передаем строку из xlsx файла и данные из web.
            logger.info(f"Сравнение данных по декларации {declaration_number}")
            compare_datas(xlsx_data, web_data)
            list_of_viewed_that_will_be_written.append(declaration_number)
            scrapper.return_to_input_number()

    except Exception as e:
        logger.error("Произошла ошибка: %s", str(e))

    finally:
        # Записать просмотренные номера деклараций в файл.
        write_viewed_numbers_to_file(PATH_TO_VIEWED_NUMBERS,
                                     list_of_viewed_that_will_be_written)
        logger.info(f"Проверены номера деклараций: {list_of_viewed_that_will_be_written}")


if __name__ == '__main__':
    open_xlsx_and_launch_comparison(XLSX_FILE)
