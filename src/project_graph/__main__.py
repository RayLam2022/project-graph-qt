import os
import subprocess
import sys
import threading
import tkinter as tk
import traceback
from pathlib import Path
from types import TracebackType

from dotenv import load_dotenv
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from project_graph import INFO
from project_graph.log_utils import log, log_dur, logs
from project_graph.ui.loading_window.loading_window import LoadingWindow

log_dur("开始导入资源文件")

# 导入资源文件
try:
    import project_graph.assets.assets  # type: ignore  # noqa: F401
except ImportError:
    from PyQt5 import pyrcc_main

    if not pyrcc_main.processResourceFile(
        [(Path(__file__).parent / "assets" / "image.rcc").as_posix()],
        (Path(__file__).parent / "assets" / "assets.py").as_posix(),
        False,
    ):
        log("Failed to compile assets.rcc")
        exit(1)

    import project_graph.assets.assets  # type: ignore  # noqa: F401


def my_except_hook(
    exctype: type[BaseException], value: BaseException, tb: TracebackType
) -> None:
    if exctype is KeyboardInterrupt:
        sys.exit(0)

    log("error!!!")
    log("\n".join(traceback.format_exception(exctype, value, tb)))
    log(logs)
    # 用tkinter弹出错误信息，用输入框组件显示错误信息
    import tkinter as tk

    root = tk.Tk()
    root.title("error!")
    tk.Label(root, text="出现异常！").pack()
    t = tk.Text(root, height=50, width=150)
    t.config(fg="white", bg="black", font=("TkDefaultFont", 8))
    for line in logs:
        t.insert(tk.END, line + "\n")
    t.pack()
    tk.Button(root, text="确定", command=root.destroy).pack()
    tk.Button(root, text="退出", command=sys.exit).pack()
    root.mainloop()


loading_window_instance = None  # 用于保存加载窗口实例


def show_loading_window():
    global loading_window_instance
    root = tk.Tk()
    loading_window_instance = LoadingWindow(root)
    root.mainloop()


def main():
    sys.excepthook = my_except_hook

    # 开始加载Loading窗口
    loading_thread = threading.Thread(target=show_loading_window)
    loading_thread.start()

    log_dur("开始初始化项目")

    load_dotenv()
    os.environ["ARK_API_KEY"] = os.getenv("ARK_API_KEY", "")
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
    os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE", "")
    if INFO.env == "dev":
        INFO.commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        )
        INFO.date = (
            subprocess.check_output(["git", "log", "-1", "--format=%cd"])
            .decode()
            .strip()
        )
        INFO.branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode()
            .strip()
        )

    log_dur("开始初始化app")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./assets/favicon.ico"))

    # 只在这里导入主窗口，防止最开始导入，一些东西没初始化好
    from project_graph.ui.main_window.main_window import Canvas

    log_dur("开始显示窗口 Canvas")

    canvas = Canvas()
    canvas.show()

    log_dur("显示窗口 Canvas 结束")

    # 关闭Loading窗口
    if loading_window_instance is not None:
        loading_window_instance.master.quit()  # 关闭Tkinter窗口
        loading_thread.join()  # 等待加载线程结束

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
