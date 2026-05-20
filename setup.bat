@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === 乐团指挥 setup ===
echo.

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

python --version
echo.
echo 安装依赖（pynput / pywebview）...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] 依赖安装失败，检查网络或 pip 源
    pause
    exit /b 1
)

echo.
echo === 完成 ===
echo 以后双击 start.bat 打开窗口，再点“开始”录制。
echo 记录中可以点“后台运行”最小化，结束后会保存并加载回看。
echo.
pause
