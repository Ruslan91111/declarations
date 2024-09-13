@echo off
cd C:\Users\impersonal\Desktop\declarations
chcp 65001 > nul  REM Переключаем консоль на UTF-8

rem Активируем виртуальное окружение
call .\venv\Scripts\activate

rem Запускаем первый скрипт в параллельном окне, добавляем pause после завершения
start "working.py" cmd /k "python dont_sleep.py & echo working.py завершен. & pause"

rem Запускаем второй скрипт в параллельном окне, добавляем pause после завершения
start "Monitoring" cmd /k "python .\monitoring\launch_monitoring_package.py & echo launch_monitoring_package.py завершен. & pause"

echo Сценарии запущены параллельно.
