@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === 乐团指挥 build ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 不可用
    echo 请先装 Python 3.10+ 并加入 PATH，或运行 setup.bat
    pause
    exit /b 1
)
python --version

echo.
echo 安装 PyInstaller + 运行时依赖...
python -m pip install --upgrade pip --quiet
python -m pip install --quiet pyinstaller -r requirements.txt
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
python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name "乐团指挥录制" ^
    --collect-all webview ^
    --hidden-import clr_loader ^
    --hidden-import webview.platforms.edgechromium ^
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
echo 用法：双击 exe 打开窗口，在窗口里点“开始”录制。
echo 记录中可点“后台运行”最小化；结束后日志会写到 exe 同目录的 sessions\ 文件夹下。
echo.
pause
