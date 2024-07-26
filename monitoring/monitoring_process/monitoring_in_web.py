"""
Модуль организации проверки данных по декларациям на интернет сайтах.
В ходе организации процесса, читает исходный файл с документами из xlsx файла,
перебирает их через цикл, проверяет не были ли документ проверен ранее,
если нет, то выбирает подходящий класс parser, создает его, передает имеющиеся данные,
класс parser осуществляет сбор необходимых данных, класс WebMonitoringWorker, в свою
очередь сохраняет данные собранные parser в DataFrame.


  class WebMonitoringWorker - класс проверки мониторинга документов.

    def collect_data_for_all_docs - основной метод проверки документов через цикл


  def launch_checking_in_web - функция запуска кода из модуля в цикле и организация мониторинга,
      в процессе создает объект класса WebMonitoringWorker и запускает
      его метод collect_data_for_all_docs

"""
import time
import pandas as pd
from common.logger_config import logger

from common.document_dataclass import Document
from common.work_with_files_and_dirs import (write_numb_to_file,
                                             create_copy_of_file, prepare_df_for_work)
from common.constants import (Files, DIR_CURRENT_MONTH, COLS_FOR_RESULT_DF)
from .monitoring_helpers import (choose_parser, check_request_time, HelpData)
from web.work_with_browser import create_browser_with_wait


