import pyautogui
import time


pyautogui.FAILSAFE = False


def dont_let_fall_asleep():
    pyautogui.hotkey('Win', 'd')
    print('Данное окно сверните, но не закрывайте. ')
    while True:
        pyautogui.press('shift')
        time.sleep(60*10)


dont_let_fall_asleep()
