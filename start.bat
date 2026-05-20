@echo off
chcp 65001 >nul
cd /d "%~dp0"

where pythonw >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 找不到 pythonw.exe
    echo 请先运行 setup.bat，或确保 Python 已正确安装到 PATH
    pause
    exit /b 1
)

start "" pythonw "%~dp0recorder.py"

echo.
echo 乐团指挥窗口已启动。
echo 在窗口里点“开始”后才会记录；记录中可点“后台运行”最小化。
echo.
timeout /t 4 >nul
