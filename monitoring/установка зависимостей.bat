@echo off
python -m venv venv
call venv\Scripts\activate.bat
poetry install
exit