class WebMonitoringWorker:
    """ Класс проверки - мониторинга документов.
    Непосредственно осуществляет мониторинг, читает и файлы,
    через цикл проверяет документы на сайтах, выбирая подходящий парсер
    собирает информацию собранную парсером."""

    def __init__(self, gold_file: str, result_file: str, file_last_number_web: str,
                 current_iteration: int, last_error: str, time_error: float):

        self.result_file = result_file
        self.gold_df = pd.read_excel(gold_file)
        self.result_df = prepare_df_for_work(self.result_file, COLS_FOR_RESULT_DF)
        self.help_data = HelpData(
            self.result_df, self.gold_df, file_last_number_web, current_iteration,
            last_error, time_error)
        self.browser_worker = create_browser_with_wait(
            self.help_data.current_iteration, self.help_data.browser_worker)
        self.document = Document()
        self.row = None
        self.site_parser = None

    def make_copy_of_file(self):
        """ Создать копию итогового файла"""
        if self.row.name % 500 == 0 and self.row.name != 0:
            create_copy_of_file(DIR_CURRENT_MONTH,
                                         'copies_of_web', self.row.name, self.result_df)

    def write_df_and_last_number_in_files(self):
        """ Записать dataframe и номер последней просмотренной строки в файлы. """
        self.result_df.to_excel(self.result_file, index=False)
        write_numb_to_file(Files.LAST_VIEWED_IN_WEB_NUMB.value,
                           self.help_data.last_checked_in_web_number)

    def all_checked(self):
        """ Проверка все ли номера документов уже проверены. """
        if self.help_data.last_row_in_gold == self.help_data.last_checked_in_web_number:
            logger.info("Все коды продуктов проверены на интернет ресурсах.")
            return True
        return False

    def process_previously_checked(self):
        """ Набор действий для документа, номер которого ранее был просмотрен. """
        if self.document.number in self.help_data.watched_docs_numbers:
            df_with_same_doc = self.result_df[
                self.result_df['ДОС'] == self.document.number
            ].reset_index()
            data_from_already_checked = df_with_same_doc.loc[0, 'ДОС':]
            self.document.save_attrs_from_prev_checked(data_from_already_checked)
            self.result_df = self.result_df._append(
                self.document.convert_document_to_pd_series(), ignore_index=True)
            self.help_data.watched_docs_numbers.add(self.document.number)
            self.help_data.last_checked_in_web_number = self.row.name
            return True
        return False

    def process_data_from_parser(self):
        """ Набор действий для документа, который ранее не был проверен. """
        if hasattr(self.site_parser, 'request_time'):
            self.help_data.request_time = self.site_parser.request_time
        self.result_df = self.result_df._append(
            self.site_parser.document.convert_document_to_pd_series(),
            ignore_index=True)
        self.help_data.last_checked_in_web_number = self.row.name
        self.help_data.watched_docs_numbers.add(self.document.number)
        self.help_data.ogrn_and_addresses = self.site_parser.ogrn_and_addresses

    def collect_data_for_all_docs(self) -> None:
        """ Через цикл перебираем строки в gold DataFrame и собираем по ним данные. """
        for _, row in self.gold_df.iloc[self.help_data.last_checked_in_web_number:].iterrows():
            self.row = row
            self.make_copy_of_file()

            # Проверка все ли документы проверены.
            if self.all_checked():
                break

            try:

                # Преобразуем данные в dataclass Document
                self.document = Document()
                self.document.save_attrs_from_gold(dict(self.row))
                # По паттернам определяем тип документа и создаем объект определенного site_parser
                type_of_parser = choose_parser(self.document.number)

                # Проверка не был ли ранее проверен номер документа
                if self.process_previously_checked():
                    continue
                logger.info(self.document.number)

                # Для не подпадающего под паттерны.
                if not type_of_parser:
                    self.result_df = self.result_df._append(row, ignore_index=True)
                    self.help_data.last_checked_in_web_number = self.row.name
                    continue

                # Отслеживаем время с последнего запроса к сайту ФСА.
                elapsed_time_from_last_request = time.time() - self.help_data.request_time
                check_request_time(type_of_parser, elapsed_time_from_last_request)

                # Инициализировать site_parser, собрать данные по документу.
                self.site_parser = type_of_parser(
                    self.browser_worker, self.document, self.help_data.ogrn_and_addresses)
                self.site_parser.process_get_data_on_doc()

            except Exception as error:
                self.handle_error_in_collect_data(error=error, timeout=15)
                break

            # Обработать и сохранить собранные данные.
            self.process_data_from_parser()
        # При удачной работе метода, сохраняет полученный DataFrame и последний номер.
        self.write_df_and_last_number_in_files()

    def handle_error_in_collect_data(self, error, timeout: int) -> None:
        """ Набор действий при возникновении исключения при работе метода
        self.collect_data_all_docs. Также проверяется, не заблокированы ли оба ip
        адреса на сайте FSA. Если заблокированы, то выполнить задержку."""
        if (str(error) == str(self.help_data.error) == 'Ошибка 403 на сервере' and
                (time.time() - float(self.help_data.error_time)) < (60 * 5)):
            logger.info('Ошибка сервера 403 для обоих ip адресов.')
            time.sleep(60 * timeout)
        self.help_data.error = error
        self.help_data.error_time = time.time()

        if hasattr(error, 'msg'):
            logger.error(error.msg)
        else:
            logger.error(error)

        self.write_df_and_last_number_in_files()
        self.browser_worker.browser_quit()


def launch_checking_in_web(gold_file: str, result_file: str, count_of_iterations: int,
                           file_for_last_number: str):
    """ Запуск кода из модуля в цикле."""
    logger.info("Старт проверки данных на интернет ресурсах: ФСА, СГР, RUSPROFILE, ЕГРЮЛ, ГОСТ.")
    last_error = None
    time_of_last_error = 0

    # Цикл, где каждая итерация - это запуск нового браузера.
    for number_of_iteration in range(count_of_iterations):
        logger.info("Запуск проверки документов на сайтах.")

        monitoring_worker = WebMonitoringWorker(
            gold_file, result_file, file_for_last_number,
            number_of_iteration, last_error, time_of_last_error)

        monitoring_worker.collect_data_for_all_docs()

        gold_last_row = monitoring_worker.help_data.last_checked_in_web_number
        web_last_row = monitoring_worker.help_data.last_row_in_gold

        # Проверка, все ли номера проверены в интернете.
        if gold_last_row == web_last_row:
            logger.info("Все коды продуктов проверены на интернет ресурсах.")
            break

        last_error = monitoring_worker.help_data.error
        time_of_last_error = monitoring_worker.help_data.error_time
