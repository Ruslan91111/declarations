"""
Модуль работы кода с интернет-ресурсами, а именно, сайтами проверки данных: ФСА, СГР, ГОСТ.
"""
import time
import re

import pandas as pd
from logger_config import logger
from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains

from monitoring.config import PROXY
from monitoring.document_dataclass import Document
from monitoring.functions_for_work_with_files_and_dirs import (
    write_last_viewed_number_to_file, read_last_viewed_number_from_file, return_or_create_new_df,
    return_or_create_xlsx_file, return_or_create_dir)
from monitoring.constants import (PATH_TO_DRIVER, Files, COLUMNS_FOR_RESULT_DF,
                                  DIR_CURRENT_MONTHLY_MONITORING, Urls)
from monitoring.scrappers import FSADeclarationScrapper, FSACertificateScrapper, SgrScrapper


def make_browser(number_of_iteration: int):
    """ Создать экземпляр браузера со всеми необходимыми параметрами. """

    service = Service(PATH_TO_DRIVER)
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    if number_of_iteration % 2 == 0:  # Подключать прокси на четных итерациях.
        options.add_argument(f'--proxy-server={PROXY}')
    options.add_argument('--headless')
    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(f'--user-agent={user_agent}')

    browser = webdriver.Chrome(service=service, options=options)
    return browser


def make_wait(browser, time_of_expectation):
    """ Создать экземпляр объекта wait. """
    wait = WebDriverWait(browser, time_of_expectation)
    return wait


def make_and_return_ogrn_and_addresses(result_file: str) -> dict:
    """Собрать и вернуть из файла уже проверенных документов
    словарь из ключей: ОГРН и значений: адресов юридических лиц."""
    try:
        df = pd.read_excel(result_file)

        # Сформировать
        if len(df) != 0:
            df = df.dropna(subset=['ОГРН заявителя', 'Адрес заявителя',
                                   'ОГРН изготовителя', 'Адрес изготовителя'])
    except FileNotFoundError:
        return {}
    ogrn_and_addresses = {}
    for _, row in df.iterrows():
        ogrn_and_addresses[row['ОГРН заявителя']] = row['Адрес заявителя']
        ogrn_and_addresses[row['ОГРН изготовителя']] = row['Адрес изготовителя']
    if 'Нет ОГРН' in ogrn_and_addresses:
        del ogrn_and_addresses['Нет ОГРН']

    return ogrn_and_addresses


def make_copy_of_file_in_process(dir_month, dir_type_of_stage, row_name, new_df):
    """ Сделать копию файла"""
    return_or_create_dir(r'./%s/%s' % (dir_month, dir_type_of_stage))
    copy_xlsx_file = r'./%s/%s/copy_lane_%s.xlsx' % (dir_month, dir_type_of_stage, row_name)
    new_df.to_excel(copy_xlsx_file, index=False)
    logger.info(f"Создана копия файла. Путь к файлу {copy_xlsx_file}")


def check_if_everything_is_checked_in_web(gold_file: str, result_file: str,
                                          file_for_last_number: str) -> bool | None:
    """ Проверка, проверены ли все номера в ГОЛД. """
    try:
        gold_df = pd.read_excel(gold_file)
        result_df = pd.read_excel(result_file)
        last_checked_in_web_number = read_last_viewed_number_from_file(file_for_last_number)
        if len(result_df) != 0 and gold_df.iloc[-1].name == last_checked_in_web_number:
            logger.info("Все номера из матрицы сверены в программе GOLD")
            return True
        return False
    except (KeyError, FileNotFoundError):
        return None


