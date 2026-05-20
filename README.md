# 乐团指挥 / Behavior Translation Terminal

把电脑前的键盘与鼠标行为转译成音乐和 ASCII/CRT 风格可视化。

这个项目有两个分享形态：

- **桌面程序**：用于真实录制全局键盘/鼠标行为，并回放生成音乐。
- **Web Demo**：用于展示视觉与声音效果，可载入 `.jsonl` 记录或生成模拟数据。

## 下载与运行

### 方式一：直接运行 Windows 程序

打包产物位于：

```txt
dist\乐团指挥录制.exe
```

双击后打开桌面录制终端。

操作：

1. 点击 `[ REC ]` 开始录制。
2. 点击 `❚❚` 暂停/继续录制。
3. 点击 `■` 停止录制，并给 session 命名。
4. 停止后会自动载入下方回放界面。
5. 点击 `[ TRAY ]` 隐藏到系统托盘。
6. 从托盘菜单可显示窗口、打开记录文件夹或退出。

### 方式二：源码运行桌面程序

首次安装：

```bat
setup.bat
```

启动：

```bat
start.bat
```

### 方式三：启动 Web Demo

在线 Demo：

```txt
https://opqxxxpqo.github.io/behavior-translation-terminal/renderer.html
```

本地 Demo：

```bat
web-demo.bat
```

然后打开：

```txt
http://127.0.0.1:8765/renderer.html
```

Web Demo 不会记录全局键盘和鼠标，只用于回放、上传 `.jsonl`、模拟数据和展示。

## 打包

```bat
build.bat
```

生成：

```txt
dist\乐团指挥录制.exe
```

## 数据与隐私

程序默认只在本机保存数据，目录为：

```txt
sessions\
```

记录内容包括：

- 键盘事件类别，例如 `letter`、`number`、`space`、`enter`、`backspace`
- 鼠标移动坐标
- 鼠标点击与滚动
- 每个事件相对于录制开始的时间

不会保存：

- 具体输入文字
- 原始按键字符
- 剪贴板内容
- 屏幕画面

## 文件说明

- `desktop.html`：桌面程序入口，负责录制控制和托盘操作。
- `renderer.html`：Web Demo 与回放播放器。
- `recorder.py`：本地录制、session 管理、pywebview 桌面窗口。
- `build.bat`：打包 Windows 程序。
- `web-demo.bat`：启动本地 Web Demo。
