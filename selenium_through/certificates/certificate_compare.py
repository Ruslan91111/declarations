import logging
import pandas as pd
from selenium.webdriver.common.by import By

from selenium_through.certificates.ammendments_certificate import amend_web_data
from selenium_through.compare_xlsx_and_web import read_viewed_numbers_of_documents, \
    scrapping_web_data_one_document, read_columns_from_xlsx, write_viewed_numbers_to_file, \
    write_to_excel_result_of_comparison, compare_xlsx_and_web_datas
from selenium_through.converters_to_xlsx_data import (convert_date_format,
                                                      remove_decimal_from_xlsx,
                                                      amend_phone_number,
                                                      amend_protocols,
                                                      amend_date_protocols)
from selenium_through.data_scrapper import DataScrapper
from selenium_through.launch_code import URL_CERTIFICATES, XLSX_TEMPLATE_CERTIFICATES

from selenium.webdriver.support import expected_conditions as EC


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('./certificate_compare.txt')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


DIR_WITH_XLSX_COMPARISON = (r"C:\Users\RIMinullin\PycharmProjects"
                            r"\someProject\selenium_through\files_of_comparison")

CERTIFICATE_NUMBER = 'ЕАЭС RU С-RU.АБ80.В.00365/23'

PATH_TO_VIEWED_NUMBERS_CERTIFICATES = (r'C:\Users\RIMinullin\PycharmProjects'
                                       r'\someProject\selenium_through\certificates\viewed.txt')

# scrapping_web_data_one_document('ЕАЭС RU С-RU.АБ80.В.00365/23', URL_CERTIFICATES, '.', XLSX_TEMPLATE_CERTIFICATES)


def give_columns_for_scrapping_certificate(columns: list) -> set:
    """Предоставить названия столбцов для скраппинга."""
    columns = list(columns)
    columns.extend(['Фамилия руководителя', 'Имя руководителя',
                    'Отчество руководителя', 'Адрес места нахождения ',
                    'Адрес места осуществления деятельности', 'Адрес производства продукции',
                    'Общее наименование продукции', 'Наименование испытательной лаборатории',
                    'Бланк сертификата'
                    'Номер записи в РАЛ испытательной лаборатории',
                    'Номер документа'])
    columns = set(columns)
    return columns


class CertificateScrapper(DataScrapper):

    def get_needed_document_in_list(self, document_number):
        """Выбрать нужный документ из списка после ввода номера сертификата."""
        needed_document_element = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*/div[1]/div/div/div/table/tbody/tr[2]/td[3]"
                       "/a/fgis-h-table-limited-text-cell/div[1]")))

        needed_document_text = needed_document_element.text.strip()

        # Проверка, что выбрана нужная декларация.
        if needed_document_text != document_number:
            logger.info(f"Неправильный выбор декларации в списке справа."
                        f"вместо {document_number},\n"
                        f"выбран {needed_document_text}.")
        else:
            logger.info(f"Выбран документ {document_number}")

        needed_document_element.click()

    def get_inner_elements(self, chapter) -> dict:
        """Собрать внутренние элементы на веб-странице. Для которых
        недостаточно метода get_data_on_document_by_columns"""
        inner_elements = {}
        self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'card-edit-row__content')))
        keys = self.browser.find_elements(By.CLASS_NAME, 'card-edit-row__header')
        values = self.browser.find_elements(By.CLASS_NAME, 'card-edit-row__content')
        for key, value in zip(keys, values):
            inner_elements[key.text + ' ' + chapter] = value.text
        return inner_elements

    def get_data_on_document_by_columns(self, needed_columns) -> dict:
        """Собрать с WEB страницы данные в словарь по определенным в шаблоне
         колонкам."""
        data = {}

        # Определяем номер последней главы - количество итераций для сбора данных.
        elements = self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, '//fgis-links-list/div/ul/li')))
        number_of_last_chapter = len(elements)

        # Перебираем и кликаем по подразделам на странице.
        for i in range(2, number_of_last_chapter + 1):
            try:
                needed_chapter = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, self.chapters + f'[{i}]/a')))
                needed_chapter.click()
                # Имя подзаголовка, берем из ссылки перед нажатием.
                chapter = needed_chapter.get_attribute('href')
                chapter = chapter[chapter.rfind('/') + 1:]
                logger.info(f"Проверка раздела {chapter}.")

            except Exception as e:
                logger.error(f"Во время исследования раздела {chapter} произошла ошибка: %s", str(e))
                break

            # "info-row__header" - ключи для словаря; "info-row__text" - значения.
            headers = self.browser.find_elements(By.CLASS_NAME, "info-row__header")
            texts = self.browser.find_elements(By.CLASS_NAME, "info-row__text")

            # Преобразуем данные в словарь.
            for header, text in zip(headers, texts):
                key = header.text.strip()
                # Ключи, которые могут встречаться несколько раз.
                duplicates = {'Полное наименование',
                              'Полное наименование юридического лица',
                              'Номер документа'}

                # Берем только те ключи и значения, который соответствуют колонкам, переданным в метод.
                if key in needed_columns:
                    value = text.text.strip()
                    # Если ключ уже есть в словаре, то добавляем к ключу строку - название подраздела.
                    if key in data or key in duplicates:
                        data[key + ' ' + chapter] = value
                        continue
                    data[key] = value

            # Собрать внутренние элементы в подразделах.
            if chapter in {'applicant', 'manufacturer'}:
                inner_data = self.get_inner_elements(chapter)
                data.update(inner_data)

            # Если подраздел 'Исследования, испытания, измерения', то отдельно собираем номера
            # и даты протоколов. Преобразовываем их в строки, как они хранятся в xlsx файле
            elif chapter == 'testingLabs':
                protocols = self.get_protocols()
                data['Номер протокола'] = ", ".join(protocols['numbers'])
                data['Дата протокола'] = ", ".join(protocols['dates'])
            pass

        logger.info("Сбор данных со страницы окончен.\n")
        return data


