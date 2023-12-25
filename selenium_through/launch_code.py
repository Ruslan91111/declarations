"""Main module - to launch the code."""
import os

from selenium_through.compare_xlsx_and_web import (open_xlsx_and_launch_comparison,
                                                   DIR_WITH_XLSX_COMPARISON,
                                                   scrapping_web_data_one_document,
                                                   DIR_SAVE_WEB_ON_DECLARATION)

# Константы
URL_DECLARATION = "https://pub.fsa.gov.ru/rds/declaration"
URL_CERTIFICATES = "https://pub.fsa.gov.ru/rss/certificate"

DRIVER_PATH = r"C:\Users\RIMinullin\PycharmProjects\someProject\chromedriver.exe"

XLSX_TEMPLATE_DECLARATIONS = (r"..\Шаблон для внесения информации по декларациям о "
                              r"соответствии второй.xlsx")

XLSX_TEMPLATE_CERTIFICATES = r".\Шаблон для внесения информаци по СС.xlsx"


def input_xlsx_template(default_path_to_xlsx: str) -> str | None:
    """Ввести путь к шаблону html, содержащему основную информацию."""
    path_to_excel = input('Введите полный путь до EXCEL файла с данными '
                          'о декларациях, включая расширение файла. '
                          'Нажмите "Enter", если хотите использовать '
                          'текущую директорию.\n--> ')

    if not path_to_excel:
        path_to_excel = default_path_to_xlsx
        return path_to_excel

    elif not os.path.isfile(path_to_excel):
        print('Указанный файл не существует.')
        return None

    return path_to_excel


def input_path_to_save_xlsx_files(default_path: str):
    """Ввести путь к папке, в которую будут сохраняться файлы с результатами сравнения."""

    path_to_dir_for_files = input('Введите полный путь до директории, в которую будут сохранены '
                                  'файлы сравнения данных в формате xlsx.\nНажмите "Enter", '
                                  'если хотите использовать '
                                  'директорию по умолчанию.\n--> ')

    if not path_to_dir_for_files:
        return default_path

    else:
        path_to_dir_for_files = os.path.abspath(path_to_dir_for_files)
        if not os.path.exists(path_to_dir_for_files):
            os.makedirs(path_to_dir_for_files)
        return path_to_dir_for_files


def launch_compare_xlsx_and_web(xlsx_template: str, url: str):
    """Запуск кода сравнения данных."""
    path_to_excel_with_numbers = input_xlsx_template(default_path_to_xlsx=xlsx_template)
    if path_to_excel_with_numbers is None:
        return None
    dir_for_save = input_path_to_save_xlsx_files(DIR_WITH_XLSX_COMPARISON)

    # Запуск цикла сравнения данных их xlsx и web.
    open_xlsx_and_launch_comparison(url, path_to_excel_with_numbers, dir_for_save)
    scrapping_web_data_one_document('ЕАЭС N RU Д-RU.РА03.В.34862/23', url, DIR_SAVE_WEB_ON_DECLARATION)


if __name__ == '__main__':
    # Запустить сравнение данных в xlsx шаблоне.
    # С вводом путей
    # launch_compare_xlsx_and_web(XLSX_TEMPLATE_DECLARATIONS, URL_DECLARATION)

    # Без ввода
    open_xlsx_and_launch_comparison(URL_DECLARATION, XLSX_TEMPLATE_DECLARATIONS, DIR_WITH_XLSX_COMPARISON)

    # Собрать данные с веба по одной декларации.
    # scrapping_web_data_one_document('ЕАЭС N RU Д-RU.РА03.В.34862/23', URL, DIR_SAVE_WEB_ON_DECLARATION)

    # Запуск сравнение данных в xlsx шаблоне сертификаты
    # open_xlsx_and_launch_comparison(URL_CERTIFICATES, XLSX_TEMPLATE_CERTIFICATES, DIR_WITH_XLSX_COMPARISON)
