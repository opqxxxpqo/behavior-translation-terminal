@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PORT=8765
set PYTHON_EXE=%~dp0.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=python

echo === 乐团指挥 Web Demo ===
echo.
echo 地址: http://127.0.0.1:%PORT%/renderer.html
echo 关闭这个窗口即可停止 Web Demo。
echo.
"%PYTHON_EXE%" -m http.server %PORT%
