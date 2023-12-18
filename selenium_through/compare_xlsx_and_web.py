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
import logging
import pandas as pd
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
XLSX_TEMPLATE = (r"..\Шаблон для внесения информации по декларациям о "
                 r"соответствии второй.xlsx")
PATH_TO_VIEWED_NUMBERS = 'viewed_numbers.txt'
DIR_WITH_XLSX_COMPARISON = (r"C:\Users\RIMinullin\PycharmProjects"
                            r"\someProject\selenium_through\files_of_comparison")
DIR_SAVE_WEB_ON_DECLARATION = (r"C:\Users\RIMinullin\PycharmProjects"
                               r"\someProject\selenium_through\web_data_by_one_declaration")
INDEXES_FOR_DF = ['Поле для сравнения', 'EXCEL данные', 'WEB данные', 'Результат сравнения']


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


def read_columns_from_xlsx(xlsx_template: str = XLSX_TEMPLATE) -> list:
    """Вернуть список колонок из xlsx файла."""
    df = pd.read_excel(xlsx_template)
    columns_from_df = df.columns
    return columns_from_df


def give_columns_for_scrapping(columns: list) -> dict:
    """Предоставить словарем названия столбцов для скрапинга."""
    columns = list(columns)
    columns.extend(['Адрес места нахождения', 'Полное наименование юридического лица',
                    'Полное наименование', 'Номер записи в РАЛ испытательной лаборатории',
                    'Номер документа'])
    columns = {i: True for i in columns}
    return columns


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


def write_to_excel_result(lists: list, path_to_excel: str):
    """Принять на вход несколько списков и записать их
    в excel файл в строки друг над другом с индексами слева."""
    data = {index: values for index, values in zip(INDEXES_FOR_DF, lists)}
    df = pd.DataFrame(data)
    # Транспонирование DataFrame: строки становятся столбцами и наоборот
    df = df.transpose()
    with pd.ExcelWriter(path_to_excel) as writer:
        df.to_excel(writer, index=True, header=False)
        # df.to_excel(writer, index=False)  Записать в 4 столбца


def scrapping_one_declaration_and_save_to_xlsx(declaration_number: str, url: str = URL,
                                               path_to_save: str = DIR_SAVE_WEB_ON_DECLARATION):
    """Получить номер декларации и собрать данные по декларации с ВЕБ-ресурса"""
    scrapper = DataScrapper(url)
    scrapper.open_page()
    scrapper.input_declaration_number(declaration_number)
    columns = give_columns_for_scrapping(read_columns_from_xlsx())
    scrapper.get_needed_declaration_in_list(declaration_number)
    data_from_web = scrapper.get_data_on_declaration(columns)
    # Словарь с данными с WEB
    web_data = amend_web_data(data_from_web)
    # Сформировать два списка для записи в xlsx файл.
    columns = read_columns_from_xlsx()
    values = []

    # Перебираем значения из данных словаря по столбцам и добавляем их в результат.
    for column in columns:
        try:
            web_value = (str(web_data[column]).replace('\n', ' ').
                         replace('  ', ' ').strip(' ').lower())
            values.append(web_value)
        except Exception as e:
            values.append('nan')

    lists = [columns, values]
    path_to_save = DIR_SAVE_WEB_ON_DECLARATION + '\\' + declaration_number + ".xlsx"
    write_to_excel_result(lists, path_to_save)


def compare_xlsx_and_web_datas(xlsx_data: dict, web_data: dict) -> list:
    """Сравнить данные из xlsx и web."""
    # Названия колонок из xlsx
    columns = read_columns_from_xlsx(XLSX_TEMPLATE)[2:]

    # Списки для сохранения данных для последующей записи в EXCEL
    list_xlsx = []
    list_web = []
    list_results = []

    for column in columns:
        try:
            # Значение из ячейки xlsx файла
            xlsx = str(xlsx_data[column]).replace('\n', ' ').replace('  ', ' ').strip(' ').lower()
            list_xlsx.append(xlsx)
            # Значение из web
            web = str(web_data[column]).replace('\n', ' ').replace('  ', ' ').strip(' ').lower()
            list_web.append(web)

            # Если значения равны.
            if xlsx == web:
                list_results.append('Да')

            # Если значения неравны.
            list_results.append('Нет')

        except KeyError:
            list_web.append('nan')
            list_results.append('Нет')

    # Результат в виде четырех списков, сопоставимых по индексам.
    lists = [columns, list_xlsx, list_web, list_results]
    return lists


def open_xlsx_and_launch_comparison(path_to_excel: str):
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
        'Дата протокола': amend_date_protocols,
        'Дата внесения в реестр сведений об аккредитованном лице': convert_date_format,
        'Дата окончания действия декларации о соответствии': convert_date_format
    })
    # Ранее просмотренные номера деклараций до текущего вызова функции.
    dict_of_viewed_numbers = read_the_viewed_numbers_of_declarations(PATH_TO_VIEWED_NUMBERS)
    # Просмотренные номера деклараций в текущем вызове функции.
    list_of_viewed_that_will_be_written = []
    # Класс, собирающий данные по декларации из web
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

            # Иначе открываем декларацию в вебе и собираем данные
            scrapper.input_declaration_number(declaration_number)
            scrapper.get_needed_declaration_in_list(declaration_number)

            cols = give_columns_for_scrapping(read_columns_from_xlsx())
            data_from_web = scrapper.get_data_on_declaration(cols)
            # Вносим ряд уточнений в словарь для последующего сравнения
            web_data = amend_web_data(data_from_web)

            # Данные по декларации из xlsx файла.
            xlsx_data = row

            # Запускаем сравнение, передаем строку из xlsx файла и данные из web.
            logger.info(f"Сравнение данных по декларации {declaration_number}")
            results_of_comparison = compare_xlsx_and_web_datas(xlsx_data, web_data)

            # Записать результат в excel файл.
            dec_num = (declaration_number.replace('/', '_'))
            path_to_new_file = DIR_WITH_XLSX_COMPARISON + '/' + dec_num + ".xlsx"
            write_to_excel_result(results_of_comparison, path_to_new_file.replace('\n', '\\'))
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
    open_xlsx_and_launch_comparison(XLSX_TEMPLATE)
    # scrapping_one_declaration_and_save_to_xlsx('ЕАЭС N RU Д-RU.АД20.В.02785_20')


# import datetime
#
# start_time = datetime.datetime.now()
# open_xlsx_and_launch_comparison(XLSX_FILE)
# print('Время выполнения: ', datetime.datetime.now() - start_time)
