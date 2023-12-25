"""Main module - to launch the code."""
import os

from selenium_through.compare_xlsx_and_web import (
    open_xlsx_and_launch_comparison, scrapping_web_data_one_document)

from selenium_through.config import (
    DIR_SAVE_WEB_ON_DECLARATION, URL_DECLARATION, XLSX_TEMPLATE_DECLARATIONS,
    PATH_TO_VIEWED_NUMBERS_DECLARATIONS, URL_CERTIFICATES, XLSX_TEMPLATE_CERTIFICATES,
    DIR_SAVE_WEB_ON_CERTIFICATES, PATH_TO_VIEWED_NUMBERS_CERTIFICATES, XLSX_ONE_DECLARATION, XLSX_ONE_CERTIFICATE)


def choice_type_of_docs() -> dict:
    """Выбрать работу с декларациями или сертификатами."""
    try:
        type_of_doc = int(input('Введите 1, если работа с декларациями,'
                                ' 2, если с сертификатами, после чего нажмите '
                                '"Enter".\n--> '))
        if type_of_doc == 1:
            return {'url': URL_DECLARATION,
                    'path_to_excel_with_numbers': XLSX_TEMPLATE_DECLARATIONS,
                    'dir_for_save_files': DIR_SAVE_WEB_ON_DECLARATION,
                    'type_of_doc': 1,
                    'path_to_viewed': PATH_TO_VIEWED_NUMBERS_DECLARATIONS,
                    'path_to_save_one_doc': XLSX_ONE_DECLARATION}

        elif type_of_doc == 2:
            return {'url': URL_CERTIFICATES,
                    'path_to_excel_with_numbers': XLSX_TEMPLATE_CERTIFICATES,
                    'dir_for_save_files': DIR_SAVE_WEB_ON_CERTIFICATES,
                    'type_of_doc': 2,
                    'path_to_viewed': PATH_TO_VIEWED_NUMBERS_CERTIFICATES,
                    'path_to_save_one_doc': XLSX_ONE_CERTIFICATE}

        else:
            print('Неверный ввод')
    except KeyError:
        "Введена не цифра"


def input_xlsx_template(default_path_to_xlsx: str) -> str | None:
    """Ввести путь к шаблону xlsx, содержащему основную информацию."""
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
        return None

    else:
        path_to_dir_for_files = os.path.abspath(path_to_dir_for_files)
        if not os.path.exists(path_to_dir_for_files):
            os.makedirs(path_to_dir_for_files)
        return path_to_dir_for_files


def launch_compare_xlsx_and_web():
    """Запуск кода сравнения данных."""
    default_dict = choice_type_of_docs()
    path_to_excel_with_numbers = input_xlsx_template(default_path_to_xlsx=default_dict["path_to_excel_with_numbers"])
    if path_to_excel_with_numbers is None:
        pass
    else:
        default_dict["path_to_excel_with_numbers"] = path_to_excel_with_numbers

    dir_for_save_files = input_path_to_save_xlsx_files(default_dict['dir_for_save_files'])

    if dir_for_save_files is None:
        pass
    else:
        default_dict["dir_for_save_files"] = dir_for_save_files

    # Запуск цикла сравнения данных их xlsx и web.
    open_xlsx_and_launch_comparison(default_dict['url'],
                                    default_dict['path_to_excel_with_numbers'],
                                    default_dict['dir_for_save_files'],
                                    default_dict["type_of_doc"],
                                    default_dict['path_to_viewed'])


def input_document_number():
    """Ввести номер документа."""
    document_number = input('Введите номер документа.')
    return document_number


def launch_scraping_one_doc():
    """Запуск кода получения данных с веба об одном документе."""
    # Выбрать тип документа и набор переменных по умолчанию.
    default_dict = choice_type_of_docs()
    document_number = input_document_number()
    path_to_template = input_xlsx_template(default_path_to_xlsx=default_dict["path_to_excel_with_numbers"])
    if path_to_template is None:
        pass
    else:
        default_dict["path_to_excel_with_numbers"] = path_to_template

    path_to_save_one_doc = input_path_to_save_xlsx_files(default_dict['path_to_save_one_doc'])
    if path_to_save_one_doc is None:
        pass
    else:
        default_dict["path_to_save_one_doc"] = path_to_save_one_doc

    # Запуск получения данных.
    scrapping_web_data_one_document(
        default_dict['url'], document_number, default_dict["type_of_doc"],
        default_dict["path_to_save_one_doc"], default_dict['path_to_excel_with_numbers'])


def main_func():
    which_func = int(input('Введите 1, если необходимо запустить функцию сравнения данных из XLSX файла.\n'
                           'Введите 2, если необходимо получить сведения об одном документе, '
                           'после чего нажмите "Enter".\n--> '))
    try:
        if int(which_func) == 1:
            launch_compare_xlsx_and_web()
        elif int(which_func) == 2:
            launch_scraping_one_doc()
        else:
            print('Введено неверное значение. Необходимо внести 1, либо 2.')
    except ValueError:
        print(print('Ошибка ввода, необходимо внести 1, либо 2.'))


if __name__ == '__main__':
    main_func()
