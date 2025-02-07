import datetime
import os
import platform
import subprocess
import sys
from .ClassWidgets.base import PluginBase, SettingsBase
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer, QTime, QDate
from PyQt5.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMessageBox,
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtGui import QIcon, QFont
from qfluentwidgets import (
    PrimaryPushButton, BodyLabel, PushButton, Dialog
)

file_path = "password.txt"
if not os.path.exists(file_path):
    default_names = '123456'
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(default_names)
else:
    with open(file_path, "r", encoding="utf-8") as f:
        passwords = f.read()

class ScreenKeyboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_uppercase = False
        self.buttons = {}
        self.parent_dialog = parent
        self.initUI()

    def initUI(self):
        self.setWindowTitle("虚拟键盘")
        self.setGeometry(100, 100, 600, 300)
        self.main_layout = QVBoxLayout()
        self.keys = [
            ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "退格"],
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
            ["Caps", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "确定"],
            [",", ".", "/", "Z", "X", "C", "V", "B", "N", "M", "@", "#", "*", "!"]
        ]

        for row in self.keys:
            row_layout = QHBoxLayout()
            for key in row:
                button = PushButton(key if not key.isalpha() else key.lower())
                button.setFixedSize(70, 40)
                button.setFont(QFont("黑体"))
                button.clicked.connect(lambda checked, key=key: self.on_key_press(key))
                row_layout.addWidget(button)
                self.buttons[key] = button
            self.main_layout.addLayout(row_layout)
        self.setLayout(self.main_layout)

    def on_key_press(self, key):
        if hasattr(self, 'parent_dialog') and self.parent_dialog:
            password_input = self.parent_dialog.password_input
            current_text = password_input.text()

            if key == "退格":
                password_input.setText(current_text[:-1])
            elif key == "确定":
                self.parent_dialog.accept()
            elif key == "Caps":
                self.is_uppercase = not self.is_uppercase
                self.update_keyboard_display()
            else:
                current_key = key.upper() if self.is_uppercase and key.isalpha() else key.lower() if key.isalpha() else key
                password_input.setText(current_text + current_key)

    def update_keyboard_display(self):
        for key, button in self.buttons.items():
            if key.isalpha():
                button.setText(key.upper() if self.is_uppercase else key.lower())


class ExitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_screen = parent
        self.setup_window_flags()
        self.initUI()
        self.setFixedSize(1050, 400)

        # 添加焦点定时器
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.force_focus)
        self.focus_timer.start(500)  # 每秒触发两次

    def setup_window_flags(self):
        # 启用窗口装饰并强制置顶
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Window |
            Qt.WindowStaysOnTopHint |  # 强制置顶
            Qt.X11BypassWindowManagerHint  # 绕过 X11 窗口管理器
        )

    def initUI(self):
        self.setWindowTitle("确认退出")
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E2E; /* 深色背景 */
                color: #FFFFFF; /* 白色文字 */
                border: 3px solid #4CAF50; /* 绿色边框 */
                border-radius: 8px; /* 圆角 */
            }
            QLabel {
                font-size: 16px;
                color: #CDD6F4; /* 浅灰色文字 */
            }
            QLineEdit {
                font-size: 16px;
                padding: 8px;
                border: 1px solid #89B4FA; /* 浅蓝色边框 */
                border-radius: 4px;
                background: #313244; /* 深灰色背景 */
                color: #FFFFFF; /* 白色文字 */
            }
            QPushButton {
                background-color: #89B4FA; /* 浅蓝色按钮 */
                color: #1E1E2E; /* 深色文字 */
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74A7F8; /* 悬停时稍深的蓝色 */
            }
            PushButton {
                background-color: #89B4FA; /* 浅蓝色按钮 */
                color: #1E1E2E; /* 深色文字 */
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            PushButton:hover {
                background-color: #74A7F8; /* 悬停时稍深的蓝色 */
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self.label = QLabel("请输入解锁密码：")
        self.label.setFont(QFont("黑体", 16))
        main_layout.addWidget(self.label)

        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        main_layout.addWidget(self.password_input)

        self.keyboard = ScreenKeyboard(self)
        main_layout.addWidget(self.keyboard)

        button_layout = QHBoxLayout()
        self.close_button = QPushButton("取消输入密码，继续锁屏")
        self.close_button.setFont(QFont("黑体"))
        self.close_button.setFixedHeight(40)
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

    def force_focus(self):
        self.activateWindow()
        self.raise_()

    def accept(self):
        with open('password.txt', "r", encoding="utf-8") as f:
            passwords = f.read()
        if self.password_input.text() == str(passwords):
            super().accept()
            self.parent_screen.close()
        else:
            self.label.setText("密码错误，请重新输入：")
            self.label.setFont(QFont("黑体", 16))
            self.password_input.clear()

    def showEvent(self, event):
        self.force_focus()
        super().showEvent(event)

    def enterEvent(self, event):
        self.force_focus()
        super().enterEvent(event)


class LockScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def initUI(self):
        # 绕过 X11 并强制置顶
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 启用窗口装饰
            Qt.WindowStaysOnTopHint |  # 强制置顶
            Qt.X11BypassWindowManagerHint  # 绕过 X11 窗口管理器
        )
        self.setWindowModality(Qt.ApplicationModal)
        screen = QApplication.primaryScreen().size()
        self.setGeometry(0, 0, screen.width(), screen.height())

        # 设置背景颜色和样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E2E; /* 深色背景 */
                color: #FFFFFF; /* 白色文字 */
            }
            BodyLabel {
                font-size: 200px; /* 时间字体大小 */
                font-weight: bold;
                color: #FFFFFF; /* 白色时间 */
            }
            PrimaryPushButton {
                background-color: #89B4FA; /* 浅蓝色按钮 */
                color: #1E1E2E; /* 深色文字 */
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            PrimaryPushButton:hover {
                background-color: #74A7F8; /* 悬停时稍深的蓝色 */
            }
        """)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)  # 增加边距
        layout.setSpacing(20)

        # 添加一个占位符，让时间标签居中
        layout.addStretch(1)

        # 时间显示
        self.time_label = BodyLabel("加载中...")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 200px; color: #FFFFFF;")
        layout.addWidget(self.time_label, alignment=Qt.AlignCenter)

        # 日期显示
        self.date_label = BodyLabel("加载中...")
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("font-size: 100px; color: #CDD6F4;")  # 浅灰色日期
        layout.addWidget(self.date_label, alignment=Qt.AlignCenter)

        # 添加一个占位符，让退出按钮沉底
        layout.addStretch(1)

        # 使用 QHBoxLayout 来放置退出按钮到右下角
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # 推动按钮到右侧
        self.exit_btn = PrimaryPushButton("退出")
        self.exit_btn.setFont(QFont("黑体", 16))
        self.exit_btn.clicked.connect(self.show_exit_dialog)
        self.exit_btn.setFixedSize(150, 50)  # 调整按钮大小
        button_layout.addWidget(self.exit_btn)  # 添加按钮
        layout.addLayout(button_layout)  # 将按钮布局添加到主布局中

    def update_time(self):
        current_datetime = datetime.datetime.now()
        weekday = current_datetime.weekday()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday = weekdays[weekday]
        current_time = QTime.currentTime().toString("HH:mm:ss")
        current_date = QDate.currentDate().toString("yyyy-MM-dd")
        self.time_label.setText(current_time)
        self.time_label.setFont(QFont("黑体"))
        self.date_label.setText(current_date + " " + weekday)
        self.date_label.setFont(QFont("黑体"))

    def show_exit_dialog(self):
        dialog = ExitDialog(self)
        dialog.exec_()

class TrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 检查系统托盘是否可用
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "错误", "系统托盘不可用")
            sys.exit(1)

        self.tray = QSystemTrayIcon()
        # 使用本地 .ico 文件
        self.tray.setIcon(QIcon("./plugins/cw-lock-plugin/lock.ico"))  # 确保 lock.ico 文件存在
        self.tray.activated.connect(self.on_tray_icon_activated)
        self.tray.show()

    def on_tray_icon_activated(self, reason):
        # 仅在左键点击时弹出确认对话框
        if reason == QSystemTrayIcon.Trigger:
            msg = Dialog('确认锁屏', '确定要锁定屏幕吗？解锁需要密码')
            if msg.exec():
                lock_screen = LockScreen()
                lock_screen.exec_()

    def run(self):
        sys.exit(self.app.exec_())

class Plugin(PluginBase):
    def __init__(self, cw_contexts, method):
        super().__init__(cw_contexts, method)
        self.floating_window = None

    def execute(self):
        """启动插件主功能"""
        app = TrayApp()
        app.run()


class Settings(SettingsBase):
    def __init__(self, plugin_path, parent=None):
        super().__init__(plugin_path, parent)
        uic.loadUi(os.path.join(self.PATH, "settings.ui"), self)
        open_names_list = self.findChild(PrimaryPushButton, "open_names_list")
        open_names_list.clicked.connect(self.open_names_file)

    def open_names_file(self):
        """打开名单文件进行编辑"""
        file_path = os.path.join(self.PATH, "password.txt")
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Linux":
            subprocess.call(["xdg-open", file_path])
        elif platform.system() == "Darwin":
            subprocess.call(["open", file_path])


if __name__ == '__main__':
    app = TrayApp()
    app.run()