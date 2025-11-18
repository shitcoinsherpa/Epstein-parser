@echo off
echo ============================================
echo Installing dependencies for Epstein Analyzer
echo ============================================
echo.

echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install gradio requests Pillow

echo.
echo ============================================
echo Build complete!
echo ============================================
echo.
echo Run run.bat to start the application
pause
