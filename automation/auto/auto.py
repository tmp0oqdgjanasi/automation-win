import json
import random
import threading
import time
import tkinter as tk
from tkinter import messagebox

import pyautogui


class AutoRunner:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "JSON Auto Runner"
        )

        self.root.geometry(
            "780x700"
        )

        self.running = False

        # =========================
        # JSON1
        # =========================

        tk.Label(
            root,
            text="JSON1：单次执行"
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 4)
        )

        self.json1_text = tk.Text(
            root,
            height=11
        )

        self.json1_text.pack(
            fill="x",
            padx=12
        )

        # =========================
        # JSON2
        # =========================

        tk.Label(
            root,
            text="JSON2：循环执行"
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 4)
        )

        self.json2_text = tk.Text(
            root,
            height=11
        )

        self.json2_text.pack(
            fill="x",
            padx=12
        )

        # =========================
        # 控制区域
        # =========================

        control = tk.Frame(root)

        control.pack(
            fill="x",
            padx=12,
            pady=12
        )

        tk.Label(
            control,
            text="循环次数："
        ).pack(side="left")

        self.count_entry = tk.Entry(
            control,
            width=12
        )

        self.count_entry.insert(
            0,
            "1"
        )

        self.count_entry.pack(
            side="left",
            padx=5
        )

        self.start_button = tk.Button(
            control,
            text="开始执行",
            width=12,
            command=self.start
        )

        self.start_button.pack(
            side="left",
            padx=8
        )

        self.stop_button = tk.Button(
            control,
            text="停止",
            width=12,
            command=self.stop
        )

        self.stop_button.pack(
            side="left"
        )

        # =========================
        # 状态
        # =========================

        self.status = tk.Label(
            root,
            text="状态：就绪",
            fg="gray"
        )

        self.status.pack(
            anchor="w",
            padx=12
        )

        # =========================
        # 日志
        # =========================

        tk.Label(
            root,
            text="执行日志："
        ).pack(
            anchor="w",
            padx=12,
            pady=(10, 2)
        )

        self.log = tk.Text(
            root,
            height=13
        )

        self.log.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12)
        )

    # ======================================
    # 日志
    # ======================================

    def write_log(self, message):

        def update():

            self.log.insert(
                tk.END,
                message + "\n"
            )

            self.log.see(
                tk.END
            )

        self.root.after(
            0,
            update
        )

    # ======================================
    # 开始
    # ======================================

    def start(self):

        if self.running:
            return

        try:

            json1 = json.loads(
                self.json1_text.get(
                    "1.0",
                    tk.END
                )
            )

            json2 = json.loads(
                self.json2_text.get(
                    "1.0",
                    tk.END
                )
            )

            count = int(
                self.count_entry.get()
            )

            if count < 1:
                raise ValueError(
                    "循环次数必须大于等于 1"
                )

        except Exception as e:

            messagebox.showerror(
                "输入错误",
                str(e)
            )

            return

        self.running = True

        self.start_button.config(
            state="disabled"
        )

        thread = threading.Thread(
            target=self.run_all,
            args=(
                json1,
                json2,
                count
            ),
            daemon=True
        )

        thread.start()

    # ======================================
    # 停止
    # ======================================

    def stop(self):

        if not self.running:
            return

        self.running = False

        self.status.config(
            text="状态：正在停止……",
            fg="orange"
        )

        self.write_log(
            "收到停止请求。"
        )

    # ======================================
    # 主执行流程
    # ======================================

    def run_all(
        self,
        json1,
        json2,
        count
    ):

        try:

            self.set_status(
                "执行 JSON1……",
                "blue"
            )

            self.write_log(
                "================================"
            )

            self.write_log(
                "开始执行 JSON1"
            )

            success = self.execute_json(
                json1,
                "JSON1"
            )

            if not success:

                self.write_log(
                    "JSON1 未完成。"
                )

                return

            self.write_log(
                "JSON1 执行完成。"
            )

            # =========================
            # JSON2 循环
            # =========================

            for i in range(
                1,
                count + 1
            ):

                if not self.running:
                    break

                self.set_status(
                    f"执行 JSON2：{i}/{count}",
                    "blue"
                )

                self.write_log(
                    "--------------------------------"
                )

                self.write_log(
                    f"开始 JSON2 第 {i}/{count} 次"
                )

                success = self.execute_json(
                    json2,
                    f"JSON2 第 {i} 次"
                )

                if not success:

                    self.write_log(
                        f"JSON2 第 {i} 次没有完整执行。"
                    )

                    self.set_status(
                        "执行失败",
                        "red"
                    )

                    return

                self.write_log(
                    f"JSON2 第 {i} 次完整执行成功。"
                )

            if self.running:

                self.set_status(
                    "全部完成",
                    "green"
                )

                self.write_log(
                    "================================"
                )

                self.write_log(
                    "全部任务完成。"
                )

            else:

                self.set_status(
                    "已停止",
                    "orange"
                )

                self.write_log(
                    "任务已停止。"
                )

        except Exception as e:

            self.set_status(
                "执行异常",
                "red"
            )

            self.write_log(
                "错误：" + str(e)
            )

        finally:

            self.running = False

            self.root.after(
                0,
                lambda: self.start_button.config(
                    state="normal"
                )
            )

    # ======================================
    # JSON 执行
    # ======================================

    def execute_json(
        self,
        data,
        name
    ):

        events = data.get(
            "events",
            []
        )

        if not isinstance(
            events,
            list
        ):

            raise ValueError(
                f"{name} 的 events 必须是数组"
            )

        if len(events) == 0:

            raise ValueError(
                f"{name} 没有任何事件"
            )

        total = len(events)

        for index, event in enumerate(
            events,
            start=1
        ):

            if not self.running:
                return False

            event_type = event.get(
                "type"
            )

            if event_type != "click":
                continue

            # =========================
            # 原始等待时间
            # =========================

            delay = float(
                event.get(
                    "delay",
                    0
                )
            )

            # 测试用的轻微随机等待。
            # 不改变事件顺序。
            random_delay = random.uniform(
                -0.08,
                0.12
            )

            delay = max(
                0,
                delay + random_delay
            )

            time.sleep(
                delay
            )

            # =========================
            # 坐标
            # =========================

            x = int(
                event["x"]
            )

            y = int(
                event["y"]
            )

            # =========================
            # 鼠标移动
            # =========================

            move_duration = random.uniform(
                0.05,
                0.18
            )

            pyautogui.moveTo(
                x,
                y,
                duration=move_duration
            )

            # =========================
            # 点击
            # =========================

            button = event.get(
                "button",
                "left"
            )

            if button not in (
                "left",
                "right",
                "middle"
            ):

                button = "left"

            pyautogui.click(
                x=x,
                y=y,
                button=button
            )

            self.write_log(
                f"{name}："
                f"{index}/{total} "
                f"点击 ({x}, {y})"
            )

        return True

    # ======================================
    # 更新状态
    # ======================================

    def set_status(
        self,
        text,
        color
    ):

        self.root.after(
            0,
            lambda: self.status.config(
                text="状态：" + text,
                fg=color
            )
        )


def main():

    root = tk.Tk()

    app = AutoRunner(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()