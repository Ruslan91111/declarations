"""
Модуль с классами и функциями, необходимыми для создания браузера для парсинга данных.

Функции:
    - make_browser:
        Создать экземпляр браузера со всеми необходимыми параметрами.

    - make_wait:
        Создать экземпляр объекта wait.

    - create_browser:
     Создать конкретный браузер для парсинга данных из интернета с объектом wait.

Классы:
    - BrowserWorker:
        Класс для работы с браузером. Содержит методы для работы с элементами и браузером.

    - MonitoringBrowser(BrowserWorker):
        Класс для работы с браузером при веб-мониторинге, дополнен созданием необходимых вкладок.

"""
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from common.config import PROXY
from common.constants import PATH_TO_DRIVER, Urls


def make_browser(number_of_iteration: int):
    """ Создать экземпляр браузера со всеми необходимыми параметрами. """
    service = Service(PATH_TO_DRIVER)
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    if number_of_iteration % 2 == 0:  # Подключать прокси на четных итерациях.
        options.add_argument(f'--proxy-server={PROXY}')
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


class BrowserWorker:
    """ Класс для работы с браузером."""
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

    def wait_elem_clickable(self, xpath):
        """ Найти и вернуть элемент на странице """
        searched_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        return searched_element

    def wait_elem_located(self, xpath):
        """ Найти и вернуть элемент на странице """
        searched_element = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        return searched_element

    def wait_all_located_by_xpath(self, xpath):
        """ Найти и вернуть элемент на странице """
        searched_element = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        return searched_element

    def wait_all_located_by_class(self, class_name):
        """ Найти и вернуть элемент на странице """
        searched_elements = self.wait.until(EC.presence_of_all_elements_located(
            (By.CLASS_NAME, class_name)))
        return searched_elements

    def find_elem_by_class(self, class_name):
        """ Найти элемент по классу. """
        element = self.browser.find_element(By.CLASS_NAME, class_name)
        return element

    def find_all_elems_by_class(self, class_name):
        """ Найти все элементы по классу. """
        elements = self.browser.find_elements(By.CLASS_NAME, class_name)
        return elements

    def find_all_elems_by_xpath(self, xpath):
        """ Найти все элементы по xpath. """
        element = self.browser.find_elements(By.XPATH, xpath)
        return element

    def input_in_field(self, xpath_input_field: str, value: str):
        """ Ввести в поле """
        input_field = self.wait_elem_clickable(xpath_input_field)
        input_field.clear()
        input_field.send_keys(value)

    def wait_and_click_elem(self, xpath: str):
        """ Дождаться и кликнуть по элементу. """
        element = self.wait_elem_clickable(xpath)
        element.click()
        return element

    def press_elem_through_chain(self, xpath: str):
        """ Кликнуть по элементу через цепочку действий. """
        element = self.wait_elem_clickable(xpath)
        ActionChains(self.browser).move_to_element(element).click().perform()
        return element

    def input_and_press_search(self, xpath_input_field: str,
                               value: str, xpath_search_button: str):
        """ Ввести в поле и кликнуть по кнопке поиска. """
        self.input_in_field(xpath_input_field, value)
        self.wait_and_click_elem(xpath_search_button)

    def get_text_by_xpath(self, xpath: str):
        """ Получить текст из элемента, искомого по xpath."""
        element = self.wait_elem_located(xpath)
        text_from_element = element.text.strip()
        return text_from_element

    def get_text_by_class(self, class_name: str):
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


class MonitoringBrowser(BrowserWorker):
    """ Класс для работы с браузером при веб-мониторинге."""

    def __init__(self, browser, wait):
        super().__init__(browser, wait)
        self.tabs = self.make_all_required_tabs()

    def make_all_required_tabs(self) -> dict:
        """Создать все 6 необходимых вкладок в браузере."""

        tabs = {'declaration': self.make_new_tab(Urls.FSA_DECLARATION.value),
                'certificate': self.make_new_tab(Urls.FSA_CERTIFICATE.value),
                'nsi': self.make_new_tab(Urls.NSI.value),
                'rusprofile': self.make_new_tab(Urls.RUSPROFILE.value),
                'gost': self.make_new_tab(Urls.GOST.value),
                'egrul': self.make_new_tab(Urls.EGRUL.value)}

        return tabs


def create_browser_with_wait(current_iteration, browser_worker, timeout: int = 30):
    """ Создать браузер для парсинга данных из интернета с объектом wait. """
    browser = make_browser(current_iteration)
    wait = make_wait(browser, timeout)
    return browser_worker(browser, wait)
