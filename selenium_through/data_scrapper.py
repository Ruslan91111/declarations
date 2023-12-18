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
file_handler = logging.FileHandler('dict_from_web_by_selenium.txt')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# Названия подразделов декларации на web странице.
# chapters = {'common information': '//fgis-links-list/div/ul/li[1]/a',
#             'declaration': '//fgis-links-list/div/ul/li[2]/a',
#             'applicant': '//fgis-links-list/div/ul/li[3]/a',
#             'manufacturer': '//fgis-links-list/div/ul/li[4]/a',
#             'custom info': '//fgis-links-list/div/ul/li[5]/a',
#             'products info': '//fgis-links-list/div/ul/li[6]/a',
#             'tests': '//fgis-links-list/div/ul/li[7]/a',
#             'declaration-schema-docs': '//fgis-links-list/div/ul/li[8]/a'}


class DataScrapper:
    """Класс, собирающий данные со страницы."""

    def __init__(self, url: str) -> None:
        # self.options = webdriver.ChromeOptions()
        # self.options.add_argument('--headless')
        self.browser = webdriver.Chrome()  # options=self.options
        self.url = url
        self.wait = WebDriverWait(self.browser, 30)
        # Подразделы декларации.
        self.chapters = '//fgis-links-list/div/ul/li'


    def open_page(self) -> None:
        """Открыть страницу"""
        self.browser.get(self.url)

    def return_to_input_number(self) -> None:
        """После сохранения данных по декларации нажать на возврат
        для ввода следующего номера декларации."""
        back_to_input = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//fgis-rds-view-declaration-toolbar/div/div[1]")))
        back_to_input.click()

    def input_declaration_number(self, number_declaration):
        """Открыть страницу с полем для ввода деклараций,
        ввести номер декларации, нажать на кнопку 'найти'."""
        # Ввести номер декларации и нажать кнопку 'найти'
        input_number_declaration = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//fgis-text/input"))
        )
        input_number_declaration.clear()
        input_number_declaration.send_keys(number_declaration)
        button_search_declaration = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Найти')]"))
        )
        button_search_declaration.click()

    # Дождаться и кликнуть на первую декларацию в списке справа.
    def get_needed_declaration_in_list(self, number_declaration) -> None:
        """Обновить браузер, дождаться список деклараций, кликнуть по нужной декларации в списке."""
        self.browser.refresh()
        # Первый элемент в списке
        needed_declaration_element = self.wait.until(
            EC.element_to_be_clickable((
                By.XPATH, "//*/div[1]/div/div/div/table/tbody/tr[2]/td[3]"
                          "/a/fgis-h-table-limited-text-cell/div[1]"))
        )
        # Номер декларации, выбранной для клика
        needed_declaration_text = needed_declaration_element.text.strip()
        # Проверка, что выбрана нужная декларация.
        if needed_declaration_text != number_declaration:
            logger.info(f"Неправильный выбор декларации в списке справа."
                        f"вместо {number_declaration},\n"
                        f"выбран {needed_declaration_text}.")
            pass

        needed_declaration_element.click()

    def get_protocols(self) -> dict:
        """При нахождении на странице подраздела 'Исследования,
        испытания, измерения' отдельно собрать номера и даты протоколов."""
        # Списки для хранения номеров протоколов и дат протоколов
        protocol_numbers = []
        protocol_dates = []

        protocols = {}

        # Нахождение всех элементов tr в таблице.
        elements = self.browser.find_elements(By.XPATH, "//tr")

        # Обход каждого элемента tr
        for element in elements:
            # Извлечение текста из элементов td
            tds = element.find_elements(By.TAG_NAME, "td")
            if len(tds) >= 2:
                protocol_number = tds[0].text.strip()
                protocol_date = tds[1].text.strip()
                # Добавление номера протокола в список protocol_numbers
                protocol_numbers.append(protocol_number)
                # Добавление даты протокола в список protocol_dates
                protocol_dates.append(protocol_date)

        protocols['numbers'] = protocol_numbers
        protocols['dates'] = protocol_dates
        return protocols

    def get_data_on_declaration(self, needed_columns):
        """Собрать со страницы данные по декларации в словарь"""

        # Словарь, куда поместим данные со страницы.
        data = {}

        # Перебираем и кликаем по подразделам на странице.
        for i in range(1, 10):
            try:
                needed_chapter = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.chapters+f'[{i}]/a')))
                needed_chapter.click()
                chapter = needed_chapter.get_attribute('href')
                chapter = chapter[chapter.rfind('/') + 1:]

            except Exception as e:
                logger.error("Подразделы закончились. Произошла ошибка: %s", str(e))

            # Находим все элементы с классом "info-row__header" - ключи для словаря
            # и "info-row__text" - значения для ключей.
            headers = self.browser.find_elements(By.CLASS_NAME, "info-row__header")
            texts = self.browser.find_elements(By.CLASS_NAME, "info-row__text")

            # Загоняем данные в словарь.
            for header, text in zip(headers, texts):
                key = header.text.strip()

                dict_of_duplicate = {'Полное наименование': True,
                                     'Полное наименование юридического лица': True,
                                     'Номер документа': True}

                if key in needed_columns:
                    value = text.text.strip()
                    # Если ключ уже есть в словаре, то добавляем к ключу строку - название подраздела.
                    if key in data or key in dict_of_duplicate:
                        data[key + ' ' + chapter] = value
                        continue
                    data[key] = value

            # Если подраздел 'Исследования, испытания, измерения', то отдельно
            # собираем номера и даты протоколов. Преобразовываем их в строки,
            # как они хранятся в xlsx файле
            if chapter == 'testingLabs':
                protocols = self.get_protocols()
                data['Номер протокола'] = ", ".join(protocols['numbers'])
                data['Дата протокола'] = ", ".join(protocols['dates'])

            if chapter == 'testingLabs':
               break
        return data

    def close_browser(self):
        """Закрыть браузер."""
        self.browser.quit()
