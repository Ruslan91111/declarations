from datetime import datetime
import pandas as pd
import logging

from selenium_through.ammendments import amend_web_data
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


def convert_date_format(date_str: str) -> str:
    """Привести строку с датой к определенному виду"""
    # Строку из xlsx вида 2020-10-20 00:00:00 привести к виду 20.10.2020
    try:
        # Преобразование строки в объект datetime
        date = datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S')
        # Преобразование объекта datetime в нужный формат
        formatted_date = date.strftime('%d.%m.%Y')
        return formatted_date
    except ValueError:
        return date_str


def remove_decimal_from_xlsx(number: str):
    """Убрать у числа точку и значения после точки."""
    # В xlsx файле есть поля, где точка с цифрами
    # передается при чтении xlsx файла pandas.
    try:
        return int(float(number))
    except ValueError:
        return number


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
            xlsx = xlsx_data[column].strip(' ')
            web = web_data[column].strip(' ')

            # Если значения равны.
            if xlsx == web:
                logger.info(f'====={i}=====\n'
                            f'Значения равны по колонке*****{column}*****\n'
                            f'в EXCEL файле -- {xlsx}\n'
                            f'в WEB данных  -- {web}\n')
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
                        f'а в XLSX {xlsx_data[column].strip(" ")}')


def open_xlsx_and_launch_comparison(path_to_excel):
    """Открыть xlsx файл, прочитать его, и запустить сравнения данных
    из xlsx файла и данных web. Функция будет читать значения
    в колонке номера деклараций, создавать экземпляр класса DataScrapper, через него
    сохранять данные с web, и запускать их сравнение."""

    # Читаем общий файл xlsx, попутно убираем из xlsx файла из колонки ОГРН точки с 0.
    df = pd.read_excel(path_to_excel, converters={
        'Основной государственный регистрационный '
        'номер юридического лица (ОГРН)': remove_decimal_from_xlsx
    })

    # перебираем номера деклараций в колонке номеров деклараций
    for index, row in df.iterrows():
        declaration_number = row.iloc[1]
        scrapper = DataScrapper(URL)
        scrapper.open_declaration(declaration_number)
        data_from_web = scrapper.get_data_on_declaration()
        # Вносим ряд уточнений в словарь для последующего сравнения
        web_data = amend_web_data(data_from_web)

        # Собрать данные из xlsx файла, попутно привести дату к единому внешнему виду.
        xlsx_data = row
        columns = read_columns_from_xlsx(path_to_excel)[2:]

        for column in columns:
            # Привести дату в xlsx к определенному виду.
            if str(type(xlsx_data[column])) == "<class 'datetime.datetime'>":
                xlsx_data[column] = convert_date_format(xlsx_data[column])
            # Привести все данные к строкам.
            if str(type(xlsx_data[column])) != "<class 'str'>":
                xlsx_data[column] = str(xlsx_data[column])

        # Запускаем сравнение, передаем строку из xlsx файла и путь к ПДФ файлу.
        logger.info(f"Сравнение данных по декларации {declaration_number}")
        compare_datas(xlsx_data, web_data)


if __name__ == '__main__':
    open_xlsx_and_launch_comparison(XLSX_FILE)