def open_xlsx_and_launch_comparison_certificates(url: str, path_to_excel_with_numbers: str,
                                    dir_for_save_files: str):
    """Открыть xlsx файл, прочитать его, и запустить сравнения данных
    из xlsx файла и данных web. Функция будет читать значения
    в колонке номера деклараций, создавать экземпляр класса DataScrapper, через него
    сохранять данные с web, и запускать их сравнение."""

    df = pd.read_excel(path_to_excel_with_numbers)

    # Ранее просмотренные номера документов до текущего вызова функции.
    dict_of_viewed_numbers = read_viewed_numbers_of_documents(PATH_TO_VIEWED_NUMBERS_CERTIFICATES)

    # Просмотренные номера документов в текущем вызове функции.
    list_of_viewed_that_will_be_written = []

    # Класс, собирающий данные по документам из web
    scrapper = CertificateScrapper(URL_CERTIFICATES)
    scrapper.open_page()

    # перебираем номера документов в колонке номеров деклараций
    try:
        for index, row in df.iterrows():
            document_number = row.iloc[1]
            # Если не передан номер или он в просмотренных, то пропустить.
            if str(document_number) == 'nan' or document_number in dict_of_viewed_numbers:
                continue
            else:
                # Иначе открываем документ в вебе и собираем данные
                scrapper.input_document_number(CERTIFICATE_NUMBER)
                scrapper.get_needed_document_in_list(CERTIFICATE_NUMBER)
                columns = give_columns_for_scrapping_certificate(read_columns_from_xlsx(
                    XLSX_TEMPLATE_CERTIFICATES))
                web_data = scrapper.get_data_on_document_by_columns(columns)
                web_data = amend_web_data(web_data)

                # Данные по декларации из xlsx файла.
                xlsx_data = row

                # Запускаем сравнение, передаем строку из xlsx файла и данные из web.
                logger.info(f"Сравнение данных по сертификату {document_number}")
                results_of_comparison = compare_xlsx_and_web_datas(path_to_excel_with_numbers,
                                                                   xlsx_data, web_data)

                # Записать результат в excel файл.
                doc_num = (document_number.replace('/', '_'))
                path_to_store_new_files = dir_for_save_files + '/' + doc_num + ".xlsx"
                write_to_excel_result_of_comparison(results_of_comparison,
                                                    path_to_store_new_files.replace('\n', '\\'))
                logger.info(f"Результаты сравнения данных по декларации "
                            f"{document_number} записаны в файл.")
                list_of_viewed_that_will_be_written.append(document_number)
                scrapper.return_to_input_number()

    except Exception as e:
        logger.error(f"При сравнении данных произошла ошибка: %s", str(e))

    finally:
        # Записать просмотренные номера деклараций в файл.
        write_viewed_numbers_to_file(PATH_TO_VIEWED_NUMBERS_CERTIFICATES, list_of_viewed_that_will_be_written)
        logger.info(f"За сеанс проверены номера деклараций: {list_of_viewed_that_will_be_written}")

    scrapper.close_browser()


open_xlsx_and_launch_comparison_certificates(URL_CERTIFICATES, XLSX_TEMPLATE_CERTIFICATES, DIR_WITH_XLSX_COMPARISON)
