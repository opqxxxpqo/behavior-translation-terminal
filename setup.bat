@echo off
chcp 65001 >nul
cd /d "%~dp0"
set LOCAL_TMP=%~dp0.tmp
if not exist "%LOCAL_TMP%" mkdir "%LOCAL_TMP%"
set TMP=%LOCAL_TMP%
set TEMP=%LOCAL_TMP%

echo === 乐团指挥 setup ===
echo.

set PYTHON_EXE=%~dp0.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] 未检测到 Python
        echo.
        echo 请到 https://www.python.org/downloads/ 安装 Python 3.10 或更高版本
        echo 安装时务必勾选 "Add Python to PATH"
        echo 安装完成后重新双击此脚本
        echo.
        pause
        exit /b 1
    )
    echo 创建本地虚拟环境 .venv ...
    python -m venv "%~dp0.venv"
)

if not exist "%PYTHON_EXE%" (
    echo [ERROR] 未检测到 Python
    pause
    exit /b 1
)

"%PYTHON_EXE%" --version
echo.
echo 安装依赖（pynput / pywebview）...
"%PYTHON_EXE%" -m ensurepip --upgrade >nul 2>&1
"%PYTHON_EXE%" -m pip install --upgrade pip --quiet
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] 依赖安装失败，检查网络或 pip 源
    pause
    exit /b 1
)

echo.
echo === 完成 ===
echo 以后双击 start.bat 打开桌面录制终端。
echo 记录中可以点 [MIN] 最小化；停止后会保存并自动载入回放。
echo.
pause
