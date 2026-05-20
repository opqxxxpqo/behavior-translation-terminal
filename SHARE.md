# 乐团指挥分享方案

## 推荐形态

正式分享版使用 Windows 桌面程序。

原因：完整体验需要全局键盘和鼠标监听，浏览器网页只能稳定记录当前页面里的输入，不能可靠记录用户在其他软件中的工作/娱乐行为。

Web 版适合作为展示 Demo：

- 打开 `renderer.html`
- 载入 `.jsonl` 记录
- 或点击 `[ SIM DATA ]` 体验视觉和声音

## 本地运行

首次运行：

```bat
setup.bat
```

启动桌面录制终端：

```bat
start.bat
```

桌面操作：

1. `[ REC ]` 开始录制。
2. `❚❚` 暂停/继续。
3. `■` 停止并命名记录。
4. `[ TRAY ]` 隐藏到系统托盘。
5. 托盘菜单可显示窗口、打开记录文件夹或退出。

启动 Web Demo：

```bat
web-demo.bat
```

Web Demo 地址：

```txt
http://127.0.0.1:8765/renderer.html
```

在线 Demo 地址：

```txt
https://opqxxxpqo.github.io/behavior-translation-terminal/renderer.html
```

## 打包 Windows 程序

```bat
build.bat
```

产物：

```txt
dist\乐团指挥录制.exe
```

GitHub Release 下载页：

```txt
https://github.com/opqxxxpqo/behavior-translation-terminal/releases/latest
```

## 对外隐私说明

建议分享时明确说明：

- 不记录用户输入的具体文字
- 键盘只保存类别，例如 letter、number、space、enter、backspace
- 鼠标保存移动、点击、滚动和时间
- 数据默认保存在本机 `sessions` 文件夹
- 用户可以暂停、停止、删除或不分享记录文件

## 文件分工

- `desktop.html`：桌面程序入口，负责录制控制和嵌入回放页
- `renderer.html`：Web Demo 和回放播放器
- `recorder.py`：本地录制、session 管理和桌面窗口
- `web-demo.bat`：启动网页展示版
- `build.bat`：打包 Windows exe
