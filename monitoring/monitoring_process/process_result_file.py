""" Модуль с кодом для подготовки итоговых файлов, а также запуска проверки
на соответствие международных деклараций. """
import os
import re
from enum import Enum

import pandas as pd

from common.constants import PATH_FOR_RESULTS_OF_MONITORING, Files, MsgForUser
from common.logger_config import logger

COLS_FOR_MULTIINDEX = ['Порядковый номер АМ', 'Код товара', 'Наименование товара', 'ДОС']

# Паттерны валидных документов
VALID_NUMBS = [
    r'(ЕАЭС N RU Д-[\w\.]+)',
    r'(РОСС RU Д-[\w\.]+)',
    r'(ТС N RU Д-[\w\.]+)',
    r'(ЕАЭС RU С-[\w\.]+)',
    r'(РОСС RU С-[\w\.]+)',
    r'\w{2}\.\d{2}\.(\d{2}|\w{2})\.\d{2}\.\d{2,3}\.\w\.\d{6}\.\d{2}\.\d{2}']


class ResultFileNames(Enum):
    """ Имена для файлов после обработки итогового файла. """
    FULL: str = (PATH_FOR_RESULTS_OF_MONITORING /
                 r'все строки БЕЗ международных деклараций.xlsx')
    WRONG_STATUSES: str = (PATH_FOR_RESULTS_OF_MONITORING /
                           r'строки с неверным статусом БЕЗ международных деклараций.xlsx')
    FULL_INTERN: str = (PATH_FOR_RESULTS_OF_MONITORING /
                        r'все строки с ПРОВЕРЕННЫМИ международными декларациями.xlsx')
    WRONG_STATUSES_INTERN: str = (PATH_FOR_RESULTS_OF_MONITORING /
                                  r'строки с неверным статусом с ПРОВЕРЕННЫМИ '
                                  r'международными декларациями.xlsx')


def remove_not_in_gold(df: pd.DataFrame) -> pd.DataFrame:
    """Удалить строки, в которых значение в колонке 'ДОС' равно 'Нет данных в GOLD' """
    return df[df['ДОС'] != 'Нет данных в GOLD']


def matches_valid_doc_numb(text, patterns):
    """ Функция, которая проверяет соответствие строки
    одному из шаблонов деклараций. """
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    return False


def collect_df_wrong_statuses(df: pd.DataFrame) -> pd.DataFrame:
    """ Создать df только с неверными статусами. """

    # Фильтруем строки с неверными статусами
    wrong_statuses_df = df[~df['Статус на сайте'].isin(['подписан и действует', 'Действует', 'действует'])]

    # Далее отбираем строки, где 'ДОС' соответствует определенному критерию
    valid_docs_df = wrong_statuses_df[wrong_statuses_df['ДОС'].apply(lambda x: matches_valid_doc_numb(x, VALID_NUMBS))]

    # Создаем DataFrame с 'Нет данных в GOLD' и убираем статус
    no_data_df = df[df['ДОС'] == 'Нет данных в GOLD'].copy()  # Копируем для изменения
    no_data_df['Статус на сайте'] = ''  # Очищаем поля 'Статус на сайте'

    # Объединяем два DataFrame
    final_df = pd.concat([valid_docs_df, no_data_df], ignore_index=True)
    final_df = final_df.sort_values(by='Порядковый номер АМ')

    return final_df


def make_multiindex(df: pd.DataFrame, cols: list):
    """ Создать df с мультииндексом. """
    df.set_index(cols, inplace=True)


def union_result_and_intern(result_xlsx: str, intern_xlsx: str) -> None:
    """ Добавить в итоги международные декларации. """
    result_df = pd.read_excel(result_xlsx)
    intern_df = pd.read_excel(intern_xlsx, index_col='Unnamed: 0')

    # Добавить международные декларации и упорядочить по номерам в матрице.
    result_df.update(intern_df)
    result_df.sort_values(by='Порядковый номер АМ')

    # Разбить на файлы: со всеми строками и со строками с неверным статусом.
    split_result_file(result_df, ResultFileNames.FULL_INTERN.value,
                      ResultFileNames.WRONG_STATUSES_INTERN.value)

    report = MsgForUser.UNION_COMPLETE.value.format(
        ResultFileNames.FULL_INTERN.value, ResultFileNames.WRONG_STATUSES_INTERN.value)

    logger.info(report)
    print(report)


def create_intern_xlsx(df, output_xlsx: str):
    """ Создать файл с международными декларациями """
    # Паттерн для фильтрации
    pattern = r'ЕАЭС (№ ?)?(KZ|BY|KG|AM)[\w\/\.\\s-]+'
    # Фильтрация DataFrame
    filtered_df = df[df['ДОС'].str.contains(pattern)]
    # Запись отфильтрованного DataFrame
    filtered_df.to_excel(output_xlsx, index=True)
    logger.info(f'Международные декларации записаны в отдельный файл {output_xlsx}')


def split_result_file(df, name_for_full, name_with_wrong_status):
    """ Получить на вход итоговый файл, записать файл с международными декларациями,
     затем установить мультииндекс и записать, затем выделить строки с неверным статусом
     и записать в файл"""
    # Проверяем есть ли файл с международными декларациями, если нет, то создаем.
    if not os.path.isfile(Files.INTERN_DOCS.value):
        create_intern_xlsx(df, Files.INTERN_DOCS.value)

    # Выбираем декларации с неверным статусом и записываем его в файл.
    wrong_status_df = collect_df_wrong_statuses(df)
    wrong_status_df.to_excel(name_with_wrong_status, index=False)
    print(MsgForUser.FILE_WRITTEN.value.format(name_with_wrong_status))

    # Удаляем индекс, устанавливаем мультииндекс и записываем в файл со всеми строками
    df.reset_index()
    make_multiindex(df, COLS_FOR_MULTIINDEX)
    df.to_excel(name_for_full)
    print(MsgForUser.FILE_WRITTEN.value.format(name_for_full))


def finish_monitoring():
    """ Сохраняет итоговый файл с результатами основного мониторинга,
    а также запускает проверку международных деклараций. """

    # Проверяем есть ли ИТОГОВЫЙ файл с международными декларациями, если нет, то создаем.
    if not os.path.isfile(ResultFileNames.FULL_INTERN.value):
        from web.intern_docs.check_intern_docs import launch_collect_intern_docs
        launch_collect_intern_docs(150)

    else:
        logger.info(MsgForUser.PATH_FOR_FIN_FILE.value.format(
            ResultFileNames.FULL_INTERN.value))
        print(MsgForUser.PATH_FOR_FIN_FILE.value.format(
            ResultFileNames.FULL_INTERN.value))


if __name__ == '__main__':

    finish_monitoring()