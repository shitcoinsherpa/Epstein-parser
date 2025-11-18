@echo off
echo ============================================
echo Starting Epstein Case Analyzer
echo ============================================
echo.

call venv\Scripts\activate.bat

echo The Gradio interface will open at:
echo http://localhost:7860
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
