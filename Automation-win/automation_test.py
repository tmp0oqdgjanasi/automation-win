import json
import os
import random
import subprocess
import sys
import threading
import time
import tkinter as tk

from tkinter import (
    filedialog,
    messagebox,
    simpledialog,
    ttk
)

from io import BytesIO

from PIL import Image, ImageChops

from pynput import mouse, keyboard

import win32gui


# ============================================================
# 程序路径
# ============================================================

def application_dir():
    """
    获取程序所在目录。

    PyInstaller --onefile：
        sys.executable 所在目录 = EXE 所在目录

    普通 Python：
        __file__ 所在目录
    """

    if getattr(sys, "frozen", False):
        return os.path.dirname(
            os.path.abspath(sys.executable)
        )

    return os.path.dirname(
        os.path.abspath(__file__)
    )


APP_DIR = application_dir()

RECORDING_DIR = os.path.join(
    APP_DIR,
    "recordings"
)

os.makedirs(
    RECORDING_DIR,
    exist_ok=True
)


# ============================================================
# ADB
# ============================================================

def get_adb_path():

    # --------------------------------------------------------
    # 1. PyInstaller onefile 临时目录
    # --------------------------------------------------------

    if getattr(sys, "frozen", False):

        base = getattr(
            sys,
            "_MEIPASS",
            APP_DIR
        )

        path = os.path.join(
            base,
            "adb",
            "adb.exe"
        )

        if os.path.exists(path):
            return path

    # --------------------------------------------------------
    # 2. EXE 同目录 / adb
    # --------------------------------------------------------

    path = os.path.join(
        APP_DIR,
        "adb",
        "adb.exe"
    )

    if os.path.exists(path):
        return path

    # --------------------------------------------------------
    # 3. 当前目录
    # --------------------------------------------------------

    path = os.path.join(
        APP_DIR,
        "adb.exe"
    )

    if os.path.exists(path):
        return path

    # --------------------------------------------------------
    # 4. 系统 PATH
    # --------------------------------------------------------

    return "adb"


ADB = get_adb_path()


