## Declaration

**Declaration** – пакет, предназначенный для оптимизации бизнес-процессов предприятия. 
Задача пакета - проверка валидности документов, предоставляемых поставщиками 
к поставляемым товарам. Проверка на актуальность сведений из документов сведениям размещенным на 
общедоступных интернет-ресурсах.

### Краткое описание процесса

Входной файл формата XLSX содержит данные о товарах, выгруженные из БД предприятия. 
Проверка условно подразделяется
на несколько этапов.

1. **Создание предварительного DataFrame**. 
2. **Сбор данных о документах, относящихся к конкретному коду товара в приложении GOLD**.
3. **Проверка данных собранных из приложения GOLD на интернет-ресурсах**.

### Описание этапов проверки
#### 1. Создание предварительного DataFrame
Из входного файла с использованием библиотеки `pandas` создается DataFrame с тремя колонками:
    - порядковый номер АМ 
    - код товара 
    - наименование товара 
DataFrame сохраняется в файл `before_checking_in_gold.xlsx`.

#### 2. Сбор документов из системы ГОЛД

Для сбора документов используется библиотека `pyautogui`. Программа автоматизирует следующие шаги:
- Запуск программы ГОЛД: навигация по меню, ввод логина и пароля, переход к карточке товара.
- Ввод номера продукта, извлечение и сохранение данных о документах.
- Сопоставление данных изготовителя с кодами и наименованиями из `dict_applicant.json`.
- Сохранение всех данных в DataFrame. В случае ошибки, DataFrame сохраняется в файл `gold_data.xlsx`.
- Сохранение последнего проверенного номера строки в файл `last_viewed_in_gold.txt`.

#### 3. Проверка данных собранных из приложения GOLD на интернет-ресурсах

После завершения сбора данных из ГОЛД, начинается этап проверки актуальности деклараций. Для этого используется пакет `web_monitoring`:

- Чтение файла с данными из ГОЛД построчно, проверка номера документа и сопоставление с паттернами.
- Проверка документа на наличие в категориях: ФСА декларации, ФСА сертификаты, СГР и международные документы. Отказные письма не обрабатываются.

Проверка осуществляется через браузер Google Chrome и библиотеку Selenium. В браузере создаются вкладки для следующих сайтов:
- Сайт ФСА для деклараций.
- Сайт ФСА для сертификатов.
- Сайт для проверки СГР.
- Сайт rusprofile для проверки адресов юридических лиц.
- Сайт egrul для проверки адресов юридических лиц.
- Сайт для проверки актуальности ГОСТ.

В зависимости от типа декларации для проверки используются классы-парсеры:
- Базовый абстрактный класс, содержащий абстрактные методы `collect_data`, методы сбора адресов и ГОСТ.
- Класс для парсинга ФСА деклараций.
- Класс для парсинга ФСА сертификатов.
- Класс-парсер для СГР.

Парсер вводит на соответствующем сайте номер документа, находит подходящий документ и собирает данные. 
Далее проводится логика проверки и сопоставления адресов на сайтах rusprofile и egrul. 
Данные с rusprofile извлекаются через парсинг, с сайта egrul - скачивается PDF-файл и из него извлекается адрес юрлица. 
Также проверяется актуальность ГОСТ.

Все данные сохраняются в DataFrame. В случае возникновения исключений DataFrame сохраняется в файл
и отслеживается последний проверенный номер строки. По окончании проверки итоговый DataFrame преобразуется, 
устанавливается мультииндекс и сохраняется  в отдельный файл. Также выбираются строки с невалидными данными и
сохраняются в отдельный файл.

Также имеется модуль для проверки международных документов, данный код выведен из общего кода, 
так как сайт для проверки этих документов работает медленно.


## Структура проекта

### Файлы и папки в корне проекта:

- `.gitignore` — файл для исключения файлов и папок из репозитория Git.
- `chromedriver.exe` — исполняемый файл для работы с веб-драйвером Chrome.
- `pyproject.toml` — файл конфигурации проекта.
- `structure.txt` — файл с описанием структуры проекта.


### Основной пакет `monitoring`:

- `__init__.py` — инициализация пакета.
- `launch_monitoring_package.py` — запуск всего проекта. Организует проверку, отслеживает этапы и запускает необходимые модули.
- `запуск программы мониторинга.bat` — скрипт для запуска программы мониторинга.

#### Пакет `common`: 

пакет с модулями, содержащими общие данные, константы, функции, используемыми более чем одним модулем

- `__init__.py` — инициализация пакета.
- `config.py` — файл конфигурации с логами, паролями и данными прокси.
- `constants.py` — файл с константами.
- `document_dataclass.py` — класс для хранения информации по документам и методы работы с ними.
- `exceptions.py` — файл с пользовательскими исключениями.
- `logger_config.py` — конфигурация логгера.
- `work_with_files_and_dirs.py` — функции для работы с файлами, директориями и процессами.

#### Пакет `monitoring_process`: 

пакет для организация мониторинга на верхнем уровне

- `__init__.py` — инициализация пакета.
- `monitoring_helpers.py` — вспомогательные функции и классы.
- `monitoring_in_web.py` — организация веб мониторинга.
- `process_result_file.py` — подготовка и обработка выходных файлов.

#### Пакет `web`:

пакет для работы в вебе через браузер работает на нижнем уровне под monitoring_process 

- `__init__.py` — инициализация пакета.
- `add_international_docs.py` — добавление международных деклараций.
- `verify_addresses.py` — логика проверки адресов на соответствие.
- `work_with_browser.py` — организация работы в браузере.

##### Пакет `parsers`:

пакет, содержащий парсеры для соответствующих сайтов

- `__init__.py` — инициализация пакета.
- `base_parser.py` — базовый парсер.
- `fsa_parser.py` — парсеры для сайта ФСА.
- `sgr_parser.py` — парсер для сайта проверки СГР.

#### Пакет `intern_docs`:

Пакет для проверки международных документов.

- `__init__.py` — инициализация пакета.
- `check_intern_docs.py` — проверка международных документов.
- `helpers.py` — вспомогательные функции.
- `parser.py` — парсер международных документов.

### Пакет `gold`:

Пакет с кодом для сбора данных из системы ГОЛД.

- `__init__.py` — инициализация пакета.
- `data_manager.py` — управление данными.
- `dict_applicant.json` — словарь с кодами и наименованиями юридических лиц.
- `get_all_applicant.py` — получение кодов и наименований юридических лиц.
- `launch_and_navigate.py` — запуск и навигация по меню ГОЛД.
- `screenshot_work.py` — работа со скриншотами с помощью pyautogui.

### Папки со скриншотами:

- `screenshots` — папка со скриншотами.
  - `the_declarations_status` — скриншоты для карточки товара.
- `screenshots_big_display` — папка со скриншотами для большого дисплея.
  - `the_declarations_status` — скриншоты статусов.


## Схематичная структура проекта представлена в корневом файле:
### structure.txt

## Зависимости проекта определены в:
### pyproject.toml

## Установка:
1. Клонировать репозиторий: git clone https://github.com/Ruslan91111/declarations
2. Установить Poetry.
3. Установить зависимости из `pyproject.toml`.
4. Разместить в корневой директории chromedriver.exe, соответствующий версии chrome браузера.
5. Запустить: python launch_monitoring_package.py
6. Ввести путь к файлу xlsx, содержащему данные по декларациям, нуждающимся в проверке.