class BrowserWorker:
    """ Задача - работа с браузером."""
    def __init__(self, browser, wait):
        self.browser = browser
        self.wait = wait

    def switch_to_tab(self, tab):
        """ Переключиться на передаваемую вкладку. """
        self.browser.switch_to.window(tab)

    def make_new_tab(self, url: str):
        """ Открыть новую вкладку"""
        self.browser.switch_to.new_window('tab')
        self.browser.get(url)
        return self.browser.current_window_handle

    def wait_until_element_to_be_clickable(self, xpath):
        """ Найти и вернуть элемент на странице """
        searched_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        return searched_element

    def wait_until_element_to_be_located(self, xpath):
        """ Найти и вернуть элемент на странице """
        searched_element = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        return searched_element

    def wait_until_all_elements_located_by_xpath(self, xpath):
        """ Найти и вернуть элемент на странице """
        searched_element = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        return searched_element

    def wait_until_all_elements_located_by_class(self, class_name):
        """ Найти и вернуть элемент на странице """
        searched_elements = self.wait.until(EC.presence_of_all_elements_located(
            (By.CLASS_NAME, class_name)))
        return searched_elements

    def find_an_element_by_class(self, class_name):
        """ Найти элемент по классу. """
        element = self.browser.find_element(By.CLASS_NAME, class_name)
        return element

    def find_the_elements_by_class(self, class_name):
        """ Найти все элементы по классу. """
        elements = self.browser.find_elements(By.CLASS_NAME, class_name)
        return elements

    def find_elements_by_xpath(self, xpath):
        """ Найти все элементы по xpath. """
        element = self.browser.find_elements(By.XPATH, xpath)
        return element

    def input_in_field(self, xpath_input_field: str, value: str):
        """ Ввести в поле """
        input_field = self.wait_until_element_to_be_clickable(xpath_input_field)
        input_field.clear()
        input_field.send_keys(value)

    def wait_and_click_element(self, xpath: str):
        """ Дождаться и кликнуть по элементу. """
        element = self.wait_until_element_to_be_clickable(xpath)
        element.click()
        return element

    def wait_and_press_element_through_chain(self, xpath: str):
        """ Кликнуть по элементу через цепочку действий. """
        element = self.wait_until_element_to_be_clickable(xpath)
        ActionChains(self.browser).move_to_element(element).click().perform()
        return element

    def input_in_field_and_press_search_button(self, xpath_input_field: str,
                                               value: str, xpath_search_button: str):
        """ Ввести в поле и кликнуть по кнопке поиска. """
        self.input_in_field(xpath_input_field, value)
        self.wait_and_click_element(xpath_search_button)

    def get_text_from_element_by_xpath(self, xpath: str):
        """ Получить текст из элемента, искомого по xpath."""
        element = self.wait_until_element_to_be_located(xpath)
        text_from_element = element.text.strip()
        return text_from_element

    def get_text_from_element_by_class(self, class_name: str):
        """ Получить текст из элемента, искомого по классу."""
        element = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, class_name)))
        text_from_element = element.text.strip()
        return text_from_element

    def refresh_browser(self):
        """ Обновить браузер. """
        self.browser.refresh()

    def browser_quit(self):
        """ Закрыть браузер."""
        self.browser.quit()


class RequiredTabsWorker(BrowserWorker):
    """Задача - открытие нужных для работы мониторинга вкладок."""
    def __init__(self, browser, wait):
        super().__init__(browser, wait)
        self.tabs = self.make_all_required_tabs()

    def make_all_required_tabs(self) -> dict:
        """Создать все 5 необходимых вкладок в браузере."""
        tabs = {'declaration': self.make_new_tab(Urls.FSA_DECLARATION.value),
                'certificate': self.make_new_tab(Urls.FSA_CERTIFICATE.value),
                'nsi': self.make_new_tab(Urls.NSI.value),
                'rusprofile': self.make_new_tab(Urls.RUSPROFILE.value),
                'gost': self.make_new_tab(Urls.GOST.value),
                'egrul': self.make_new_tab(Urls.EGRUL.value)}

        return tabs


def determine_type_of_doc(number) -> type | None:
    """ Определить тип документа. """
    patterns = {
        r'(ЕАЭС N RU Д-[\w\.]+)': FSADeclarationScrapper,
        r'(РОСС RU Д-[\w\.]+)': FSADeclarationScrapper,
        r'(ТС N RU Д-[\w\.]+)': FSADeclarationScrapper,
        r'(ЕАЭС RU С-[\w\.]+)': FSACertificateScrapper,
        r'(РОСС RU С-[\w\.]+)': FSACertificateScrapper,
        r'\w{2}\.\d{2}\.(\d{2}|\w{2})\.\d{2}\.\d{2,3}\.\w\.\d{6}\.\d{2}\.\d{2}': SgrScrapper}
    for pattern, scrapper_class in patterns.items():
        if re.match(pattern, number):
            return scrapper_class
    return None


