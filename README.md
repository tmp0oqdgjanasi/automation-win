# AutomationTest
Android Emulator 自动化录制与执行工具。
本项目用于通过 ADB 操作 Android Emulator，并提供两个独立的自动化流程：
- **板块一：Process 1**
  - 单次执行
  - 用于启动指定 App
  - 进入指定页面
  - 执行预先录制的操作
- **板块二：Process 2**
  - 循环执行
  - 在 Process 1 完成后开始
  - 根据设置的循环次数执行
  - 支持次数误差 ±
程序支持鼠标录制，并将录制结果保存为 JSON。
---
## 一、项目结构
当前项目目录：
```text
AutomationTest/
│
├─ automation_test.py
├─ build.bat
├─ README.md
│
├─ adb/
│   ├─ adb.exe
│   ├─ AdbWinApi.dll
│   ├─ AdbWinUsbApi.dll
│   ├─ fastboot.exe
│   └─ 其他 Android Platform-Tools 文件
│
└─ recordings/

文件说明

文件 / 文件夹	作用
automation_test.py	主程序
build.bat	用于生成 EXE
README.md	项目说明
adb/	内置 Android Platform-Tools
recordings/	保存录制出来的 JSON
process1.json	Process 1 录制数据
process2.json	Process 2 录制数据

第一次创建项目时：

recordings/

可以为空。

不需要提前创建：

dist/
build/
process1.json
process2.json

这些会在程序运行或打包时自动产生。

⸻

二、运行原理

整个程序分成两个阶段。

                    启动程序
                       │
                       ▼
              ┌─────────────────┐
              │   Process 1     │
              │     板块一       │
              └────────┬────────┘
                       │
                       │ 单次执行
                       ▼
              启动指定 Android App
                       │
                       ▼
              进入指定页面
                       │
                       ▼
              执行录制的操作
                       │
                       ▼
                 Process 1 完成
                       │
                       ▼
              ┌─────────────────┐
              │   Process 2     │
              │     板块二       │
              └────────┬────────┘
                       │
                       │ 循环执行
                       ▼
                执行录制动作
                       │
                       ▼
                  完成一次
                       │
                       ▼
                判断循环次数
                       │
                 ┌─────┴─────┐
                 │           │
              未达到        已达到
                 │           │
                 ▼           ▼
              下一轮       自动停止

⸻

三、Process 1 板块一

Process 1 是整个自动化任务的第一阶段。

它只执行一次。

主要用途：

启动 App
   ↓
进入指定页面
   ↓
执行初始化操作
   ↓
等待页面稳定
   ↓
完成

例如：

打开游戏
   ↓
等待游戏启动
   ↓
点击登录
   ↓
点击进入游戏
   ↓
点击指定按钮
   ↓
进入目标页面
   ↓
Process 1 完成

Process 1 完成以后不会重复执行。

⸻

四、Process 2 板块二

Process 2 是循环阶段。

Process 1 完成以后：

Process 2
   ↓
执行一次
   ↓
完成次数 +1
   ↓
等待
   ↓
执行下一次

例如设置：

循环次数：100
误差：5

程序会随机生成：

95 ~ 105

之间的实际目标次数。

例如本次随机得到：

实际目标：102 次

那么程序执行：

Process 1：1 次
Process 2：
1 / 102
2 / 102
3 / 102
...
102 / 102
自动停止

⸻

五、录制功能

程序支持通过鼠标录制 Android Emulator 内的操作。

可以记录：

* 鼠标点击
* 点击时间
* 点击间隔
* 鼠标按住时间
* 鼠标滑动
* 滑动起点
* 滑动终点
* 滑动持续时间
* 鼠标滑动轨迹
* Android 坐标
* 归一化坐标
* 当前前台 App
* 页面变化信息

⸻

六、录制 Process 1

启动程序以后：

Process 1

选择录制。

程序会寻找：

Android Emulator

窗口。

找到以后记录 Emulator 内容区域。

然后在 Emulator 中进行操作。

例如：

点击
滑动
点击
等待
点击

录制完成以后保存：

recordings/process1.json

⸻

七、录制 Process 2

Process 2 的录制方式与 Process 1 类似。

录制完成以后保存：

recordings/process2.json

最终：

recordings/
├─ process1.json
└─ process2.json

⸻

八、JSON 数据

Process 1 和 Process 2 使用 JSON 保存录制数据。

基本结构：

{
  "schema": "android_emulator_process",
  "version": 2,
  "recorded_at": 0,
  "device": {
    "screen_width": 1080,
    "screen_height": 1920
  },
  "target": {
    "package": "com.example.app"
  },
  "click": {
    "min_interval_s": 0
  },
  "actions": []
}

⸻

九、坐标系统

程序优先保存归一化坐标。

例如：

"normalized": {
    "x": 0.5,
    "y": 0.5
}

表示：

X = 屏幕宽度 × 0.5
Y = 屏幕高度 × 0.5

例如设备：

1080 × 1920

则：

X = 540
Y = 960

这样可以降低不同分辨率之间的坐标偏差。

⸻

十、ADB

项目内置 Android Platform-Tools。

目录：

adb/

其中至少应该包含：

adb/
├─ adb.exe
├─ AdbWinApi.dll
├─ AdbWinUsbApi.dll
└─ 其他 Platform-Tools 文件

建议直接使用 Google 官方完整的 Windows Platform-Tools。

不要只复制：

adb.exe

建议保留整个 Platform-Tools 目录。

官方：

https://developer.android.com/tools/releases/platform-tools

⸻

十一、ADB 自动寻找

程序优先寻找项目目录中的：

.\adb\adb.exe

因此不需要用户配置：

PATH

也不需要单独安装 ADB。

程序结构：

AutomationTest.exe
        │
        ▼
.\adb\adb.exe
        │
        ▼
Android Emulator

⸻

十二、ADB 连接

启动自动化之前，需要确保：

Android Emulator

已经启动，并且 ADB 可以正常连接。

可以在命令行测试：

adb devices

正常情况下类似：

List of devices attached
emulator-5554    device

如果显示：

unauthorized

需要处理 Android 调试授权。

如果没有设备：

List of devices attached

下面为空，则程序无法执行 Android 操作。

⸻

十三、Level 3 拟人化

程序支持 Level 3 拟人化执行。

拟人化是在实际执行阶段进行。

录制文件保存的是原始操作参数。

执行时再进行轻微扰动。

结构：

原始录制
   ↓
JSON
   ↓
Level 3 执行层
   ↓
轻微随机扰动
   ↓
ADB
   ↓
Android Emulator

⸻

点击拟人化

原始点击间隔不会被缩短。

执行时可以加入非负随机等待。

概念：

实际等待时间 =
原始间隔
+
随机增加时间

例如原始：

2.00 秒

实际可能：

2.08 秒
2.17 秒
2.03 秒
2.21 秒

不会主动缩短原始间隔。

⸻

滑动拟人化

滑动持续时间也可以进行轻微随机变化。

例如：

原始：500 ms

可能执行：

520 ms
548 ms
503 ms

而不是每一次完全固定。

⸻

等待时间

Process 2 每轮之间可以设置：

暂停时间（min）

以及：

最小间隔（min）

实际等待时间取两者中较大的值。

例如：

暂停时间 = 1 min
最小间隔 = 3 min

实际：

等待 3 min

⸻

十四、循环次数 ± 误差

GUI 中：

循环次数

例如：

100

以及：

误差（±）

例如：

5

则目标范围：

95 ~ 105

程序启动时随机选择一个目标值。

例如：

102

整个任务就执行：

Process 1
    ↓
Process 2 × 102

达到目标以后自动停止。

⸻

十五、停止功能

程序提供：

开始
停止

点击：

停止

以后：

* 停止当前循环
* 停止下一轮执行
* 停止等待
* 自动结束后台线程

等待时间不是一次性阻塞，因此可以及时停止。

⸻

十六、GUI

主界面包含：

Process 1 JSON
[选择文件]
Process 2 JSON
[选择文件]
循环次数
[100]
误差（±）
[0]
暂停时间（min）
[0]
最小间隔（min）
[0]
[开始]    [停止]
状态：等待中
进度：0 / 0

⸻

十七、生成 EXE

开发环境需要 Python。

安装依赖：

pip install pyinstaller

项目还需要：

pywin32
Pillow
pynput

可以安装：

pip install pywin32 pillow pynput pyinstaller

⸻

十八、打包

运行：

build.bat

PyInstaller 会自动创建：

build/
dist/

这些目录不需要提前创建。

⸻

十九、最终 EXE

最终建议输出结构：

dist/
└─ AutomationTest/
    │
    ├─ AutomationTest.exe
    │
    ├─ adb/
    │   ├─ adb.exe
    │   ├─ AdbWinApi.dll
    │   ├─ AdbWinUsbApi.dll
    │   └─ 其他 Platform-Tools 文件
    │
    └─ recordings/
        ├─ process1.json
        └─ process2.json

把整个：

dist/AutomationTest/

复制到另一台 Windows 电脑即可使用。

⸻

二十、目标电脑

最终 EXE 使用时：

不需要安装 Python

也不需要：

不需要安装 PyInstaller
不需要配置 Python
不需要安装 ADB
不需要配置 ADB PATH

但 Android Emulator 本身需要已经存在并运行。

⸻

二十一、第一次使用

推荐流程：

1. 启动 Android Emulator
2. 启动 AutomationTest.exe
3. 检查 ADB 连接
4. 录制 Process 1
5. 保存 process1.json
6. 录制 Process 2
7. 保存 process2.json
8. 导入两个 JSON
9. 设置循环次数
10. 设置误差
11. 设置暂停时间
12. 设置最小间隔
13. 点击开始
14. Process 1 执行一次
15. Process 2 开始循环
16. 达到目标次数后自动停止

⸻

二十二、注意事项

1. Emulator 必须已经启动

程序不能代替 Emulator 本身。

需要先启动 Android Emulator。

⸻

2. 录制时窗口不要随意移动

录制过程中最好保持 Emulator 窗口位置和比例稳定。

⸻

3. 不要修改 JSON

除非你明确知道 JSON 字段的作用，否则建议直接使用程序录制生成的 JSON。

⸻

4. 不要删除 adb 文件

最终 EXE 所在目录必须保留：

adb/

否则程序可能无法执行 Android 操作。

⸻

5. recordings 可以重新录制

如果需要重新录制，可以删除：

recordings/process1.json
recordings/process2.json

然后重新录制。

⸻

二十三、推荐最终目录

开发阶段：

AutomationTest/
│
├─ automation_test.py
├─ build.bat
├─ README.md
│
├─ adb/
│   ├─ adb.exe
│   ├─ AdbWinApi.dll
│   ├─ AdbWinUsbApi.dll
│   └─ ...
│
└─ recordings/

打包以后：

AutomationTest/
│
└─ dist/
    │
    └─ AutomationTest/
        │
        ├─ AutomationTest.exe
        │
        ├─ adb/
        │   ├─ adb.exe
        │   ├─ AdbWinApi.dll
        │   ├─ AdbWinUsbApi.dll
        │   └─ ...
        │
        └─ recordings/
            ├─ process1.json
            └─ process2.json

⸻

二十四、核心逻辑总结

本项目最终逻辑：

                 AutomationTest
                       │
              ┌────────┴────────┐
              │                 │
           录制系统           执行系统
              │                 │
       ┌──────┴──────┐          │
       │             │          │
   Process 1     Process 2      │
       │             │          │
     单次          循环          │
       │             │          │
       └──────┬──────┘          │
              │                 │
              ▼                 ▼
           JSON 参数      Level 3 执行层
                                │
                                ▼
                               ADB
                                │
                                ▼
                         Android Emulator

⸻

二十五、免责声明

本工具主要用于自动化测试、重复性操作和 Android Emulator 流程测试。

请确保自动化行为符合所使用软件、平台以及服务的规则。

请勿将自动化功能用于绕过安全验证、反作弊机制、访问控制或其他平台限制。
