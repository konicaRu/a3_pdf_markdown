@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment was not found.
    echo Run setup first:
    echo uv sync --python 3.11.15
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m a3_pdf_markdown.app.main

