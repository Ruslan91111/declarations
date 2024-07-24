"""Исключения"""


class ScreenshotNotFoundException(Exception):
    """Не найден скриншот - ошибка, которая делает невозможным
    дальнейшее выполнение программы."""
    def __init__(self, screenshot):
        super().__init__()
        screenshot_name = screenshot[screenshot.rfind('\\'):]
        self.msg = f'Скриншот <{screenshot_name}> не найден в течении заданного периода времени.'


class StopIterationInGoldException(Exception):
    """Прерывание итерации в ГОЛД."""
    def __init__(self):
        super().__init__()
        self.msg = 'Прервана выполнение итерации проверки данных в ГОЛД'


class NotLoadedForNewDocException(Exception):
    """Сайт ФСА заблокировал по IP и не прогружает документы для нового номера."""
    def __init__(self, number):
        super().__init__()
        self.msg = f'На сайте ФСА не загружены документы для номера - {number}'


class FileNotPassedException(Exception):
    """ Название файла на рабочем столе не передано. """
    def __init__(self):
        super().__init__()
        self.msg = 'Название файла для проверки не передано. '


class FileNotExistingException(Exception):
    """Указанный файл не существует."""
    def __init__(self):
        super().__init__()
        self.msg = 'Указанный файл не существует.'


class Server403Exception(Exception):
    def __init__(self, message):
        super().__init__()
        self.msg = 'Ошибка 403 на сервере'

    def __str__(self):
        return self.msg
