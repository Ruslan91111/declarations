import os
from datetime import datetime
import re
import pandas as pd
import logging

from pdf_through.download_pdfs import SeleniumDownloadPdfs, URL
from work_with_pdf import convert_pdf_to_dict, read_columns_from_xlsx, TEMPLATE_XLSX

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('comparison.txt')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)


def convert_date_format(date_str):
    """Привести строку с датой к определенному виду"""
    try:
        # Преобразование строки в объект datetime
        date = datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S')
        # Преобразование объекта datetime в нужный формат
        formatted_date = date.strftime('%d.%m.%Y')
        return formatted_date
    except ValueError:
        return date_str


def remove_decimal_from_xlsx(x):
    try:
        return int(float(x))
    except ValueError:
        return x


def find_file(folder_path, sub_string):
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if sub_string in file_name:
                full_path = os.path.join(root, file_name)
                return full_path
    return None


def compare_xlsx_and_pdf(xlsx_data, pdf_data):
    """Сравнить строку из XLSX и PDF файл.
    Условно получает два словаря и сравнивает между собой"""
    xlsx_file = TEMPLATE_XLSX
    # Названия столбцов по-другому взять
    columns = read_columns_from_xlsx(xlsx_file)[2:]

    i = 1
    for column in columns:
        if column not in pdf_data:
            logger.info(f'====={i}=====\n'
                        f'Колонка ***{column}*** не найдена в PDF файле\n')
            i += 1
            continue
        if xlsx_data[column] == pdf_data[column]:
            continue

        logger.info(f'====={i}=====\n'
                    f'Несоответствие данных по колонке ***{column}***\n'
                    f'в EXCEL файле -- \n{xlsx_data[column]}\n'
                    f'в PDF файле -- \n{pdf_data[column]}\n')
        i += 1


def open_xlsx_find_pdf(path_to_excel):
    """Проверить наличие файла pdf по нужному номеру декларации."""

    # Путь к папке с ПДФ файлами.
    folder_path = r'C:\Users\RIMinullin\PycharmProjects\someProject'

    # Читаем общий файл xlsx
    df = pd.read_excel(path_to_excel, converters={
        'Основной государственный регистрационный '
        'номер юридического лица (ОГРН)': remove_decimal_from_xlsx
    })

    # перебираем номера деклараций в колонке номеров деклараций
    for index, row in df.iterrows():
        number_decl = row[1].replace("/", "_")

        # Ищем ПДФ файл в папке. Вернет либо None, либо путь к файлу
        pdf_path = find_file(folder_path, number_decl)

        # Если файл пдф не найден, то запускаем selenium, находим и скачиваем нужный файл ПДФ.
        if pdf_path is None:
            selenium = SeleniumDownloadPdfs(URL)
            selenium.goto_url()

            selenium.input_declaration(number_decl)
            selenium.click_download_pdf_declaration()
            # Сохранить путь к файлу при скачивании и запустить сравнение.

        # Если ПДФ файл найден
        if pdf_path is not None:

            # Данные из ПДФ файла в словарь
            pdf_data = convert_pdf_to_dict(pdf_path)

            # Собрать данные из xlsx файла, попутно привести дату к единому внешнему виду.
            xlsx_data = row
            columns = read_columns_from_xlsx(TEMPLATE_XLSX)[2:]
            for column in columns:
                if str(type(xlsx_data[column])) == "<class 'datetime.datetime'>":
                    xlsx_data[column] = convert_date_format(xlsx_data[column])
                if str(type(xlsx_data[column])) != "<class 'str'>":
                    xlsx_data[column] = str(xlsx_data[column])

            # Запускаем сравнение, передаем строку из xlsx файла и путь к ПДФ файлу.
            logger.info(f"Сравнение данных по декларации {row[1]}")
            compare_xlsx_and_pdf(xlsx_data, pdf_data)


if __name__ == '__main__':
    open_xlsx_find_pdf(TEMPLATE_XLSX)
