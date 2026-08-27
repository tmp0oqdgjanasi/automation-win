import json
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from pynput import mouse
import pygetwindow as gw


class Recorder:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Recorder")
        self.root.geometry("560x430")

        self.events = []
        self.recording = False
        self.last_time = 0
        self.listener = None

        self.mode = tk.StringVar(value="json1")

        tk.Label(
            root,
            text="JSON 鼠标录制器",
            font=("Arial", 16, "bold")
        ).pack(pady=12)

        tk.Label(root, text="录制类型：").pack()

        tk.OptionMenu(
            root,
            self.mode,
            "json1",
            "json2"
        ).pack(pady=5)

        self.info = tk.Label(
            root,
            text="当前未录制",
            fg="gray"
        )
        self.info.pack(pady=10)

        button_frame = tk.Frame(root)
        button_frame.pack()

        tk.Button(
            button_frame,
            text="开始录制",
            width=12,
            command=self.start
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="停止录制",
            width=12,
            command=self.stop
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="导出 JSON",
            width=12,
            command=self.export
        ).pack(side="left", padx=5)

        self.text = tk.Text(
            root,
            height=14,
            width=68
        )
        self.text.pack(
            padx=12,
            pady=15,
            fill="both",
            expand=True
        )

    def start(self):
        self.events = []
        self.last_time = time.monotonic()
        self.recording = True

        self.info.config(
            text="录制中……请点击目标软件",
            fg="red"
        )

        self.listener = mouse.Listener(
            on_click=self.on_click
        )

        self.listener.start()

        self.refresh()

    def on_click(
        self,
        x,
        y,
        button,
        pressed
    ):
        if not self.recording:
            return

        if not pressed:
            return

        now = time.monotonic()

        delay = now - self.last_time

        self.last_time = now

        button_name = str(button).split(".")[-1]

        event = {
            "type": "click",
            "x": int(x),
            "y": int(y),
            "button": button_name,
            "delay": round(delay, 4)
        }

        self.events.append(event)

        self.root.after(
            0,
            self.refresh
        )

    def refresh(self):
        data = {
            "version": 1,
            "mode": self.mode.get(),
            "events": self.events
        }

        self.text.delete(
            "1.0",
            tk.END
        )

        self.text.insert(
            tk.END,
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            )
        )

    def stop(self):
        self.recording = False

        if self.listener:
            self.listener.stop()
            self.listener = None

        self.info.config(
            text=f"录制结束，共 {len(self.events)} 次点击",
            fg="green"
        )

        self.refresh()

    def get_active_window(self):
        try:
            window = gw.getActiveWindow()

            if window:
                return {
                    "title": window.title,
                    "left": window.left,
                    "top": window.top,
                    "width": window.width,
                    "height": window.height
                }

        except Exception:
            pass

        return None

    def export(self):
        if self.recording:
            self.stop()

        if not self.events:
            messagebox.showwarning(
                "提示",
                "没有录制到任何鼠标点击。"
            )
            return

        data = {
            "version": 1,
            "mode": self.mode.get(),
            "window": self.get_active_window(),
            "events": self.events
        }

        if self.mode.get() == "json1":
            filename = "json1.json"
        else:
            filename = "json2.json"

        path = filedialog.asksaveasfilename(
            title="保存 JSON",
            defaultextension=".json",
            initialfile=filename,
            filetypes=[
                ("JSON 文件", "*.json"),
                ("所有文件", "*.*")
            ]
        )

        if not path:
            return

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

            messagebox.showinfo(
                "保存成功",
                f"JSON 已保存：\n{path}"
            )

        except Exception as e:
            messagebox.showerror(
                "保存失败",
                str(e)
            )


def main():
    root = tk.Tk()

    Recorder(root)

    root.mainloop()


if __name__ == "__main__":
    main()
