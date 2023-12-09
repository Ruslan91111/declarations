import PyPDF2
import pandas as pd
import logging

from ammendments_to_pdf import append_tech_regulations, append_OGRN_INN, \
    append_address_applicant_and_manufacturer_and_production, \
    append_indents_before_contact_and_common, remove_extra_indent, append_code_tn, append_space_after_lab, \
    append_name_of_applicant_and_manufacturer, append_test_carried, \
    separate_int_and_str, remove_space_in_phone_number, remove_substrings, remove_substrings_second, \
    append_condition_of_storage, append_title_of_doc, append_prothokols

PDF_PATH = r'..\Выписка по ДС № ЕАЭС N RU Д-RU.РА03.В.41616_23 от 2023-11-29.pdf'
TEMPLATE_XLSX = r'C:\Users\RIMinullin\PycharmProjects\someProject\Шаблон для внесения информации по декларациям о соответствии.xlsx'
TEXT_FILE = '../text.txt'

# Настройки логера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('log.txt')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def convert_pdf_to_one_str(path_to_pdf: str) -> str:
    """Прочитать ПДФ и преобразовать все его содержимое к одной строке."""
    with open(path_to_pdf, 'rb') as file:
        reader_pdf = PyPDF2.PdfReader(file)
        # Считаем количество страниц в pdf файле.
        count_of_pages = len(reader_pdf.pages)
        # Заводим литеру строки, куда будем добавлять строки из PDF файла.
        all_text = ''
        # Извлекаем строки из PDF постранично и формируем одну строку.
        for i in range(count_of_pages):
            page = reader_pdf.pages[i]
            page_content = page.extract_text()
            all_text += page_content
    return all_text.replace('  ', ' ')


def write_text_to_file(text_file: str, text_from_pdf: str) -> None:
    """Write str to file"""
    with open(text_file, 'w') as file:
        file.write(text_from_pdf)


def read_columns_from_xlsx(xlsx_template: str) -> list:
    """Read xlsx file and return list of columns."""
    df = pd.read_excel(xlsx_template)
    columns_from_df = df.columns
    return columns_from_df

# для простых пар
def find_one_item_in_text(text: str, substr: str) -> dict:
    """Найти пару ключ-значение в тексте, ключами будут колонки из xlsx файла."""
    # Найти начало и конец ключа.
    index_key_start = text.find(substr)
    ind_key_end = text.find(substr) + len(substr)
    # Сформировать подстроку для ключа.
    key = text[index_key_start:ind_key_end]
    # Найти начало и конец значения. Начало - символ после ключа.
    # Конец - знак абзаца
    ind_value_start = ind_key_end + 1
    ind_value_end = text.find('\n', ind_key_end, -1)
    # Сформировать подстроку для значения.
    value = text[ind_value_start:ind_value_end].strip(' ')
    return {key: value}


simple_cols = ('Тип объекта декларирования', 'Схема декларирования',
              'Фамилия руководителя юридического лица',
              'Имя руководителя юридического лица', 'Отчество руководителя юридического лица',
              'Должность руководителя', 'Номер телефона', 'Адрес электронной почты',
              'Происхождение продукции', 'Номер аттестата аккредитации испытательной\nлаборатории',
              'Дата внесения в реестр сведений об аккредитованном лице',
              'Дата окончания действия декларации о соответствии',
              'Статус декларации')


def find_all_simple_items_in_text(text: str, keys: tuple = simple_cols):
    """Fill the dict "key-value" from text from pdf."""
    dict_from_text = {}
    # Ключи будут - столбцы из xlsx файла.
    for key in keys:
        # Берем ключ и находим ему значение в тексте, и добавляем пару в словарь.
        key_value = find_one_item_in_text(text, key)
        dict_from_text.update(key_value)
    return dict_from_text


def convert_pdf_to_dict(pdf_path: str = PDF_PATH) -> dict:
    """Read PDF and return dict for comparison."""
    # Текст из ПДФ преобразовываем в одну строку.
    str_pdf = convert_pdf_to_one_str(pdf_path)
    write_text_to_file('new.txt', str_pdf)

    # Удалить подстроки со страницами
    str_pdf = remove_substrings(str_pdf)
    str_pdf = remove_substrings_second(str_pdf)


    # В тексте добавить пробел, где цифры и буквы идут без пробелов.
    str_pdf = separate_int_and_str(str_pdf)



    # Добавить абзац перед 'контактные' и 'общее наименование
    str_pdf = append_indents_before_contact_and_common(str_pdf)

    # Заменить ненужные переносы между предлогами.
    str_pdf = remove_extra_indent(str_pdf)

    # Добавить пробелы после 'лаборатории'.
    str_pdf = append_space_after_lab(str_pdf)

    # Удалить лишний пробел в телефонном номере
    str_pdf = remove_space_in_phone_number(str_pdf)

    # Выберем названия колонок из шаблона xlsx.
    columns = read_columns_from_xlsx(TEMPLATE_XLSX)

    # Преобразуем текст в словарь.
    dict_result = find_all_simple_items_in_text(str_pdf)


    # Вот сюда добавить дополнительные условия
    # вручную формируем пары ключ - значение.
    append_tech_regulations(str_pdf, dict_result)
    append_OGRN_INN(str_pdf, dict_result)
    append_code_tn(str_pdf, dict_result)
    append_address_applicant_and_manufacturer_and_production(str_pdf, dict_result)
    append_name_of_applicant_and_manufacturer(str_pdf, dict_result)
    append_test_carried(str_pdf, dict_result)
    append_condition_of_storage(str_pdf, dict_result)
    append_title_of_doc(str_pdf, dict_result)
    append_prothokols(str_pdf, dict_result)
    return dict_result


if __name__ == '__main__':
    convert_pdf_to_dict()
