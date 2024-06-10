"""
Модуль работы кода с интернет-ресурсами, а именно, сайтами проверки данных: ФСА, СГР, ГОСТ.
"""
import random
import sys
import time
import re

import pandas as pd
import pyautogui
from fake_useragent import UserAgent

from selenium import webdriver
from selenium.common import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains

from config import PROXY
from exceptions import NotLoadedDocumentsOnFsaForNewNumberException, Server403Exception, ServiceNotAvailableException, \
    StopIterationInGoldException, StopMonitoringException, DocsForNewNumberNotLoadedException
from monitoring.document_dataclass import Document
from monitoring.functions_for_work_with_files_and_dirs import (
    write_last_viewed_number_to_file, read_last_viewed_number_from_file, return_or_create_new_df,
    return_or_create_xlsx_file, return_or_create_dir)
from logger_config import logger
from monitoring.constants import (PATH_TO_DRIVER, Files, COLUMNS_FOR_RESULT_DF,
                                  DIR_CURRENT_MONTHLY_MONITORING, RusProfileXPaths, Urls)
from monitoring.scrappers import FSADeclarationScrapper, FSACertificateScrapper, SgrScrapper


def make_browser(number_of_iteration: int):
    """ Создать экземпляр браузера со всеми необходимыми параметрами. """
    service = Service(PATH_TO_DRIVER)
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    # if number_of_iteration % 2 == 0:  # Подключать прокси на четных итерациях.
    #     options.add_argument(f'--proxy-server={PROXY}')
    # options.add_argument('--headless')
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
    except FileNotFoundError:
        return {}
    ogrn_and_addresses = {}
    for _, row in df.iterrows():
        ogrn_and_addresses[row['ОГРН заявителя']] = row['Адрес заявителя']
        ogrn_and_addresses[row['ОГРН изготовителя']] = row['Адрес изготовителя']
    if 'Нет ОГРН' in ogrn_and_addresses.keys():
        del ogrn_and_addresses['Нет ОГРН']
    return ogrn_and_addresses


def make_copy_of_file_in_process(dir_month, dir_type_of_stage, row_name, new_df, columns):
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
        searched_elements = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, class_name)))
        return searched_elements

    def find_an_element_by_class(self, class_name):
        element = self.browser.find_element(By.CLASS_NAME, class_name)
        return element

    def find_elements_by_class(self, class_name):
        elements = self.browser.find_elements(By.CLASS_NAME, class_name)
        return elements

    # def find_an_element_by_xpath(self, xpath):
    #     element = self.browser.find_elements(By.XPATH, xpath)
    #     return element

    def find_elements_by_xpath(self, xpath):
        element = self.browser.find_elements(By.XPATH, xpath)
        return element

    def input_in_field(self, xpath_input_field: str, value: str):
        input_field = self.wait_until_element_to_be_clickable(xpath_input_field)
        input_field.clear()
        input_field.send_keys(value)

    def wait_and_click_element(self, xpath: str):
        element = self.wait_until_element_to_be_clickable(xpath)
        element.click()
        return element

    def wait_and_press_element_through_chain(self, xpath: str):
        element = self.wait_until_element_to_be_clickable(xpath)
        ActionChains(self.browser).move_to_element(element).click().perform()
        return element

    def input_in_field_and_press_search_button(self, xpath_input_field: str,
                                               value: str, xpath_search_button: str):
        self.input_in_field(xpath_input_field, value)
        self.wait_and_click_element(xpath_search_button)

    def get_text_from_element_by_xpath(self, xpath: str):
        element = self.wait_until_element_to_be_located(xpath)
        text_from_element = element.text.strip()
        return text_from_element

    def get_text_from_element_by_class(self, class_name: str):
        element = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, class_name)))
        text_from_element = element.text.strip()
        return text_from_element

    def refresh_browser(self):
        self.browser.refresh()

    def refresh_browser_by_hotkey(self):
        pyautogui.hotkey('ctrl', 'r')

    def chain_move_and_click(self, element):
        ActionChains(self.browser).move_to_element(element).click().perform()

    def browser_quit(self):
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
                'gost': self.make_new_tab(Urls.GOST.value)}
        return tabs


