"""
乐团指挥：单窗口录制器 + 回看器。
双击 exe → 弹窗 → 用户点"开始"才开始录制。停止时弹窗重命名 jsonl。

Privacy: keyboard events are categorized (letter/number/modifier/backspace/
space/enter/tab/arrow/symbol/other) before being written to disk. Raw keycodes
and typed characters are never persisted.
"""

import base64
import ctypes
import json
import os
import re
import sys
import threading
import time
import traceback
import uuid
from ctypes import wintypes
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
    RESOURCE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent
    RESOURCE_DIR = BASE_DIR

LOG_DIR = BASE_DIR / "sessions"
LOG_DIR.mkdir(exist_ok=True)
EXPORT_DIR = BASE_DIR / "exports"

MOUSE_HZ = 30
MOUSE_MIN_INTERVAL = 1.0 / MOUSE_HZ
IDLE_THRESHOLD_S = 300
WATCHDOG_INTERVAL_S = 10

# ----- Mutable state -----
_last_mouse_t = 0.0
_idle_active = False
_paused = False
_log_file = None
_log_path = None
_session_id = None
_session_start_time = None
_kb_listener = None
_ms_listener = None
_state = "idle"  # "idle" | "recording" | "paused"
_state_lock = threading.RLock()
_write_lock = threading.Lock()
_stop_event = threading.Event()
_press_cat: dict = {}


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def _os_idle_seconds() -> float:
    if sys.platform != "win32":
        return 0.0
    info = _LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    millis = ctypes.windll.kernel32.GetTickCount64() - info.dwTime
    return millis / 1000.0


def _now_rel() -> float:
    if _session_start_time is None:
        return 0.0
    return round(time.time() - _session_start_time, 4)


def _write_line(obj: dict) -> None:
    if _log_file is None or _log_file.closed:
        return
    _log_file.write(json.dumps(obj, ensure_ascii=False) + "\n")
    _log_file.flush()


def write_event(event: dict) -> None:
    global _idle_active
    if _log_file is None or _log_file.closed:
        return
    skip_idle_close = event["type"] in (
        "idle_start", "idle_end", "session_start", "session_end",
    )
    with _write_lock:
        if _idle_active and not skip_idle_close:
            _write_line({"t": _now_rel(), "type": "idle_end"})
            _idle_active = False
        event["t"] = _now_rel()
        _write_line(event)


def _categorize_char(ch: str) -> str:
    if ch.isalpha(): return "letter"
    if ch.isdigit(): return "number"
    return "symbol"


def _categorize_special(key) -> str:
    name = str(key).replace("Key.", "")
    if name in ("shift", "shift_r", "ctrl", "ctrl_r", "alt", "alt_r",
                "cmd", "cmd_r", "caps_lock"): return "modifier"
    if name in ("backspace", "delete"): return "backspace"
    if name == "space": return "space"
    if name in ("enter", "return"): return "enter"
    if name == "tab": return "tab"
    if name in ("up", "down", "left", "right"): return "arrow"
    if name.startswith("f") and name[1:].isdigit(): return "fn"
    if name == "esc": return "esc"
    return "other"


def _classify(key) -> str:
    if hasattr(key, "char") and key.char is not None:
        return _categorize_char(key.char)
    return _categorize_special(key)


def on_press(key):
    if _paused or _state == "idle":
        return
    cat = _classify(key)
    try:
        _press_cat[key] = cat
    except TypeError:
        pass
    write_event({"type": "key_down", "cat": cat})


def on_release(key):
    if _paused or _state == "idle":
        return
    cat = _press_cat.pop(key, None) if key.__hash__ is not None else None
    if cat is None:
        cat = _classify(key)
    write_event({"type": "key_up", "cat": cat})


def on_move(x, y):
    global _last_mouse_t
    if _paused or _state == "idle":
        return
    now = time.time()
    if now - _last_mouse_t < MOUSE_MIN_INTERVAL:
        return
    _last_mouse_t = now
    write_event({"type": "mouse_move", "x": x, "y": y})


