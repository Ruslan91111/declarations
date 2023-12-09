import pandas as pd
import logging

from selenium_through.ammendments import amend_web_data
from selenium_through.converters_to_xlsx_data import convert_date_format, remove_decimal_from_xlsx, amend_phone_number, \
    amend_protocols, amend_date_protocols
from selenium_through.data_scrapper import DataScrapper

# Константы
URL = "https://pub.fsa.gov.ru/rds/declaration"
DRIVER_PATH = r"C:\Users\RIMinullin\PycharmProjects\someProject\chromedriver.exe"
XLSX_FILE = r"..\Шаблон для внесения информации по декларациям о соответствии.xlsx"


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('result_of_comparison_xlsx_and_web.txt')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)


def read_columns_from_xlsx(xlsx_template: str) -> list:
    """Вернуть список колонок из xlsx файла."""
    df = pd.read_excel(xlsx_template)
    columns_from_df = df.columns
    return columns_from_df


def compare_datas(xlsx_data, web_data):
    """Сравнить данные из xlsx и web."""
    # Названия колонок из xlsx
    columns = read_columns_from_xlsx(XLSX_FILE)[2:]
    i = 1
    # Берем название одной колонки.
    for column in columns:
        try:
            # Берем значения по колонке из xlsx и web.
            xlsx = str(xlsx_data[column]).replace('\n', '').strip(' ')
            web = str(web_data[column]).replace('\n', '').strip(' ')
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
            print('НЕТ ПОЛЯ В WEB ДАННЫХ', column)
            logger.info(f'====={i}=====\n'
                        f'В WEB ДАННЫХ ОТСУТСТВУЕТ ЗНАЧЕНИЕ ДЛЯ КОЛОНКИ'
                        f'*****{column}*****\n'
                        f'а в XLSX {str(xlsx_data[column]).strip(" ")}')


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

    scrapper = DataScrapper(URL)
    scrapper.open_page()

    # перебираем номера деклараций в колонке номеров деклараций
    for index, row in df.iterrows():
        declaration_number = row.iloc[1]

        scrapper.input_declaration_number(declaration_number)
        scrapper.get_needed_declaration_in_list(declaration_number)
        data_from_web = scrapper.get_data_on_declaration()
        # Вносим ряд уточнений в словарь для последующего сравнения
        web_data = amend_web_data(data_from_web)

        # Собрать данные из xlsx файла, попутно привести дату к единому внешнему виду.
        xlsx_data = row
        columns = read_columns_from_xlsx(path_to_excel)[2:]

        # Запускаем сравнение, передаем строку из xlsx файла и путь к ПДФ файлу.
        logger.info(f"Сравнение данных по декларации {declaration_number}")
        compare_datas(xlsx_data, web_data)
        scrapper.return_to_input_number()


if __name__ == '__main__':
    open_xlsx_and_launch_comparison(XLSX_FILE)