class WebMonitoringWorker:
    """ Класс проверки - мониторинга документов. """
    def __init__(self, gold_file, result_file, file_for_last_number, number_of_iteration,
                 error, time_error, browser_worker=RequiredTabsWorker):
        # Файлы и DataFrame
        self.result_file = result_file
        self.gold_df = pd.read_excel(gold_file)
        self.already_checked_df = pd.read_excel(return_or_create_xlsx_file(result_file))
        self.result_df = return_or_create_new_df(result_file, columns=[COLUMNS_FOR_RESULT_DF])
        # Данные необходимые для мониторинга.
        self.ogrn_and_addresses = make_and_return_ogrn_and_addresses(self.result_file)
        self.last_checked_in_web_number = read_last_viewed_number_from_file(file_for_last_number)
        self.number_of_iteration = number_of_iteration
        self.request_time = 0
        self.error = error
        self.error_time = time_error
        # Используемые объекты browser и wait
        browser = make_browser(self.number_of_iteration)
        wait = make_wait(browser, 30)
        self.browser_worker = browser_worker(browser, wait)

    def make_copy_of_web_file(self, row):
        """ Сделать копию итогового файла"""
        if row.name % 500 == 0 and row.name != 0:
            make_copy_of_file_in_process(DIR_CURRENT_MONTHLY_MONITORING,
                                         'copies_of_web', row.name, self.result_df)

    def check_request_time(self, scrapper_by_type_of_doc, elapsed_time_from_last_request):
        """ Проверить сколько времени прошло с момента последнего обращения к сайту ФСА,
        если недостаточно, то выполнить задержку. """
        if (scrapper_by_type_of_doc in {FSADeclarationScrapper, FSACertificateScrapper} and
                0 < elapsed_time_from_last_request < 60):
            time.sleep(60 - elapsed_time_from_last_request)

    def write_df_and_last_checked_number_in_files(self):
        """ Записать dataframe и номер последней просмотренной строки в файлы. """
        self.result_df.to_excel(self.result_file, index=False)
        write_last_viewed_number_to_file(Files.LAST_VIEWED_IN_WEB_NUMBER.value,
                                         self.last_checked_in_web_number)

    def collect_data_for_all_docs(self) -> None:
        """ Через цикл перебираем строки в ГОЛД файле и собираем по ним данные. """
        for _, row in self.gold_df.iloc[self.last_checked_in_web_number:].iterrows():
            self.make_copy_of_web_file(row)
            try:
                document = Document()
                document.convert_and_save_attrs_from_gold(dict(row))

                # По паттернам определяем тип документа и создаем объект определенного scrapper
                type_of_scrapper = determine_type_of_doc(document.number)
                logger.info(document.number)
                if not type_of_scrapper:  # Для не подпадающего под паттерны.
                    self.result_df = self.result_df._append(row, ignore_index=True)
                    continue

                # Отслеживаем время с последнего запроса к сайту ФСА.
                elapsed_time_from_last_request = time.time() - self.request_time
                self.check_request_time(type_of_scrapper, elapsed_time_from_last_request)

                # Инициализировать scrapper.
                scrapper = type_of_scrapper(self.browser_worker, document, self.ogrn_and_addresses)
                scrapper.process_get_data_on_document()  # Сбор данных по документу.
                self.ogrn_and_addresses = scrapper.ogrn_and_addresses

            except Exception as error:
                self.handle_error_in_collect_data(error=error, timeout=15)
                break

            # Атрибут request_time только у сборщиков данных сайта FSA.
            if hasattr(scrapper, 'request_time'):
                self.request_time = scrapper.request_time

            self.result_df = self.result_df._append(
                scrapper.document.convert_document_to_pd_series(), ignore_index=True)
            self.last_checked_in_web_number = row.name

    def handle_error_in_collect_data(self, error, timeout: int) -> None:
        """ Набор действий при возникновении исключения при работе метода
        self.collect_data_all_docs. Также проверяется, не заблокированы ли оба ip
        адреса на сайте FSA. Если заблокированы, то выполнить задержку."""
        if (str(error) == str(self.error) == 'Ошибка 403 на сервере' and
                (time.time() - float(self.error_time)) < (60 * 5)):
            logger.info('Ошибка сервера 403 для обоих ip адресов.')
            time.sleep(60 * timeout)
        self.error = error
        self.error_time = time.time()

        if hasattr(error, 'msg'):
            logger.error(error.msg)
        else:
            logger.error(error)

        self.write_df_and_last_checked_number_in_files()
        self.browser_worker.browser_quit()


def launch_checking_in_web(gold_file, result_file, count_of_iterations,
                           file_for_last_number, browser_worker=RequiredTabsWorker):
    """ Запуск кода из модуля в цикле."""

    logger.info("Старт проверки данных на интернет ресурсах: "
                "ФСА, СГР, RUSPROFILE, ЕГРЮЛ, ГОСТ.")
    last_error = None
    time_of_last_error = 0

    for number_of_iteration in range(count_of_iterations):

        # Проверка все ли проверено в вебе.
        everything_is_checked = check_if_everything_is_checked_in_web(
            gold_file, result_file, Files.LAST_VIEWED_IN_WEB_NUMBER.value)
        if everything_is_checked:
            logger.info("Все коды продуктов проверены на интернет ресурсах.")
            break
        logger.info("Продолжается проверка продуктов на сайтах.")
        monitoring_worker = WebMonitoringWorker(gold_file, result_file, file_for_last_number,
                                                number_of_iteration, last_error,
                                                time_of_last_error, browser_worker)

        monitoring_worker.collect_data_for_all_docs()

        last_error = monitoring_worker.error
        time_of_last_error = monitoring_worker.error_time
