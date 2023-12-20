"""
DataScrapper - класс для сбора данных по декларации с веба.
"""
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Конфигурация логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('./logs/data_scrapper.txt')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class DataScrapper:
    """Класс, собирающий данные со страницы.
    Работает с определенной страницей."""

    def __init__(self, url: str) -> None:
        self.options = webdriver.ChromeOptions()
        # self.options.add_argument("--headless")
        # self.options.add_argument("--window-size=1920,1080")
        self.browser = webdriver.Chrome()  # options=self.options
        self.url = url
        self.wait = WebDriverWait(self.browser, 30)
        # XPATH для подразделов декларации.
        self.chapters = '//fgis-links-list/div/ul/li'

    def open_page(self) -> None:
        """Открыть страницу"""
        self.browser.get(self.url)

    def return_to_input_number(self) -> None:
        """После сохранения данных по декларации нажать на возврат
        для ввода следующего номера декларации."""
        back_to_input = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//fgis-rds-view-declaration-toolbar/div/div[1]")))
        back_to_input.click()

    def input_document_number(self, document_number: str):
        """Открыть страницу с полем для ввода номера документа,
        ввести номер декларации, нажать на кнопку 'найти'."""
        input_number_document = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//fgis-text/input")))
        input_number_document.clear()
        input_number_document.send_keys(document_number)
        button_search = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Найти')]")))
        button_search.click()
        logger.info(f"Введен номер документа {document_number}")

    def get_needed_document_in_list(self, document_number: str) -> None:
        """Обновить браузер, дождаться список документов, кликнуть по нужному документу в списке."""
        self.browser.refresh()
        # Первый элемент в списке
        needed_document_element = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*/div[1]/div/div/div/table/tbody/tr[2]/td[3]"
                       "/a/fgis-h-table-limited-text-cell/div[1]")))

        # Строка - номер документа, выбранного для клика
        needed_document_text = needed_document_element.text.strip()
        # Проверка, что выбрана нужная декларация.
        if needed_document_text != document_number:
            logger.info(f"Неправильный выбор декларации в списке справа."
                        f"вместо {document_number},\n"
                        f"выбран {needed_document_text}.")
        else:
            logger.info(f"Выбран документ {document_number}")

        needed_document_element.click()

    def get_protocols(self) -> dict:
        """При нахождении на странице подраздела 'Исследования,
        испытания, измерения' отдельно собрать номера и даты протоколов."""
        protocol_numbers = []
        protocol_dates = []
        protocols = {}

        # Нахождение всех элементов tr в таблице протоколов.
        elements = self.browser.find_elements(By.XPATH, "//tr")

        # Обход каждого элемента tr
        for element in elements:
            # Извлечение текста из элементов td
            tds = element.find_elements(By.TAG_NAME, "td")
            if len(tds) >= 2:
                protocol_number = tds[0].text.strip()
                protocol_date = tds[1].text.strip()
                # Добавление номеров и дат протоколов в списки
                protocol_numbers.append(protocol_number)
                protocol_dates.append(protocol_date)

        protocols['numbers'] = protocol_numbers
        protocols['dates'] = protocol_dates
        logger.info(f"Номера протоколов {protocol_numbers},"
                    f" даты протоколов {protocol_dates}")
        return protocols

    def get_data_on_document_by_columns(self, needed_columns) -> dict:
        """Собрать с WEB страницы данные в словарь по определенным в шаблоне
         колонкам."""
        data = {}

        # Определяем номер последней главы - количество итераций для сбора данных.
        elements = self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, '//fgis-links-list/div/ul/li')))
        number_of_last_chapter = len(elements)

        # Перебираем и кликаем по подразделам на странице.
        for i in range(1, number_of_last_chapter + 1):
            try:
                needed_chapter = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, self.chapters+f'[{i}]/a')))
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

            # Если подраздел 'Исследования, испытания, измерения', то отдельно собираем номера
            # и даты протоколов. Преобразовываем их в строки, как они хранятся в xlsx файле

            if chapter == 'testingLabs':  # Пока для декларации. Для сертификата под другому
                protocols = self.get_protocols()
                data['Номер протокола'] = ", ".join(protocols['numbers'])
                data['Дата протокола'] = ", ".join(protocols['dates'])
            pass

        logger.info("Сбор данных со страницы окончен.\n")
        return data

    def close_browser(self):
        """Закрыть браузер."""
        self.browser.quit()
