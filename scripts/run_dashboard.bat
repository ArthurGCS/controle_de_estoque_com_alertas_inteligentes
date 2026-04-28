@echo off
setlocal

set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%\src"
set "PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    set "PYTHON=python"
)

"%PYTHON%" -m streamlit run "src\estoque_monitor\dashboard.py" --server.address localhost --server.port 8501

endlocal
