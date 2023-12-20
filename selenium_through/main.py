import os

from selenium_through.compare_xlsx_and_web import (scrapping_web_data_one_document,
                                                   open_xlsx_and_launch_comparison,
                                                   XLSX_TEMPLATE, DIR_WITH_XLSX_COMPARISON)


def input_xlsx_template(default_path_to_xlsx: str):
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


def input_type_of_doc():
    type_of_doc = input('Введите 1, либо просто нажмите "Enter", если работа будет с декларациями, '
                        '2 если с сертификатами.\n--> ')
    if type_of_doc.strip() == '1' or not type_of_doc:
        type_of_doc = 1
        return type_of_doc
    elif type_of_doc.strip() == '2':
        type_of_doc = 2
        return type_of_doc
    else:
        print('Введено неверное значение.')
        return None


def input_path_to_save_xlsx_files(default_path: str):
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


def launch_compare_xlsx_and_web():
    path_to_excel_with_numbers = input_xlsx_template(default_path_to_xlsx=XLSX_TEMPLATE)
    if path_to_excel_with_numbers is None:
        return None
    type_of_doc = input_type_of_doc()
    if type_of_doc is None:
        return None
    dir_for_save = input_path_to_save_xlsx_files(DIR_WITH_XLSX_COMPARISON)
    # Запуск цикла сравнения данных их xlsx и web.
    open_xlsx_and_launch_comparison(path_to_excel_with_numbers, type_of_doc, dir_for_save)
    # scrapping_web_data_one_document('ЕАЭС N RU Д-RU.РА03.В.34862/23')


if __name__ == '__main__':
    launch_compare_xlsx_and_web()

# import datetime
#
# start_time = datetime.datetime.now()
# open_xlsx_and_launch_comparison(XLSX_TEMPLATE)
# print('Время выполнения: ', datetime.datetime.now() - start_time)