class WebMonitoringWorker:

    def __init__(self, gold_file, result_file, file_for_last_number, browser_worker=RequiredTabsWorker):

        self.gold_file = gold_file
        self.result_file = result_file

        self.gold_df = pd.read_excel(gold_file)
        self.already_checked_df = pd.read_excel(return_or_create_xlsx_file(result_file))
        self.new_df = return_or_create_new_df(result_file, columns=[COLUMNS_FOR_RESULT_DF])

        self.ogrn_and_addresses = make_and_return_ogrn_and_addresses(self.result_file)
        self.last_checked_in_web_number = read_last_viewed_number_from_file(file_for_last_number)
        self.number_of_iteration = 0
        self.request_time = 0

        browser = make_browser(self.number_of_iteration)
        wait = make_wait(browser, 30)
        self.browser_worker = browser_worker(browser, wait)

    def make_copy_of_web_file(self, row):
        """ Сделать копию итогового файла"""
        if row.name % 500 == 0 and row.name != 0:
            make_copy_of_file_in_process(DIR_CURRENT_MONTHLY_MONITORING, 'copies_of_web', row.name,
                                         self.already_checked_df, self.new_df)

    def check_request_time(self, scrapper_by_type_of_doc, elapsed_time_from_last_request):
        if ((scrapper_by_type_of_doc == FSADeclarationScrapper or
             scrapper_by_type_of_doc == FSACertificateScrapper) and
                0 < elapsed_time_from_last_request < 60):
            time.sleep(60 - elapsed_time_from_last_request)

    def write_df_and_last_checked_number_in_files(self):
        # total_df = pd.concat([self.already_checked_df, self.new_df])
        self.new_df.to_excel(self.result_file, index=False)
        write_last_viewed_number_to_file(Files.LAST_VIEWED_IN_WEB_NUMBER.value, self.last_checked_in_web_number)

    def determine_type_of_doc(self, number) -> type | None:
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


    def collect_data_about_docs_through_for(self) -> None:
        """ Через цикл перебираем строки в ГОЛД файле и собираем по ним данные. """
        for _, row in self.gold_df.iloc[self.last_checked_in_web_number:].iterrows():
            self.make_copy_of_web_file(row)
            document = Document()
            document.convert_and_save_attrs_from_gold(dict(row))

            # По паттернам определяем тип документа и создаем объект определенного scrapper
            scrapper_by_type_of_doc = self.determine_type_of_doc(document.number)
            if not scrapper_by_type_of_doc:  # Для не подпадающего под паттерны.
                self.new_df = self.new_df._append(row, ignore_index=True)
                continue

            # Отслеживаем время с последнего запроса к сайту ФСА.
            elapsed_time_from_last_request = time.time() - self.request_time
            self.check_request_time(scrapper_by_type_of_doc, elapsed_time_from_last_request)

            # Определить какой тип документа и какой сайт нужен.
            scrapper = scrapper_by_type_of_doc(self.browser_worker, document)

            try:
                scrapper.process_get_data_on_document()  # Сбор данных.

            except Exception as error:
                self.write_df_and_last_checked_number_in_files()
                logger.error(error)
                self.browser_worker.browser_quit()
                break


            # Атрибут request_time только у скраперов сайта FSA.
            if hasattr(scrapper, 'request_time'):
                self.request_time = scrapper.request_time

            self.new_df = self.new_df._append(scrapper.document.convert_document_to_pd_series(), ignore_index=True)
            self.last_checked_in_web_number = row.name






def launch_checking_in_web(gold_file, result_file, count_of_iterations,
                           file_for_last_number, browser_worker=RequiredTabsWorker):
    """ Запуск кода из модуля в цикле."""
    logger.info("Старт проверки данных на интернет ресурсах: ФСА, СГР, RUSPROFILE, ГОСТ.")
    error403 = ''

    for _ in range(count_of_iterations):

        # Проверка все ли проверено в вебе.
        everything_is_checked = check_if_everything_is_checked_in_web(
            gold_file, result_file, Files.LAST_VIEWED_IN_WEB_NUMBER.value)
        if everything_is_checked:
            logger.info("Все коды продуктов проверены на интернет ресурсах.")
            break

        logger.info("Продолжается проверка продуктов на сайтах.")
        monitoring_worker = WebMonitoringWorker(gold_file, result_file, file_for_last_number, browser_worker)
        monitoring_worker.collect_data_about_docs_through_for()