def adb(*args, timeout=10):

    try:

        result = subprocess.run(
            [ADB, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return result.stdout.decode(
            "utf-8",
            errors="ignore"
        )

    except Exception as e:

        print(
            "ADB error:",
            e
        )

        return ""


def adb_bytes(*args, timeout=10):

    try:

        result = subprocess.run(
            [ADB, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return result.stdout

    except Exception:

        return b""


def adb_available():

    output = adb(
        "version"
    )

    return "Android Debug Bridge" in output


def adb_devices():

    output = adb(
        "devices"
    )

    devices = []

    for line in output.splitlines():

        line = line.strip()

        if (
            not line
            or line.startswith("List of devices")
        ):
            continue

        parts = line.split()

        if len(parts) >= 2:

            serial = parts[0]
            state = parts[1]

            devices.append(
                (serial, state)
            )

    return devices


# ============================================================
# Android
# ============================================================

def get_screen_size():

    output = adb(
        "shell",
        "wm",
        "size"
    )

    for line in output.splitlines():

        if "Physical size:" in line:

            try:

                value = line.split(
                    ":",
                    1
                )[1].strip()

                w, h = value.split("x")

                return (
                    int(w),
                    int(h)
                )

            except Exception:
                pass

    return (
        1080,
        1920
    )


def get_foreground_package():

    output = adb(
        "shell",
        "dumpsys",
        "window",
        "windows"
    )

    for line in output.splitlines():

        if (
            "mCurrentFocus" in line
            or
            "mFocusedApp" in line
        ):

            parts = (
                line
                .replace("{", " ")
                .replace("}", " ")
                .split()
            )

            for part in parts:

                if "/" in part:

                    package = part.split(
                        "/",
                        1
                    )[0]

                    if "." in package:

                        return package

    return "unknown"


def launch_package(package):

    if not package:
        return False

    output = adb(
        "shell",
        "monkey",
        "-p",
        package,
        "1"
    )

    return True


# ============================================================
# Emulator Window
# ============================================================

EMULATOR_TITLE_KEYWORDS = [
    "Android Emulator",
    "Emulator"
]


def find_emulator_window():

    windows = []

    def callback(hwnd, _):

        if not win32gui.IsWindowVisible(hwnd):
            return

        title = win32gui.GetWindowText(hwnd)

        if not title:
            return

        title_lower = title.lower()

        for keyword in EMULATOR_TITLE_KEYWORDS:

            if keyword.lower() in title_lower:

                windows.append(
                    (
                        hwnd,
                        title
                    )
                )

                return

    win32gui.EnumWindows(
        callback,
        None
    )

    if windows:

        return windows[0]

    return (
        None,
        None
    )


def get_client_area(hwnd):

    rect = win32gui.GetClientRect(
        hwnd
    )

    left, top = win32gui.ClientToScreen(
        hwnd,
        (
            rect[0],
            rect[1]
        )
    )

    right, bottom = win32gui.ClientToScreen(
        hwnd,
        (
            rect[2],
            rect[3]
        )
    )

    return (
        left,
        top,
        right,
        bottom
    )


# ============================================================
# 坐标转换
# ============================================================

def desktop_to_android(
    x,
    y,
    client_rect,
    android_width,
    android_height
):

    left, top, right, bottom = client_rect

    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        return None

    if x < left or x >= right:
        return None

    if y < top or y >= bottom:
        return None

    rx = (
        x - left
    ) / width

    ry = (
        y - top
    ) / height

    android_x = (
        rx *
        android_width
    )

    android_y = (
        ry *
        android_height
    )

    return (
        round(android_x, 2),
        round(android_y, 2),
        round(rx, 6),
        round(ry, 6)
    )


def normalize_to_screen(
    normalized_x,
    normalized_y
):

    width, height = get_screen_size()

    x = int(
        normalized_x *
        width
    )

    y = int(
        normalized_y *
        height
    )

    x = max(
        0,
        min(
            width - 1,
            x
        )
    )

    y = max(
        0,
        min(
            height - 1,
            y
        )
    )

    return (
        x,
        y
    )


# ============================================================
# Screenshot
# ============================================================

def screenshot():

    data = adb_bytes(
        "exec-out",
        "screencap",
        "-p",
        timeout=15
    )

    if not data:
        return None

    try:

        return Image.open(
            BytesIO(data)
        ).convert(
            "RGB"
        )

    except Exception:

        return None


def compare_screen(
    image1,
    image2
):

    if image1 is None:
        return 0.0

    if image2 is None:
        return 0.0

    try:

        image1 = image1.resize(
            (64, 64)
        ).convert(
            "L"
        )

        image2 = image2.resize(
            (64, 64)
        ).convert(
            "L"
        )

        diff = ImageChops.difference(
            image1,
            image2
        )

        histogram = diff.histogram()

        total_pixels = 64 * 64

        changed = 0

        for value in range(
            31,
            256
        ):

            changed += histogram[value]

        return (
            changed /
            total_pixels
        )

    except Exception:

        return 0.0


# ============================================================
# Recorder
# ============================================================

class Recorder:

    def __init__(
        self,
        process_name,
        finished_callback=None,
        status_callback=None
    ):

        self.process_name = process_name

        self.finished_callback = (
            finished_callback
        )

        self.status_callback = (
            status_callback
        )

        self.recording = False

        self.start_time = None

        self.events = []

        self.lock = threading.Lock()

        self.mouse_down_time = None

        self.mouse_down_position = None

        self.current_drag = None

        self.last_click_time = None

        self.last_screen = None

        self.change_start = None

        self.change_max = 0

        self.android_width = 1080

        self.android_height = 1920

        self.emulator_hwnd = None

        self.emulator_rect = None

        self.target_package = "unknown"

        self.screen_thread = None

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    def status(self, text):

        print(
            text
        )

        if self.status_callback:

            self.status_callback(
                text
            )

    # --------------------------------------------------------
    # Start
    # --------------------------------------------------------

    def start(self):

        if self.recording:
            return False

        hwnd, title = (
            find_emulator_window()
        )

        if not hwnd:

            if self.finished_callback:

                self.finished_callback(
                    False,
                    None,
                    "没有找到 Android Emulator 窗口。"
                )

            return False

        self.emulator_hwnd = hwnd

        self.emulator_rect = (
            get_client_area(hwnd)
        )

        (
            self.android_width,
            self.android_height
        ) = get_screen_size()

        self.target_package = (
            get_foreground_package()
        )

        self.events = []

        self.start_time = time.time()

        self.last_click_time = None

        self.last_screen = screenshot()

        self.change_start = None

        self.change_max = 0

        self.mouse_down_time = None

        self.mouse_down_position = None

        self.current_drag = None

        self.recording = True

        self.status(
            f"{self.process_name} 开始录制"
        )

        self.status(
            f"Emulator：{title}"
        )

        self.status(
            f"Android："
            f"{self.android_width} x "
            f"{self.android_height}"
        )

        self.status(
            f"目标 App："
            f"{self.target_package}"
        )

        self.status(
            "按 Space 停止录制"
        )

        self.screen_thread = threading.Thread(
            target=self.screen_monitor,
            daemon=True
        )

        self.screen_thread.start()

        return True

    # --------------------------------------------------------
    # Stop
    # --------------------------------------------------------

    def stop(self):

        if not self.recording:
            return

        self.recording = False

        self.status(
            f"{self.process_name} 录制结束"
        )

        if self.finished_callback:

            self.finished_callback(
                True,
                self.build_json(),
                None
            )

    # --------------------------------------------------------
    # Build JSON
    # --------------------------------------------------------

    def build_json(self):

        with self.lock:

            actions = list(
                self.events
            )

        return {

            "schema":
                "android_emulator_process",

            "version":
                3,

            "recorded_at":
                int(time.time()),

            "record_type":
                self.process_name,

            "device": {

                "screen_width":
                    self.android_width,

                "screen_height":
                    self.android_height
            },

            "target": {

                "package":
                    self.target_package
            },

            "click": {

                "min_interval_s":
                    0
            },

            "screen_detection": {

                "change_threshold":
                    0.50,

                "required_duration_s":
                    5.0
            },

            "actions":
                actions
        }

    # --------------------------------------------------------
    # Mouse Down
    # --------------------------------------------------------

    def mouse_down(
        self,
        x,
        y,
        button
    ):

        if not self.recording:
            return

        if button != mouse.Button.left:
            return

        converted = desktop_to_android(
            x,
            y,
            self.emulator_rect,
            self.android_width,
            self.android_height
        )

        if converted is None:
            return

        (
            ax,
            ay,
            rx,
            ry
        ) = converted

        now = time.time()

        self.mouse_down_time = now

        self.mouse_down_position = (
            ax,
            ay,
            rx,
            ry
        )

        self.current_drag = [
            (
                ax,
                ay,
                now
            )
        ]

    # --------------------------------------------------------
    # Mouse Move
    # --------------------------------------------------------

    def mouse_move(
        self,
        x,
        y
    ):

        if not self.recording:
            return

        if self.mouse_down_time is None:
            return

        converted = desktop_to_android(
            x,
            y,
            self.emulator_rect,
            self.android_width,
            self.android_height
        )

        if converted is None:
            return

        ax, ay, rx, ry = converted

        now = time.time()

        if self.current_drag is not None:

            last = self.current_drag[-1]

            if (
                now -
                last[2]
                >=
                0.02
            ):

                self.current_drag.append(
                    (
                        ax,
                        ay,
                        now
                    )
                )

    # --------------------------------------------------------
    # Mouse Up
    # --------------------------------------------------------

    def mouse_up(
        self,
        x,
        y,
        button
    ):

        if not self.recording:
            return

        if button != mouse.Button.left:
            return

        if self.mouse_down_time is None:
            return

        now = time.time()

        duration = (
            now -
            self.mouse_down_time
        )

        converted = desktop_to_android(
            x,
            y,
            self.emulator_rect,
            self.android_width,
            self.android_height
        )

        if converted is None:

            self.mouse_down_time = None
            self.mouse_down_position = None
            self.current_drag = None

            return

        (
            ax,
            ay,
            rx,
            ry
        ) = converted

        elapsed_ms = int(
            (
                now -
                self.start_time
            ) *
            1000
        )

        # ----------------------------------------------------
        # CLICK
        # ----------------------------------------------------

        if duration <= 0.35:

            interval_ms = None

            if self.last_click_time is not None:

                interval_ms = int(
                    (
                        now -
                        self.last_click_time
                    ) *
                    1000
                )

            event = {

                "action":
                    "click",

                "time_ms":
                    elapsed_ms,

                "x":
                    ax,

                "y":
                    ay,

                "normalized": {

                    "x":
                        rx,

                    "y":
                        ry
                },

                "hold_duration_ms":
                    int(
                        duration *
                        1000
                    ),

                "click_interval_ms":
                    interval_ms,

                "package":
                    get_foreground_package()
            }

            with self.lock:

                self.events.append(
                    event
                )

            self.last_click_time = now

            self.status(
                f"CLICK "
                f"({ax:.1f},{ay:.1f})"
            )

        # ----------------------------------------------------
        # SWIPE
        # ----------------------------------------------------

        else:

            points = []

            if self.current_drag:

                for px, py, pt in (
                    self.current_drag
                ):

                    points.append({

                        "x":
                            px,

                        "y":
                            py,

                        "t_ms":
                            int(
                                (
                                    pt -
                                    self.mouse_down_time
                                ) *
                                1000
                            )
                    })

            points.append({

                "x":
                    ax,

                "y":
                    ay,

                "t_ms":
                    int(
                        duration *
                        1000
                    )
            })

            start = (
                self.mouse_down_position
            )

            event = {

                "action":
                    "swipe",

                "time_ms":
                    elapsed_ms,

                "from": {

                    "x":
                        start[0],

                    "y":
                        start[1],

                    "normalized": {

                        "x":
                            start[2],

                        "y":
                            start[3]
                    }
                },

                "to": {

                    "x":
                        ax,

                    "y":
                        ay,

                    "normalized": {

                        "x":
                            rx,

                        "y":
                            ry
                    }
                },

                "duration_ms":
                    int(
                        duration *
                        1000
                    ),

                "trajectory":
                    points,

                "package":
                    get_foreground_package()
            }

            with self.lock:

                self.events.append(
                    event
                )

            self.status(
                f"SWIPE "
                f"({start[0]:.1f},"
                f"{start[1]:.1f}) -> "
                f"({ax:.1f},{ay:.1f})"
            )

        self.mouse_down_time = None

        self.mouse_down_position = None

        self.current_drag = None

    # --------------------------------------------------------
    # Screen Monitor
    # --------------------------------------------------------

    def screen_monitor(self):

        threshold = 0.50

        required_duration = 5.0

        while self.recording:

            time.sleep(1)

            current = screenshot()

            difference = compare_screen(
                self.last_screen,
                current
            )

            now = time.time()

            if difference > threshold:

                if self.change_start is None:

                    self.change_start = now

                    self.change_max = (
                        difference
                    )

                else:

                    self.change_max = max(
                        self.change_max,
                        difference
                    )

                    duration = (
                        now -
                        self.change_start
                    )

                    if (
                        duration >=
                        required_duration
                    ):

                        event = {

                            "action":
                                "page_change",

                            "time_ms":
                                int(
                                    (
                                        now -
                                        self.start_time
                                    ) *
                                    1000
                                ),

                            "change_ratio":
                                round(
                                    self.change_max,
                                    4
                                ),

                            "stable_duration_s":
                                round(
                                    duration,
                                    2
                                )
                        }

                        with self.lock:

                            self.events.append(
                                event
                            )

                        self.status(
                            "检测到页面变化"
                        )

                        self.change_start = None

                        self.change_max = 0

            else:

                self.change_start = None

                self.change_max = 0

            self.last_screen = current


# ============================================================
# Automation
# ============================================================

class Automation:

    def __init__(
        self,
        status_callback=None
    ):

        self.status_callback = (
            status_callback
        )

        self.running = False

        self.completed = 0

        self.target = 0

        self.process1 = None

        self.process2 = None

        self.base_count = 0

        self.error_count = 0

        self.pause_minutes = 0

        self.min_interval_minutes = 0

        self.click_min_interval_s = 0

        self.last_click_time = None

        # Level 3 参数
        self.human_level = 3

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    def status(self, text):

        print(
            text
        )

        if self.status_callback:

            self.status_callback(
                text
            )

    # --------------------------------------------------------
    # Start
    # --------------------------------------------------------

    def start(
        self,
        process1,
        process2,
        count,
        error,
        pause_minutes,
        min_interval_minutes
    ):

        if self.running:
            return

        self.process1 = process1

        self.process2 = process2

        self.base_count = count

        self.error_count = error

        self.pause_minutes = (
            pause_minutes
        )

        self.min_interval_minutes = (
            min_interval_minutes
        )

        low = max(
            1,
            count - error
        )

        high = max(
            low,
            count + error
        )

        self.target = random.randint(
            low,
            high
        )

        self.completed = 0

        self.running = True

        self.last_click_time = None

        threading.Thread(
            target=self.worker,
            daemon=True
        ).start()

    # --------------------------------------------------------
    # Stop
    # --------------------------------------------------------

    def stop(self):

        self.running = False

        self.status(
            "已停止"
        )

    # --------------------------------------------------------
    # Level 3 random
    # --------------------------------------------------------

    def human_pause(
        self,
        base_seconds,
        minimum_extra=0.03,
        maximum_extra=0.20
    ):

        if base_seconds <= 0:
            return

        extra_max = max(
            minimum_extra,
            min(
                maximum_extra,
                base_seconds * 0.20
            )
        )

        delay = (
            base_seconds +
            random.uniform(
                minimum_extra,
                extra_max
            )
        )

        self.sleep_interruptible(
            delay
        )

    def human_coordinate(
        self,
        x,
        y,
        width,
        height
    ):

        # Level 3：
        # 根据屏幕尺寸做很小的坐标扰动。
        # 不改变录制的 normalized 参数。

        max_offset = max(
            1,
            int(
                min(
                    width,
                    height
                ) *
                0.003
            )
        )

        dx = random.randint(
            -max_offset,
            max_offset
        )

        dy = random.randint(
            -max_offset,
            max_offset
        )

        x += dx

        y += dy

        x = max(
            0,
            min(
                width - 1,
                x
            )
        )

        y = max(
            0,
            min(
                height - 1,
                y
            )
        )

        return (
            x,
            y
        )

    # --------------------------------------------------------
    # Process 1
    # --------------------------------------------------------

    def execute_process1(self):

        target = self.process1.get(
            "target",
            {}
        )

        package = target.get(
            "package"
        )

        if not package:

            self.status(
                "Process 1 缺少目标 App 包名"
            )

            return False

        self.status(
            f"启动目标 App：{package}"
        )

        launch_package(
            package
        )

        # 给 App 一个基础启动时间
        self.human_pause(
            1.0,
            0.20,
            0.80
        )

        self.status(
            "Process 1：开始执行"
        )

        actions = self.process1.get(
            "actions",
            []
        )

        for action in actions:

            if not self.running:

                return False

            action_type = action.get(
                "action"
            )

            if action_type == "click":

                self.execute_click(
                    action
                )

            elif action_type == "swipe":

                self.execute_swipe(
                    action
                )

            elif action_type == "page_change":

                # 录制得到的页面变化：
                # 回放时作为页面稳定等待点。

                duration = action.get(
                    "stable_duration_s",
                    1
                )

                duration = max(
                    1,
                    min(
                        duration,
                        10
                    )
                )

                self.status(
                    "Process 1：等待页面稳定"
                )

                self.sleep_interruptible(
                    duration
                )

        self.status(
            "Process 1：完成"
        )

        return True

    # --------------------------------------------------------
    # Process 2
    # --------------------------------------------------------

    def execute_process2(self):

        actions = self.process2.get(
            "actions",
            []
        )

        if not actions:

            self.status(
                "Process 2 没有动作"
            )

            return False

        for action in actions:

            if not self.running:

                return False

            action_type = action.get(
                "action"
            )

            if action_type == "click":

                self.execute_click(
                    action
                )

            elif action_type == "swipe":

                self.execute_swipe(
                    action
                )

            elif action_type == "page_change":

                duration = action.get(
                    "stable_duration_s",
                    1
                )

                duration = max(
                    1,
                    min(
                        duration,
                        10
                    )
                )

                self.status(
                    "等待页面稳定"
                )

                self.sleep_interruptible(
                    duration
                )

        return True

    # --------------------------------------------------------
    # Click
    # --------------------------------------------------------

    def execute_click(
        self,
        action
    ):

        normalized = action.get(
            "normalized"
        )

        width, height = (
            get_screen_size()
        )

        if normalized:

            x, y = normalize_to_screen(
                normalized["x"],
                normalized["y"]
            )

        else:

            x = int(
                action.get(
                    "x",
                    0
                )
            )

            y = int(
                action.get(
                    "y",
                    0
                )
            )

        # ----------------------------------------------------
        # Level 3 坐标微扰
        # ----------------------------------------------------

        if self.human_level >= 3:

            x, y = self.human_coordinate(
                x,
                y,
                width,
                height
            )

        # ----------------------------------------------------
        # 原始点击间隔
        # ----------------------------------------------------

        recorded_interval = (
            action.get(
                "click_interval_ms"
            )
        )

        if recorded_interval is not None:

            base_interval = (
                recorded_interval /
                1000
            )

        else:

            base_interval = (
                self.click_min_interval_s
            )

        base_interval = max(
            0,
            base_interval
        )

        # ----------------------------------------------------
        # Level 3：
        # 只增加，不缩短原始间隔
        # ----------------------------------------------------

        if self.human_level >= 3:

            random_add = random.uniform(
                0.03,
                max(
                    0.08,
                    base_interval * 0.30
                )
            )

        else:

            random_add = 0

        actual_interval = (
            base_interval +
            random_add
        )

        if (
            self.last_click_time
            is not None
        ):

            elapsed = (
                time.time()
                -
                self.last_click_time
            )

            remaining = (
                actual_interval -
                elapsed
            )

            if remaining > 0:

                self.sleep_interruptible(
                    remaining
                )

        if not self.running:
            return

        adb(
            "shell",
            "input",
            "tap",
            str(x),
            str(y)
        )

        self.last_click_time = (
            time.time()
        )

        # 点击后微小自然停顿
        if self.human_level >= 3:

            self.human_pause(
                0.03,
                0.02,
                0.12
            )

        self.status(
            f"点击 "
            f"({x},{y})"
        )

    # --------------------------------------------------------
    # Swipe
    # --------------------------------------------------------

    def execute_swipe(
        self,
        action
    ):

        start = action.get(
            "from",
            {}
        )

        end = action.get(
            "to",
            {}
        )

        start_norm = start.get(
            "normalized"
        )

        end_norm = end.get(
            "normalized"
        )

        width, height = (
            get_screen_size()
        )

        if start_norm and end_norm:

            x1, y1 = normalize_to_screen(
                start_norm["x"],
                start_norm["y"]
            )

            x2, y2 = normalize_to_screen(
                end_norm["x"],
                end_norm["y"]
            )

        else:

            x1 = int(
                start.get(
                    "x",
                    0
                )
            )

            y1 = int(
                start.get(
                    "y",
                    0
                )
            )

            x2 = int(
                end.get(
                    "x",
                    0
                )
            )

            y2 = int(
                end.get(
                    "y",
                    0
                )
            )

        # ----------------------------------------------------
        # Level 3 滑动坐标微扰
        # ----------------------------------------------------

        if self.human_level >= 3:

            x1, y1 = self.human_coordinate(
                x1,
                y1,
                width,
                height
            )

            x2, y2 = self.human_coordinate(
                x2,
                y2,
                width,
                height
            )

        duration = int(
            action.get(
                "duration_ms",
                500
            )
        )

        duration = max(
            50,
            duration
        )

        # ----------------------------------------------------
        # Level 3：
        # 滑动时间只增加
        # ----------------------------------------------------

        if self.human_level >= 3:

            duration_add = random.randint(
                0,
                max(
                    1,
                    int(
                        duration *
                        0.15
                    )
                )
            )

            duration += (
                duration_add
            )

        adb(
            "shell",
            "input",
            "swipe",
            str(x1),
            str(y1),
            str(x2),
            str(y2),
            str(duration)
        )

        self.status(
            f"滑动 "
            f"({x1},{y1}) -> "
            f"({x2},{y2}) "
            f"{duration}ms"
        )

        if self.human_level >= 3:

            self.human_pause(
                0.04,
                0.02,
                0.15
            )

    # --------------------------------------------------------
    # Worker
    # --------------------------------------------------------

    def worker(self):

        try:

            self.status(
                f"实际循环目标："
                f"{self.target} 次"
            )

            # =================================================
            # 第一板块：只执行一次
            # =================================================

            if not self.execute_process1():

                self.running = False

                self.status(
                    "Process 1 失败，停止"
                )

                return

            # =================================================
            # 第二板块：循环
            # =================================================

            while (
                self.running
                and
                self.completed <
                self.target
            ):

                current = (
                    self.completed + 1
                )

                self.status(
                    f"开始 Process 2："
                    f"{current}/"
                    f"{self.target}"
                )

                success = (
                    self.execute_process2()
                )

                if success:

                    self.completed += 1

                    self.status(
                        f"Process 2 完成："
                        f"{self.completed}/"
                        f"{self.target}"
                    )

                else:

                    self.status(
                        "Process 2 执行失败"
                    )

                    break

                # ------------------------------------------------
                # 循环间隔
                # ------------------------------------------------

                if (
                    self.completed >=
                    self.target
                ):

                    break

                wait_minutes = max(
                    self.pause_minutes,
                    self.min_interval_minutes
                )

                if wait_minutes > 0:

                    # Level 3：
                    # 等待只增加，不减少
                    if self.human_level >= 3:

                        extra = random.uniform(
                            0,
                            min(
                                0.5,
                                wait_minutes *
                                60 *
                                0.05
                            )
                        )

                    else:

                        extra = 0

                    wait_seconds = (
                        wait_minutes *
                        60 +
                        extra
                    )

                    self.status(
                        f"下一轮等待 "
                        f"{wait_seconds / 60:.2f} min"
                    )

                    self.sleep_interruptible(
                        wait_seconds
                    )

            if (
                self.completed >=
                self.target
            ):

                self.status(
                    "达到循环上限，自动停止"
                )

            elif not self.running:

                self.status(
                    "手动停止"
                )

        except Exception as e:

            self.status(
                f"执行异常：{e}"
            )

        finally:

            self.running = False

    # --------------------------------------------------------
    # Interruptible Sleep
    # --------------------------------------------------------

    def sleep_interruptible(
        self,
        seconds
    ):

        end = (
            time.time() +
            seconds
        )

        while (
            self.running
            and
            time.time() <
            end
        ):

            remaining = (
                end -
                time.time()
            )

            time.sleep(
                min(
                    0.25,
                    max(
                        0,
                        remaining
                    )
                )
            )


# ============================================================
# GUI
# ============================================================

class App:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title(
            "Automation Test"
        )

        self.root.geometry(
            "760x760"
        )

        self.root.minsize(
            700,
            700
        )

        self.process1 = None

        self.process2 = None

        self.process1_path = ""

        self.process2_path = ""

        self.recorder = None

        self.keyboard_listener = None

        self.mouse_listener = None

        self.automation = Automation(
            status_callback=
            self.update_status
        )

        self.build_ui()

        self.start_global_listeners()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.update_progress_loop()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        title = tk.Label(
            self.root,
            text="Android Emulator Automation",
            font=(
                "Microsoft YaHei",
                18,
                "bold"
            )
        )

        title.pack(
            pady=(15, 5)
        )

        subtitle = tk.Label(
            self.root,
            text=
            "板块一：单次先行    "
            "→    "
            "板块二：循环执行",
            font=(
                "Microsoft YaHei",
                10
            )
        )

        subtitle.pack(
            pady=(0, 10)
        )

        self.notebook = ttk.Notebook(
            self.root
        )

        self.notebook.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        self.tab_process1 = tk.Frame(
            self.notebook
        )

        self.tab_process2 = tk.Frame(
            self.notebook
        )

        self.tab_run = tk.Frame(
            self.notebook
        )

        self.notebook.add(
            self.tab_process1,
            text="板块一 · 单次先行"
        )

        self.notebook.add(
            self.tab_process2,
            text="板块二 · 循环"
        )

        self.notebook.add(
            self.tab_run,
            text="执行控制"
        )

        self.build_process1_tab()

        self.build_process2_tab()

        self.build_run_tab()

        # ----------------------------------------------------
        # 底部状态
        # ----------------------------------------------------

        bottom = tk.Frame(
            self.root
        )

        bottom.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        self.status_label = tk.Label(
            bottom,
            text="状态：等待中",
            anchor="w"
        )

        self.status_label.pack(
            fill="x"
        )

        self.progress_label = tk.Label(
            bottom,
            text="进度：0 / 0",
            anchor="w"
        )

        self.progress_label.pack(
            fill="x",
            pady=(5, 0)
        )

    # ========================================================
    # Process 1 UI
    # ========================================================

    def build_process1_tab(self):

        frame = self.tab_process1

        tk.Label(
            frame,
            text="板块一：单次先行",
            font=(
                "Microsoft YaHei",
                15,
                "bold"
            )
        ).pack(
            pady=(20, 5)
        )

        tk.Label(
            frame,
            text=
            "通过录制获得打开 App、进入指定页面所需的点击和滑动参数。\n"
            "运行时只执行一次，完成后自动进入板块二。",
            justify="left"
        ).pack(
            pady=(0, 20)
        )

        path_frame = tk.Frame(
            frame
        )

        path_frame.pack(
            fill="x",
            padx=30
        )

        tk.Label(
            path_frame,
            text="JSON："
        ).pack(
            side="left"
        )

        self.p1_entry = tk.Entry(
            path_frame
        )

        self.p1_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10
        )

        tk.Button(
            path_frame,
            text="导入",
            command=self.load_process1
        ).pack(
            side="right"
        )

        button_frame = tk.Frame(
            frame
        )

        button_frame.pack(
            pady=25
        )

        self.p1_record_button = tk.Button(
            button_frame,
            text="开始录制板块一",
            width=22,
            height=2,
            command=self.start_record_process1
        )

        self.p1_record_button.grid(
            row=0,
            column=0,
            padx=10
        )

        tk.Button(
            button_frame,
            text="查看录制信息",
            width=22,
            height=2,
            command=self.show_process1_info
        ).grid(
            row=0,
            column=1,
            padx=10
        )

        info = tk.Label(
            frame,
            text=
            "录制方法：\n"
            "1. 先打开 Emulator\n"
            "2. 将目标 App 放到需要开始录制的位置\n"
            "3. 点击「开始录制板块一」\n"
            "4. 在 Emulator 内进行操作\n"
            "5. 按 Space 结束录制\n"
            "6. 程序自动保存 JSON",
            justify="left",
            anchor="w"
        )

        info.pack(
            fill="x",
            padx=40,
            pady=15
        )

    # ========================================================
    # Process 2 UI
    # ========================================================

    def build_process2_tab(self):

        frame = self.tab_process2

        tk.Label(
            frame,
            text="板块二：循环执行",
            font=(
                "Microsoft YaHei",
                15,
                "bold"
            )
        ).pack(
            pady=(20, 5)
        )

        tk.Label(
            frame,
            text=
            "通过录制获得需要重复执行的动作。\n"
            "板块一完成后自动进入这里，并按照设置循环。",
            justify="left"
        ).pack(
            pady=(0, 20)
        )

        path_frame = tk.Frame(
            frame
        )

        path_frame.pack(
            fill="x",
            padx=30
        )

        tk.Label(
            path_frame,
            text="JSON："
        ).pack(
            side="left"
        )

        self.p2_entry = tk.Entry(
            path_frame
        )

        self.p2_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10
        )

        tk.Button(
            path_frame,
            text="导入",
            command=self.load_process2
        ).pack(
            side="right"
        )

        button_frame = tk.Frame(
            frame
        )

        button_frame.pack(
            pady=25
        )

        self.p2_record_button = tk.Button(
            button_frame,
            text="开始录制板块二",
            width=22,
            height=2,
            command=self.start_record_process2
        )

        self.p2_record_button.grid(
            row=0,
            column=0,
            padx=10
        )

        tk.Button(
            button_frame,
            text="查看录制信息",
            width=22,
            height=2,
            command=self.show_process2_info
        ).grid(
            row=0,
            column=1,
            padx=10
        )

        # ----------------------------------------------------
        # 循环参数
        # ----------------------------------------------------

        settings = tk.LabelFrame(
            frame,
            text="循环参数"
        )

        settings.pack(
            fill="x",
            padx=30,
            pady=10
        )

        self.add_setting(
            settings,
            0,
            "循环次数",
            "100"
        )

        self.add_setting(
            settings,
            1,
            "误差（±）",
            "0"
        )

        self.add_setting(
            settings,
            2,
            "暂停时间（min）",
            "0"
        )

        self.add_setting(
            settings,
            3,
            "最小间隔（min）",
            "0"
        )

        self.count_entry = self.setting_entries[0]

        self.error_entry = self.setting_entries[1]

        self.pause_entry = self.setting_entries[2]

        self.min_interval_entry = (
            self.setting_entries[3]
        )

        human_frame = tk.Frame(
            frame
        )

        human_frame.pack(
            pady=15
        )

        tk.Label(
            human_frame,
            text="拟人化等级："
        ).pack(
            side="left"
        )

        self.level_var = tk.StringVar(
            value="Level 3"
        )

        level_box = ttk.Combobox(
            human_frame,
            textvariable=self.level_var,
            values=[
                "Level 1",
                "Level 2",
                "Level 3"
            ],
            state="readonly",
            width=12
        )

        level_box.pack(
            side="left",
            padx=10
        )

        # 当前需求默认只使用 Level 3
        level_box.current(2)

    # ========================================================
    # Run UI
    # ========================================================

    def build_run_tab(self):

        frame = self.tab_run

        tk.Label(
            frame,
            text="执行控制",
            font=(
                "Microsoft YaHei",
                15,
                "bold"
            )
        ).pack(
            pady=(20, 15)
        )

        flow = tk.Label(
            frame,
            text=
            "板块一\n"
            "↓\n"
            "打开指定 App + 进入指定页面\n"
            "↓\n"
            "板块一完成\n"
            "↓\n"
            "板块二开始循环\n"
            "↓\n"
            "达到随机目标次数\n"
            "↓\n"
            "自动停止",
            font=(
                "Microsoft YaHei",
                11
            ),
            justify="center"
        )

        flow.pack(
            pady=10
        )

        button_frame = tk.Frame(
            frame
        )

        button_frame.pack(
            pady=30
        )

        tk.Button(
            button_frame,
            text="开始整个流程",
            width=20,
            height=3,
            command=self.start
        ).grid(
            row=0,
            column=0,
            padx=15
        )

        tk.Button(
            button_frame,
            text="停止",
            width=20,
            height=3,
            command=self.stop
        ).grid(
            row=0,
            column=1,
            padx=15
        )

        tk.Label(
            frame,
            text=
            "注意：\n"
            "开始后会先执行板块一一次。\n"
            "板块一完成后才会执行板块二。\n"
            "按「停止」可以终止当前流程。",
            justify="left"
        ).pack(
            pady=10
        )

    # ========================================================
    # Settings helper
    # ========================================================

    def add_setting(
        self,
        parent,
        row,
        label,
        default
    ):

        if not hasattr(
            self,
            "setting_entries"
        ):

            self.setting_entries = []

        tk.Label(
            parent,
            text=label,
            width=18,
            anchor="e"
        ).grid(
            row=row,
            column=0,
            padx=10,
            pady=7
        )

        entry = tk.Entry(
            parent,
            width=15
        )

        entry.insert(
            0,
            default
        )

        entry.grid(
            row=row,
            column=1,
            padx=10,
            pady=7
        )

        self.setting_entries.append(
            entry
        )

    # ========================================================
    # Global listeners
    # ========================================================

    def start_global_listeners(self):

        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click
        )

        self.mouse_listener.start()

        self.keyboard_listener = (
            keyboard.Listener(
                on_press=self.on_key_press
            )
        )

        self.keyboard_listener.start()

    def on_mouse_move(
        self,
        x,
        y
    ):

        if self.recorder:

            self.recorder.mouse_move(
                x,
                y
            )

    def on_mouse_click(
        self,
        x,
        y,
        button,
        pressed
    ):

        if not self.recorder:
            return

        if pressed:

            self.recorder.mouse_down(
                x,
                y,
                button
            )

        else:

            self.recorder.mouse_up(
                x,
                y,
                button
            )

    def on_key_press(
        self,
        key
    ):

        try:

            if key == keyboard.Key.space:

                if self.recorder:

                    self.root.after(
                        0,
                        self.stop_recording
                    )

        except Exception:
            pass

    # ========================================================
    # Recorder Process 1
    # ========================================================

    def start_record_process1(self):

        if self.recorder:

            messagebox.showwarning(
                "提示",
                "当前已经有录制正在进行。"
            )

            return

        self.recorder = Recorder(
            "process1",
            finished_callback=
            self.record_finished,
            status_callback=
            self.update_status
        )

        success = self.recorder.start()

        if success:

            self.p1_record_button.config(
                text="录制中... Space 停止"
            )

            self.p2_record_button.config(
                state="disabled"
            )

    # ========================================================
    # Recorder Process 2
    # ========================================================

    def start_record_process2(self):

        if self.recorder:

            messagebox.showwarning(
                "提示",
                "当前已经有录制正在进行。"
            )

            return

        self.recorder = Recorder(
            "process2",
            finished_callback=
            self.record_finished,
            status_callback=
            self.update_status
        )

        success = self.recorder.start()

        if success:

            self.p2_record_button.config(
                text="录制中... Space 停止"
            )

            self.p1_record_button.config(
                state="disabled"
            )

    # ========================================================
    # Stop recorder
    # ========================================================

    def stop_recording(self):

        if self.recorder:

            self.recorder.stop()

    # ========================================================
    # Recorder finished
    # ========================================================

    def record_finished(
        self,
        success,
        data,
        error
    ):

        def process():

            self.p1_record_button.config(
                text="开始录制板块一",
                state="normal"
            )

            self.p2_record_button.config(
                text="开始录制板块二",
                state="normal"
            )

            if not success:

                self.recorder = None

                if error:

                    messagebox.showerror(
                        "录制失败",
                        error
                    )

                return

            if not data:

                self.recorder = None

                return

            process_name = data.get(
                "record_type",
                "process"
            )

            if process_name == "process1":

                default_name = (
                    "process1.json"
                )

            else:

                default_name = (
                    "process2.json"
                )

            path = os.path.join(
                RECORDING_DIR,
                default_name
            )

            # 如果文件已经存在，
            # 自动生成备份名字

            if os.path.exists(path):

                timestamp = time.strftime(
                    "%Y%m%d_%H%M%S"
                )

                path = os.path.join(
                    RECORDING_DIR,
                    f"{process_name}_"
                    f"{timestamp}.json"
                )

            try:

                with open(
                    path,
                    "w",
                    encoding="utf-8"
                ) as f:

                    json.dump(
                        data,
                        f,
                        ensure_ascii=False,
                        indent=2
                    )

                if process_name == "process1":

                    self.process1 = data

                    self.process1_path = path

                    self.p1_entry.delete(
                        0,
                        tk.END
                    )

                    self.p1_entry.insert(
                        0,
                        path
                    )

                    # 读取录制的最低点击间隔
                    self.automation.click_min_interval_s = (
                        data
                        .get(
                            "click",
                            {}
                        )
                        .get(
                            "min_interval_s",
                            0
                        )
                    )

                else:

                    self.process2 = data

                    self.process2_path = path

                    self.p2_entry.delete(
                        0,
                        tk.END
                    )

                    self.p2_entry.insert(
                        0,
                        path
                    )

                count = len(
                    data.get(
                        "actions",
                        []
                    )
                )

                messagebox.showinfo(
                    "录制完成",
                    f"{process_name} 已保存。\n\n"
                    f"文件：\n{path}\n\n"
                    f"动作数量：{count}"
                )

            except Exception as e:

                messagebox.showerror(
                    "保存失败",
                    str(e)
                )

            finally:

                self.recorder = None

        self.root.after(
            0,
            process
        )

    # ========================================================
    # Import Process 1
    # ========================================================

    def load_process1(self):

        path = filedialog.askopenfilename(
            title="选择 Process 1 JSON",
            filetypes=[
                (
                    "JSON 文件",
                    "*.json"
                )
            ]
        )

        if not path:
            return

        try:

            data = load_json(
                path
            )

            self.process1 = data

            self.process1_path = path

            self.p1_entry.delete(
                0,
                tk.END
            )

            self.p1_entry.insert(
                0,
                path
            )

            self.automation.click_min_interval_s = (
                data
                .get(
                    "click",
                    {}
                )
                .get(
                    "min_interval_s",
                    0
                )
            )

            messagebox.showinfo(
                "成功",
                "Process 1 JSON 已加载"
            )

        except Exception as e:

            messagebox.showerror(
                "错误",
                str(e)
            )

    # ========================================================
    # Import Process 2
    # ========================================================

    def load_process2(self):

        path = filedialog.askopenfilename(
            title="选择 Process 2 JSON",
            filetypes=[
                (
                    "JSON 文件",
                    "*.json"
                )
            ]
        )

        if not path:
            return

        try:

            data = load_json(
                path
            )

            self.process2 = data

            self.process2_path = path

            self.p2_entry.delete(
                0,
                tk.END
            )

            self.p2_entry.insert(
                0,
                path
            )

            messagebox.showinfo(
                "成功",
                "Process 2 JSON 已加载"
            )

        except Exception as e:

            messagebox.showerror(
                "错误",
                str(e)
            )

    # ========================================================
    # Show info
    # ========================================================

    def show_process1_info(self):

        self.show_process_info(
            self.process1,
            "Process 1"
        )

    def show_process2_info(self):

        self.show_process_info(
            self.process2,
            "Process 2"
        )

    def show_process_info(
        self,
        data,
        title
    ):

        if not data:

            messagebox.showinfo(
                title,
                "还没有加载 JSON。"
            )

            return

        actions = data.get(
            "actions",
            []
        )

        clicks = sum(
            1
            for x in actions
            if x.get("action") ==
            "click"
        )

        swipes = sum(
            1
            for x in actions
            if x.get("action") ==
            "swipe"
        )

        pages = sum(
            1
            for x in actions
            if x.get("action") ==
            "page_change"
        )

        package = (
            data
            .get(
                "target",
                {}
            )
            .get(
                "package",
                "unknown"
            )
        )

        width = (
            data
            .get(
                "device",
                {}
            )
            .get(
                "screen_width",
                "?"
            )
        )

        height = (
            data
            .get(
                "device",
                {}
            )
            .get(
                "screen_height",
                "?"
            )
        )

        text = (
            f"{title}\n\n"
            f"目标 App：{package}\n"
            f"设备尺寸：{width} x {height}\n\n"
            f"总动作：{len(actions)}\n"
            f"点击：{clicks}\n"
            f"滑动：{swipes}\n"
            f"页面变化：{pages}"
        )

        messagebox.showinfo(
            title,
            text
        )

    # ========================================================
    # Start automation
    # ========================================================

    def start(self):

        if self.automation.running:

            messagebox.showwarning(
                "提示",
                "程序已经在运行。"
            )

            return

        if self.process1 is None:

            messagebox.showerror(
                "错误",
                "请先导入或录制 Process 1。"
            )

            return

        if self.process2 is None:

            messagebox.showerror(
                "错误",
                "请先导入或录制 Process 2。"
            )

            return

        try:

            count = int(
                self.count_entry.get()
            )

            error = int(
                self.error_entry.get()
            )

            pause = float(
                self.pause_entry.get()
            )

            min_interval = float(
                self.min_interval_entry.get()
            )

            if count < 1:

                raise ValueError(
                    "循环次数必须 ≥ 1"
                )

            if error < 0:

                raise ValueError(
                    "误差必须 ≥ 0"
                )

            if error >= count:

                raise ValueError(
                    "误差必须小于循环次数"
                )

            if pause < 0:

                raise ValueError(
                    "暂停时间必须 ≥ 0"
                )

            if min_interval < 0:

                raise ValueError(
                    "最小间隔必须 ≥ 0"
                )

        except Exception as e:

            messagebox.showerror(
                "输入错误",
                str(e)
            )

            return

        if not adb_available():

            messagebox.showerror(
                "ADB 错误",
                "没有找到可用的 ADB。\n\n"
                "请确认 adb 文件夹中包含：\n"
                "adb.exe\n"
                "AdbWinApi.dll\n"
                "AdbWinUsbApi.dll"
            )

            return

        devices = adb_devices()

        ready_devices = [
            x
            for x in devices
            if x[1] == "device"
        ]

        if not ready_devices:

            messagebox.showerror(
                "ADB 错误",
                "没有发现 Android 设备。\n\n"
                "请先启动 Emulator，并确认 ADB 已连接。"
            )

            return

        self.automation.start(
            self.process1,
            self.process2,
            count,
            error,
            pause,
            min_interval
        )

        self.notebook.select(
            self.tab_run
        )

    # ========================================================
    # Stop
    # ========================================================

    def stop(self):

        self.automation.stop()

    # ========================================================
    # Status
    # ========================================================

    def update_status(
        self,
        text
    ):

        self.root.after(
            0,
            self._update_status_ui,
            text
        )

    def _update_status_ui(
        self,
        text
    ):

        self.status_label.config(
            text=
            "状态：" +
            str(text)
        )

        self.progress_label.config(
            text=
            f"进度："
            f"{self.automation.completed} / "
            f"{self.automation.target}"
        )

    # ========================================================
    # Progress refresh
    # ========================================================

    def update_progress_loop(self):

        try:

            self.progress_label.config(
                text=
                f"进度："
                f"{self.automation.completed} / "
                f"{self.automation.target}"
            )

        except Exception:
            pass

        self.root.after(
            500,
            self.update_progress_loop
        )

    # ========================================================
    # Close
    # ========================================================

    def on_close(self):

        if self.recorder:

            self.recorder.recording = False

            self.recorder = None

        if self.automation.running:

            answer = messagebox.askyesno(
                "退出",
                "程序正在执行。\n\n"
                "确定停止并退出吗？"
            )

            if not answer:
                return

            self.automation.stop()

        try:

            if self.mouse_listener:

                self.mouse_listener.stop()

        except Exception:
            pass

        try:

            if self.keyboard_listener:

                self.keyboard_listener.stop()

        except Exception:
            pass

        self.root.destroy()

    # ========================================================
    # Run
    # ========================================================

    def run(self):

        self.root.mainloop()


# ============================================================
# JSON loader
# ============================================================

def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# Main
# ============================================================

def main():

    app = App()

    app.run()


if __name__ == "__main__":

    main()