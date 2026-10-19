@echo off
echo Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo Setup done. Now run:  python src\cleaning.py
