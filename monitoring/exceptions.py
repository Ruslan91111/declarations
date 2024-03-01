"""Исключения"""


class ScreenshotNotFoundException(Exception):
    """Не найден скриншот - ошибка, которая делает невозможным
    дальнейшее выполнение программы."""
    def __init__(self, image_path):
        self.image_path = image_path


class StopIterationExceptionInGold(Exception):
    """Прерывание цикла работы в ГОЛД."""
    def __init__(self):
        super().__init__()
        self.msg = 'Прервано выполнение функции add_declaration_number_and_manufacturer.'


class SeleniumNotFoundException(Exception):
    """Не дождались какого-либо элемента в selenium."""
    def __init__(self):
        super().__init__()
        self.msg = 'Превышено ожидание элемента на веб странице. Прерывание итерации.'


class EgrulCaptchaException(Exception):
    """Возникла капча в ЕГРЮЛ."""
    def __init__(self):
        super().__init__()
        self.msg = 'Возникла капча в ЕГРЮЛ.'