def on_click(x, y, button, pressed):
    if _paused or _state == "idle":
        return
    write_event({"type": "mouse_click", "x": x, "y": y,
                 "button": str(button).replace("Button.", ""), "pressed": pressed})


def on_scroll(x, y, dx, dy):
    if _paused or _state == "idle":
        return
    write_event({"type": "mouse_scroll", "x": x, "y": y, "dx": dx, "dy": dy})


def _start_listeners():
    from pynput import keyboard, mouse
    kb = keyboard.Listener(on_press=on_press, on_release=on_release)
    ms = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    kb.start()
    ms.start()
    return kb, ms


def watchdog():
    global _kb_listener, _ms_listener, _idle_active
    while not _stop_event.is_set():
        _stop_event.wait(timeout=WATCHDOG_INTERVAL_S)
        if _stop_event.is_set():
            break
        if _paused or _state == "idle":
            continue

        idle_s = _os_idle_seconds()
        if idle_s >= IDLE_THRESHOLD_S:
            with _write_lock:
                if (not _idle_active
                        and _log_file is not None and not _log_file.closed):
                    _idle_active = True
                    _write_line({"t": _now_rel(), "type": "idle_start",
                                 "idle_s": round(idle_s, 1)})

        dead = []
        if _kb_listener is not None and not _kb_listener.is_alive():
            dead.append("keyboard")
        if _ms_listener is not None and not _ms_listener.is_alive():
            dead.append("mouse")
        if dead:
            write_event({"type": "listener_died", "which": dead})
            for L in (_kb_listener, _ms_listener):
                try:
                    L.stop()
                except Exception:
                    pass
            _kb_listener, _ms_listener = _start_listeners()
            write_event({"type": "listener_restarted"})


# ----- Recording control API (called from window) -----

def start_recording():
    global _log_file, _log_path, _session_id, _session_start_time
    global _kb_listener, _ms_listener, _state, _paused, _idle_active
    with _state_lock:
        if _state != "idle":
            return {"ok": False, "msg": "already recording"}
        _session_id = uuid.uuid4().hex[:8]
        _session_start_time = time.time()
        _log_path = LOG_DIR / f"{int(_session_start_time)}_{_session_id}.jsonl"
        _log_file = open(_log_path, "a", encoding="utf-8")
        _paused = False
        _idle_active = False
        _press_cat.clear()
        _stop_event.clear()
        write_event({
            "type": "session_start",
            "session_id": _session_id,
            "wall_clock": _session_start_time,
            "mouse_hz": MOUSE_HZ,
            "platform": sys.platform,
        })
        _kb_listener, _ms_listener = _start_listeners()
        threading.Thread(target=watchdog, daemon=True).start()
        _state = "recording"
    return {"ok": True, "session_id": _session_id, "path": str(_log_path)}


def pause_recording():
    global _paused, _state
    with _state_lock:
        if _state == "idle":
            return {"ok": False, "msg": "not recording"}
        _paused = not _paused
        write_event({"type": "recording_paused" if _paused else "recording_resumed"})
        _state = "paused" if _paused else "recording"
    return {"ok": True, "paused": _paused, "state": _state}


def stop_recording(new_name=None):
    global _log_file, _log_path, _kb_listener, _ms_listener
    global _state, _paused, _session_id, _session_start_time
    with _state_lock:
        if _state == "idle":
            return {"ok": False, "msg": "not recording"}
        write_event({"type": "session_end"})
        for L in (_kb_listener, _ms_listener):
            try:
                if L is not None:
                    L.stop()
            except Exception:
                pass
        _kb_listener = None
        _ms_listener = None
        _stop_event.set()
        if _log_file is not None and not _log_file.closed:
            _log_file.close()
        old_path = _log_path
        final_path = old_path
        if new_name:
            safe = re.sub(r'[\\/:*?"<>|]', "_", str(new_name)).strip()
            if safe and not safe.lower().endswith(".jsonl"):
                safe += ".jsonl"
            if safe:
                cand = LOG_DIR / safe
                if cand.exists() and cand.resolve() != old_path.resolve():
                    cand = LOG_DIR / f"{cand.stem}_{uuid.uuid4().hex[:4]}.jsonl"
                try:
                    old_path.rename(cand)
                    final_path = cand
                except Exception:
                    final_path = old_path
        _state = "idle"
        _paused = False
        _log_path = None
        _session_id = None
        _session_start_time = None
    return {"ok": True, "path": str(final_path), "name": final_path.name}


