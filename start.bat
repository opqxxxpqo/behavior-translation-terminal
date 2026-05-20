@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHONW_EXE=%~dp0.venv\Scripts\pythonw.exe
if not exist "%PYTHONW_EXE%" (
    where pythonw >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] 找不到 pythonw.exe
        echo 请先运行 setup.bat，或确保 Python 已正确安装到 PATH
        pause
        exit /b 1
    )
    set PYTHONW_EXE=pythonw
)

if "%PYTHONW_EXE%"=="" (
    echo [ERROR] 找不到 pythonw.exe
    pause
    exit /b 1
)

start "" "%PYTHONW_EXE%" "%~dp0recorder.py"

echo.
echo 乐团指挥桌面录制终端已启动。
echo 在窗口里点 [REC] 后才会记录；记录中可点 [MIN] 最小化。
echo.
timeout /t 4 >nul
