from datetime import datetime

import pandas as pd
import logging

from work_with_pdf import convert_pdf_to_dict, read_columns_from_xlsx, TEMPLATE_XLSX

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('comparison.txt')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)


def convert_date_format(date_str):
    try:
        # Преобразование строки в объект datetime
        date = datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S')
        # Преобразование объекта datetime в нужный формат
        formatted_date = date.strftime('%d.%m.%Y')
        return formatted_date
    except ValueError:
        return date_str



def compare_xlsx_and_dict(xlsx_template: str) -> list:
    """"""
    df = pd.read_excel(xlsx_template)
    dict_from_pdf = convert_pdf_to_dict()
    columns = read_columns_from_xlsx(xlsx_template)[2:]
    wrong_view = 0
    rounds = 0

    for column in columns:
        rounds += 1
        logger.info(f'name of column - %s' % column)

        if str(type(df.iloc[3][column])) == "<class 'datetime.datetime'>":
            logger.info(f'value from EXCEL -- %s ' % convert_date_format(df.iloc[3][column]))

        else:
            logger.info(f'value from EXCEL -- %s ' % df.iloc[3][column])

        try:
            logger.info(f'value from PDF -- %s ' % dict_from_pdf[column])
        except:
            logger.info('Отсутствует')
            wrong_view += 1
            logger.info('*******************')
    logger.info(wrong_view)
    logger.info(rounds)


if __name__ == '__main__':
    compare_xlsx_and_dict(TEMPLATE_XLSX)
