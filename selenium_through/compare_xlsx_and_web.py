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
file_handler = logging.FileHandler('./logs/comparison_xlsx_and_web.txt')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
# Добавляем обработчики к объекту логгера
logger.addHandler(file_handler)


def read_columns_from_xlsx(xlsx_template: str =XLSX_TEMPLATE) -> list:
    """Вернуть список наименований всех столбцов из шаблонного xlsx файла."""
    df = pd.read_excel(xlsx_template)
    columns_from_df = df.columns
    return columns_from_df


def give_columns_for_scrapping(columns: list) -> set:
    """Предоставить названия столбцов для скраппинга."""
    columns = list(columns)
    columns.extend(['Адрес места нахождения', 'Полное наименование юридического лица',
                    'Полное наименование', 'Номер записи в РАЛ испытательной лаборатории',
                    'Номер документа'])
    columns = set(columns)
    return columns


def write_viewed_numbers_to_file(text_file: str, viewed: list) -> None:
    """Записать номера просмотренных документов в файл."""
    with open(text_file, 'a') as file:
        for number in viewed:
            file.write(str(number) + '\n')


def read_viewed_numbers_of_documents(text_file: str) -> dict:
    """Прочитать номера просмотренных документов из файла."""
    with open(text_file, 'r') as file:
        list_of_viewed = file.read().split("\n")
        my_dict = {number: 0 for number in list_of_viewed}
        return my_dict


def write_to_excel_result_of_comparison(lists: list, path_to_excel: str):
    """Принять на вход несколько списков и записать их
    в excel файл в строки друг над другом с индексами слева."""
    data = {index: values for index, values in zip(INDEXES_FOR_DF, lists)}
    df = pd.DataFrame(data)
    df = df.transpose()  # Транспонирование DataFrame: строки становятся столбцами и наоборот.
    with pd.ExcelWriter(path_to_excel) as writer:
        df.to_excel(writer, index=True, header=False)
        # df.to_excel(writer, index=False)  Записать в 4 столбца


def scrapping_web_data_one_document(document_number: str, url: str,
                                    path_to_save: str):
    """Получить номер документа, собрать данные с ВЕБ-ресурса(по определенным колонки)
    и сохранить в xlsx файл."""

    scrapper = DataScrapper(url)
    scrapper.open_page()
    scrapper.input_document_number(document_number)
    columns = give_columns_for_scrapping(read_columns_from_xlsx())
    scrapper.get_needed_document_in_list(document_number)
    data_from_web = scrapper.get_data_on_document_by_columns(columns)
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
    path_to_save = path_to_save + '\\' + (document_number.
                                                         replace('/', '_')) + ".xlsx"
    write_to_excel_result_of_comparison(lists, path_to_save)


def compare_xlsx_and_web_datas(xlsx_data: pd.Series, web_data: dict) -> list:
    """Сравнить данные из xlsx и web."""
    # Названия колонок из xlsx
    columns = read_columns_from_xlsx(XLSX_TEMPLATE)[2:]
    # Списки для сохранения данных для последующей записи в EXCEL
    xlsx_list, web_list, results_list = [], [], []

    for column in columns:
        try:
            # Значение из ячейки xlsx файла
            xlsx = str(xlsx_data[column]).replace('\n', ' ').replace('  ', ' ').strip(' ').lower()
            xlsx_list.append(xlsx)
            # Значение из web
            web = str(web_data[column]).replace('\n', ' ').replace('  ', ' ').strip(' ').lower()
            web_list.append(web)

            # Если значения равны.
            if xlsx == web:
                results_list.append('Да')
            # Если значения неравны.
            else:
                results_list.append('Нет')

        # Если в WEB данных нет значения
        except KeyError:
            web_list.append('nan')
            if xlsx == 'nan':
                results_list.append('Да')
            else:
                results_list.append('Нет')

    # Результат в виде четырех списков, сопоставимых по индексам.
    lists = [columns, xlsx_list, web_list, results_list]
    return lists


def open_xlsx_and_launch_comparison(url: str, path_to_excel_with_numbers: str,
                                    dir_for_save_files: str):
    """Открыть xlsx файл, прочитать его, и запустить сравнения данных
    из xlsx файла и данных web. Функция будет читать значения
    в колонке номера деклараций, создавать экземпляр класса DataScrapper, через него
    сохранять данные с web, и запускать их сравнение."""

    # Читаем общий файл xlsx, конвертируем содержимое.
    df = pd.read_excel(path_to_excel_with_numbers, converters={
        'Основной государственный регистрационный '
        'номер юридического лица (ОГРН)': remove_decimal_from_xlsx,
        'Номер телефона': amend_phone_number,
        'Номер протокола': amend_protocols,
        'Дата протокола': amend_date_protocols,
        'Дата внесения в реестр сведений об аккредитованном лице': convert_date_format,
        'Дата окончания действия декларации о соответствии': convert_date_format
    })

    # Ранее просмотренные номера документов до текущего вызова функции.
    dict_of_viewed_numbers = read_viewed_numbers_of_documents(PATH_TO_VIEWED_NUMBERS)
    # Просмотренные номера документов в текущем вызове функции.
    list_of_viewed_that_will_be_written = []

    # Класс, собирающий данные по документам из web
    scrapper = DataScrapper(url)
    scrapper.open_page()

    # перебираем номера документов в колонке номеров деклараций
    try:
        for index, row in df.iterrows():
            document_number = row.iloc[1]
            # Если не передан номер или он в просмотренных, то пропустить.
            if str(document_number) == 'nan' or document_number in dict_of_viewed_numbers:
                continue

            # Иначе открываем декларацию в вебе и собираем данные
            scrapper.input_document_number(document_number)
            scrapper.get_needed_document_in_list(document_number)
            columns = give_columns_for_scrapping(read_columns_from_xlsx())
            data_from_web = scrapper.get_data_on_document_by_columns(columns)
            # Вносим ряд уточнений в словарь для последующего сравнения
            web_data = amend_web_data(data_from_web)
            # Данные по декларации из xlsx файла.
            xlsx_data = row

            # Запускаем сравнение, передаем строку из xlsx файла и данные из web.
            logger.info(f"Сравнение данных по декларации {document_number}")
            results_of_comparison = compare_xlsx_and_web_datas(xlsx_data, web_data)

            # Записать результат в excel файл.
            dec_num = (document_number.replace('/', '_'))
            path_to_store_new_files = dir_for_save_files + '/' + dec_num + ".xlsx"
            write_to_excel_result_of_comparison(results_of_comparison, path_to_store_new_files.replace('\n', '\\'))
            logger.info(f"Результаты сравнения данных по декларации "
                        f"{document_number} записаны в файл.")
            list_of_viewed_that_will_be_written.append(document_number)
            scrapper.return_to_input_number()

    except Exception as e:
        logger.error(f"При сравнении данных произошла ошибка: %s", str(e))

    finally:
        # Записать просмотренные номера деклараций в файл.
        write_viewed_numbers_to_file(PATH_TO_VIEWED_NUMBERS, list_of_viewed_that_will_be_written)
        logger.info(f"За сеанс проверены номера деклараций: {list_of_viewed_that_will_be_written}")

    scrapper.close_browser()


if __name__ == '__main__':
    open_xlsx_and_launch_comparison(URL, XLSX_TEMPLATE, DIR_WITH_XLSX_COMPARISON)
    # scrapping_web_data_one_document('ЕАЭС N RU Д-RU.РА03.В.34862/23', URL, DIR_SAVE_WEB_ON_DECLARATION)