def get_recording_status():
    with _state_lock:
        if _state == "idle":
            return {"state": "idle"}
        size = _log_path.stat().st_size if _log_path and _log_path.exists() else 0
        elapsed = time.time() - _session_start_time if _session_start_time else 0
        return {
            "state": _state,
            "session_id": _session_id,
            "elapsed": round(elapsed, 1),
            "size": size,
            "path": str(_log_path) if _log_path else "",
            "name": _log_path.name if _log_path else "",
        }


# ----- pywebview JS API -----

class Api:
    def __init__(self):
        self.window = None

    def set_window(self, window):
        self.window = window

    def list_sessions(self):
        if not LOG_DIR.exists():
            return []
        out = []
        for f in sorted(LOG_DIR.glob("*.jsonl"),
                        key=lambda p: -p.stat().st_mtime):
            st = f.stat()
            out.append({
                "name": f.name,
                "path": str(f),
                "size": st.st_size,
                "mtime": st.st_mtime,
            })
        return out

    def read_session(self, path: str) -> str:
        try:
            p = Path(path)
            if p.parent.resolve() != LOG_DIR.resolve():
                return ""
            if p.suffix.lower() != ".jsonl":
                return ""
            return p.read_text(encoding="utf-8")
        except Exception:
            return ""

    def save_wav(self, name: str, b64: str) -> str:
        EXPORT_DIR.mkdir(exist_ok=True)
        safe = re.sub(r'[\\/:*?"<>|]', "_", name) or "out.wav"
        out = EXPORT_DIR / safe
        out.write_bytes(base64.b64decode(b64))
        try:
            os.startfile(str(EXPORT_DIR))
        except Exception:
            pass
        return str(out)

    def start_recording(self):
        return start_recording()

    def pause_recording(self):
        return pause_recording()

    def stop_recording(self, new_name=None):
        return stop_recording(new_name)

    def get_recording_status(self):
        return get_recording_status()

    def minimize_window(self):
        try:
            if self.window is None:
                return False
            self.window.minimize()
            return True
        except Exception:
            return False

    def open_log_folder(self):
        try:
            os.startfile(str(LOG_DIR))
            return True
        except Exception:
            return False

    def delete_session(self, path: str) -> bool:
        try:
            p = Path(path)
            if p.parent.resolve() != LOG_DIR.resolve():
                return False
            if p.suffix.lower() != ".jsonl":
                return False
            p.unlink()
            return True
        except Exception:
            return False


def main_window():
    try:
        import webview
    except ImportError:
        _crash_log(RuntimeError("pywebview missing"))
        sys.exit(2)

    renderer = RESOURCE_DIR / "renderer.html"
    if not renderer.exists():
        _crash_log(FileNotFoundError(f"renderer.html missing: {renderer}"))
        sys.exit(3)

    api = Api()
    window = webview.create_window(
        "乐团指挥",
        url=renderer.as_uri(),
        js_api=api,
        width=1200, height=820,
        background_color="#0a0a0f",
    )
    api.set_window(window)

    def on_closing():
        # Auto-save if still recording when window closes
        try:
            if _state != "idle":
                stop_recording(None)
        except Exception:
            pass
        return True

    try:
        window.events.closing += on_closing
    except Exception:
        pass

    webview.start()


def _crash_log(exc):
    try:
        LOG_DIR.mkdir(exist_ok=True)
        with open(LOG_DIR / "crash.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.ctime()} ---\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        if "--terminal" in sys.argv:
            # Dev/headless fallback
            import signal
            print("Terminal mode. Ctrl+C to stop.")
            start_recording()
            stop_flag = threading.Event()
            signal.signal(signal.SIGINT, lambda *_: stop_flag.set())
            stop_flag.wait()
            r = stop_recording(None)
            print("Saved:", r.get("path"))
        else:
            main_window()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        _crash_log(e)
        raise
