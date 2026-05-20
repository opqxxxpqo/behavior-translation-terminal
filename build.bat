@echo off
chcp 65001 >nul
cd /d "%~dp0"
set LOCAL_TMP=%~dp0.tmp
if not exist "%LOCAL_TMP%" mkdir "%LOCAL_TMP%"
set TMP=%LOCAL_TMP%
set TEMP=%LOCAL_TMP%

echo === 乐团指挥 build ===
echo.

set PYTHON_EXE=%~dp0.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python 不可用
        echo 请先装 Python 3.10+ 并加入 PATH，或运行 setup.bat
        pause
        exit /b 1
    )
    set PYTHON_EXE=python
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python 不可用
    pause
    exit /b 1
)
"%PYTHON_EXE%" --version

echo.
echo 安装 PyInstaller + 运行时依赖...
"%PYTHON_EXE%" -m ensurepip --upgrade >nul 2>&1
"%PYTHON_EXE%" -m pip install --upgrade pip --quiet
"%PYTHON_EXE%" -m pip install --quiet pyinstaller -r requirements.txt
if errorlevel 1 (
    echo [ERROR] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 清理旧产物...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist 乐团指挥录制.spec del /q 乐团指挥录制.spec

echo.
echo 开始打包 (1-3 分钟)...
"%PYTHON_EXE%" -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name "乐团指挥录制" ^
    --collect-all webview ^
    --hidden-import clr_loader ^
    --hidden-import webview.platforms.edgechromium ^
    --add-data "desktop.html;." ^
    --add-data "renderer.html;." ^
    --add-data "samples;samples" ^
    recorder.py

if errorlevel 1 (
    echo.
    echo [ERROR] 打包失败，查看上面输出
    pause
    exit /b 1
)

echo.
echo === 完成 ===
echo 产物: %~dp0dist\乐团指挥录制.exe
echo.
echo 用法：双击 exe 打开桌面录制终端，点 [REC] 开始记录。
echo 停止后会自动载入回放页；日志会写到 exe 同目录的 sessions\ 文件夹下。
echo.
pause
