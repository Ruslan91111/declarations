import PyPDF2
import pandas as pd
import logging

from ammendments_to_pdf import append_tech_regulations, append_OGRN_INN, append_address_applicant, \
    append_indents, append_address_manufacturer, remove_extra_indent, append_code_tn, space_after_lab, \
    divide_int_and_str, append_name_of_applicant_and_manufacturer, append_test_carried, append_name_of_product

PDF_PATH = r'../Выписка по ДС № ЕАЭС N RU Д-RU.РА03.В.41616_23 от 2023-11-29.pdf'
TEMPLATE_XLSX = r'../Шаблон для внесения информации по декларациям о соответствии.xlsx'
TEXT_FILE = '../text.txt'

# Настройки логера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('log.txt')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def pdf_to_str(path_to_pdf: str) -> str:
    """Read PDF file, convert and return one big str."""
    with open(path_to_pdf, 'rb') as file:
        read_pdf = PyPDF2.PdfReader(file)
        # Считаем количество страниц в pdf файле.
        count_of_pages = len(read_pdf.pages)
        # Заводим литеру строки, куда будем добавлять строки из PDF файла.
        all_text = ''
        # Извлекаем строки из PDF постранично
        for i in range(count_of_pages):
            page = read_pdf.pages[i]
            page_content = page.extract_text()
            all_text += page_content
    return all_text


def write_text_to_file(text_file: str, text_from_pdf: str) -> None:
    """Write str to file"""
    with open(text_file, 'w') as file:
        file.write(text_from_pdf)


def read_columns_from_xlsx(xlsx_template: str) -> list:
    """Read xlsx file and return list of columns."""
    df = pd.read_excel(xlsx_template)
    columns_from_df = df.columns
    return columns_from_df


def find_item(text: str, substr: str) -> dict:
    """Find key:value in text from pdf by name of columns in xlsx template."""
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
    value = text[ind_value_start:ind_value_end]
    return {key: value}


def convert_text_to_dict(text: str, keys: list):
    """Fill the dict "key-value" from text from pdf."""
    dict_from_text = {}
    # Ключи будут - столбцы из xlsx файла.
    for key in keys:
        # Берем ключ и находим ему значение в тексте, и добавляем пару в словарь.
        key_value = find_item(text, key)
        dict_from_text.update(key_value)
    return dict_from_text


def convert_pdf_to_dict() -> dict:
    """Read PDF and return dict for comparison."""
    # Из пдф в строку.
    str_pdf = pdf_to_str(PDF_PATH)
    write_text_to_file('before.txt', str_pdf)


    str_pdf = divide_int_and_str(str_pdf)
    write_text_to_file('after_address.txt', str_pdf)

    str_pdf = append_indents(str_pdf)

    write_text_to_file('after_str_pdf.txt', str_pdf)
    str_pdf = remove_extra_indent(str_pdf)
    str_pdf = space_after_lab(str_pdf)



    # Запишем в файл.
    write_text_to_file(TEXT_FILE, str_pdf)
    # Выберем названия колонок из шаблона xlsx.
    columns = read_columns_from_xlsx(TEMPLATE_XLSX)
    # Преобразуем текст в словарь.
    dict_result = convert_text_to_dict(str_pdf, columns)


    # Вот сюда добавить дополнительные условия
    append_tech_regulations(str_pdf, dict_result)
    append_OGRN_INN(str_pdf, dict_result)
    append_code_tn(str_pdf, dict_result)
    logger.info(str_pdf)
    append_address_applicant(str_pdf, dict_result)
    append_address_manufacturer(str_pdf, dict_result)
    append_name_of_applicant_and_manufacturer(str_pdf, dict_result)
    append_test_carried(str_pdf, dict_result)
    append_name_of_product(str_pdf, dict_result)
    logger.info(dict_result)
    return dict_result


if __name__ == '__main__':
    convert_pdf_to_dict()
