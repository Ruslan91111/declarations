import PyPDF2
import pandas as pd
import logging

PDF_PATH = r'Выписка по ДС № ЕАЭС N RU Д-RU.РА01.В.39739_23 от 2023-11-21.pdf'
TEMPLATE_XLSX = r'Шаблон для внесения информации по декларациям о соответствии.xlsx'
TEXT_FILE = 'text.txt'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('log.txt')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)


def pdf_to_str(path_to_pdf: str) -> str:
    """Read PDF file, convert and return one big str."""
    with open(path_to_pdf, 'rb') as file:
        read_pdf = PyPDF2.PdfReader(file)
        count_of_pages = len(read_pdf.pages)
        all_text = ''
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
    ind_key_start = text.find(substr)
    ind_key_end = text.find(substr) + len(substr)
    key = text[ind_key_start:ind_key_end]
    ind_value_start = ind_key_end + 1
    ind_value_end = text.find('\n', ind_key_end, -1)
    value = text[ind_value_start:ind_value_end]
    return {key: value}


def convert_text_to_dict(text: str, keys: list):
    """Fill the dict couples key and value from text from pdf."""
    dict_from_text = {}
    for item in keys:
        key_value = find_item(text, item)
        dict_from_text.update(key_value)
    return dict_from_text


def main_func():
    """"""
    # Из пдф в строку.
    str_from_pdf = pdf_to_str(PDF_PATH)

    # Запишем в файл.
    write_text_to_file(TEXT_FILE, str_from_pdf)

    # Выберем названия колонок из шаблона xlsx.
    columns = read_columns_from_xlsx(TEMPLATE_XLSX)

    # Преобразуем текст в словарь.
    dict_result = convert_text_to_dict(str_from_pdf, columns)
    logger.info(dict_result)
    print(dict_result)




if __name__ == '__main__':
    main_func()
