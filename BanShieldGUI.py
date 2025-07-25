import sys
import os
import subprocess
import time
import threading
import platform
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLineEdit, QTextEdit, QPushButton, QLabel,
                             QMessageBox, QCheckBox, QSizePolicy, QSlider)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QIcon
from dotenv import load_dotenv

class BanCheckerThread(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.process = None
        self.running = False
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

    def read_output(self, stream, stream_type):
        while self.running and self.process:
            line = stream.readline()
            if line:
                timestamp = time.strftime('%H:%M:%S')
                if stream_type == "stdout":
                    self.log_signal.emit(f"[{timestamp}] [{stream_type.upper()}] {line.strip()}")
                    if "NO BAN" in line:
                        self.status_signal.emit("No Ban", "#6699cc")
                    elif "BAN DETECTED" in line:
                        self.status_signal.emit("Ban Detected!", "#cc3333")
                        QApplication.instance().beep()
                else:
                    if "DeprecationWarning" not in line and "trace-deprecation" not in line:
                        self.log_signal.emit(f"[{timestamp}] [ERROR] {line.strip()}")
                        self.status_signal.emit("Error", "#cc3333")

    def run(self):
        self.running = True
        try:
            python_cmd = "python3" if platform.system() in ["Darwin", "Linux"] else "python"
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] [INFO] Starting BanChecker.py with {python_cmd} in {self.script_dir}...")

            self.process = subprocess.Popen(
                [python_cmd, os.path.join(self.script_dir, "BanChecker.py")],
                cwd=self.script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace",
                env=os.environ.copy()
            )

            stdout_thread = threading.Thread(target=self.read_output, args=(self.process.stdout, "stdout"))
            stderr_thread = threading.Thread(target=self.read_output, args=(self.process.stderr, "stderr"))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            stdout_thread.join()
            stderr_thread.join()

            while self.running:
                if self.process.poll() is not None:
                    self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] [INFO] BanChecker.py process finished with return code {self.process.returncode}")
                    self.finished_signal.emit()
                    break

        except Exception as e:
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] [ERROR] {str(e)}")
            self.status_signal.emit("Error", "#cc3333")
            self.finished_signal.emit()

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] [INFO] BanChecker.py process terminated.")
            self.finished_signal.emit()

class BanShieldGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BanShield V2")
        self.setGeometry(100, 100, 900, 600)
        self.setWindowIcon(QIcon("icon.ico"))
        self.setStyleSheet("""
            QMainWindow { background: #23272A; }
            QLabel { color: #D8D8D8; font-size: 13px; font-family: 'Tahoma', 'Arial', sans-serif; }
            QLineEdit, QTextEdit {
                background: #1c1e22;
                color: #F8F8F2;
                border: 1px solid #4B5C6E;
                border-radius: 2px;
                font-size: 13px;
                font-family: 'Tahoma', 'Arial', sans-serif;
                padding: 4px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5a6a7a, stop:1 #23272A);
                color: #F2F2F2;
                border: 1px solid #324357;
                border-radius: 3px;
                font-size: 14px;
                padding: 6px 12px;
                font-family: 'Tahoma', 'Arial', sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6C7B8A, stop:1 #23272A);
                border: 1px solid #6699cc;
            }
            QPushButton:disabled {
                background: #3d4248;
                color: #999999;
                border: 1px solid #32373C;
            }
            QCheckBox { color: #D8D8D8; font-size: 13px; }
            QSlider::groove:horizontal { background: #323b45; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal {
                background: #86a1c6;
                border: 1px solid #334d66;
                width: 18px; height: 18px;
                border-radius: 9px;
                margin: -7px 0;
            }
            #settingsPanel {
                background: #20232A;
                border-right: 2px solid #39495C;
            }
            #toggleButton {
                background: #374a5e;
                color: #E8E8E8;
                padding: 6px;
                border-radius: 2px;
                font-size: 20px;
                qproperty-text: "☰";
                border: 1px solid #495D72;
            }
            #toggleButton:hover { background: #495D72; }
            #madeByLabel { color: #7F8FA6; font-size: 11px; font-family: 'Tahoma', 'Arial', sans-serif; }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_widget.setLayout(main_layout)

        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.clicked.connect(self.toggle_settings)
        main_layout.addWidget(self.toggle_button)

        self.settings_panel = QWidget()
        self.settings_panel.setObjectName("settingsPanel")
        self.settings_panel.setFixedWidth(0)  # PANEL BAŞLANGIÇTA KAPALI!
        settings_layout = QFormLayout()
        self.settings_panel.setLayout(settings_layout)

        self.env_fields = {
            "ProfileToWatch": QLineEdit(),
            "WatchingProfileUsername": QLineEdit(),
            "WatchingProfilePassword": QLineEdit(),
            "WatchingProfileSharedSecret": QLineEdit(),
            "WatchingProfileIdentitySecret": QLineEdit(),
            "BankAccountTradeURL": QLineEdit(),
            "BankAccountUsername": QLineEdit(),
            "BankAccountPassword": QLineEdit(),
            "BankAccountSharedSecret": QLineEdit(),
            "AutoAccept": QCheckBox(),
            "TELEGRAM_BOT_TOKEN": QLineEdit(),
            "TELEGRAM_CHAT_ID": QLineEdit(),
            "TelegramNotify": QCheckBox()
        }
        self.env_fields["WatchingProfilePassword"].setEchoMode(QLineEdit.Password)
        self.env_fields["BankAccountPassword"].setEchoMode(QLineEdit.Password)
        self.env_fields["WatchingProfileSharedSecret"].setEchoMode(QLineEdit.Password)
        self.env_fields["WatchingProfileIdentitySecret"].setEchoMode(QLineEdit.Password)
        self.env_fields["BankAccountSharedSecret"].setEchoMode(QLineEdit.Password)
        self.env_fields["TELEGRAM_BOT_TOKEN"].setEchoMode(QLineEdit.Password)

        for key, widget in self.env_fields.items():
            if key == "TELEGRAM_BOT_TOKEN":
                label = "Telegram Bot Token"
            elif key == "TELEGRAM_CHAT_ID":
                label = "Telegram Chat ID"
            elif key == "TelegramNotify":
                label = "Mobile/Telegram Alarm"
            else:
                label = key.replace("ProfileToWatch", "Profile URL").replace("AutoAccept", "Auto Accept")
            settings_layout.addRow(label + ":", widget)

        from functools import partial
        self.inventory_type_checkboxes = {
            "cs2": QCheckBox("CS2 Items"),
            "tf2": QCheckBox("TF2 Items"),
            "dota2": QCheckBox("Dota 2 Items"),
            "all": QCheckBox("All Inventory")
        }
        for cb in self.inventory_type_checkboxes.values():
            cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            cb.setMinimumHeight(22)

        inventory_type_widget = QWidget()
        inventory_type_vbox = QVBoxLayout()
        inventory_type_vbox.setContentsMargins(0, 0, 0, 0)
        inventory_type_vbox.setSpacing(10)
        for cb in self.inventory_type_checkboxes.values():
            inventory_type_vbox.addWidget(cb)
        inventory_type_widget.setLayout(inventory_type_vbox)
        settings_layout.addRow("Inventory to Send:", inventory_type_widget)

        def inventory_type_changed(changed_key):
            if self.inventory_type_checkboxes["all"].isChecked():
                for k in ["cs2", "tf2", "dota2"]:
                    self.inventory_type_checkboxes[k].setChecked(False)
                    self.inventory_type_checkboxes[k].setEnabled(False)
            else:
                for k in ["cs2", "tf2", "dota2"]:
                    self.inventory_type_checkboxes[k].setEnabled(True)

        for k, cb in self.inventory_type_checkboxes.items():
            cb.stateChanged.connect(partial(inventory_type_changed, k))

        self.check_interval_slider = QSlider(Qt.Horizontal)
        self.check_interval_slider.setMinimum(20)
        self.check_interval_slider.setMaximum(300)
        self.check_interval_slider.setSingleStep(1)
        self.check_interval_slider.setValue(20)
        self.check_interval_slider.setTickInterval(10)
        self.check_interval_slider.setTickPosition(QSlider.TicksBelow)
        self.check_interval_slider.setStyleSheet("""
            QSlider::groove:horizontal { background: #374a5e; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #c3e0f7; border: 2px solid #6699cc; width: 18px; height: 18px; border-radius: 9px; margin: -7px 0; }
        """)
        self.check_interval_label = QLabel("20 seconds")
        self.check_interval_label.setStyleSheet("color: #b0c4de; font-size: 13px; margin-left: 10px; font-family: 'Tahoma', 'Arial', sans-serif;")
        def update_check_interval_label():
            val = self.check_interval_slider.value()
            self.check_interval_label.setText(f"{val} seconds")
        self.check_interval_slider.valueChanged.connect(update_check_interval_label)
        update_check_interval_label()
        slider_widget = QWidget()
        slider_layout = QHBoxLayout()
        slider_layout.setContentsMargins(0,0,0,0)
        slider_layout.addWidget(self.check_interval_slider)
        slider_layout.addWidget(self.check_interval_label)
        slider_widget.setLayout(slider_layout)
        settings_layout.addRow("Check Interval:", slider_widget)

        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        settings_layout.addRow(save_button)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        self.status_label = QLabel("Status: Not Running")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #f2f2f2; font-family: 'Tahoma', 'Arial', sans-serif;")
        right_layout.addWidget(self.status_label)

        self.last_check_label = QLabel("Last Check: N/A")
        self.last_check_label.setStyleSheet("color: #b0c4de;")
        right_layout.addWidget(self.last_check_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_layout.addWidget(self.log_text, stretch=1)

        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Bot")
        self.start_button.clicked.connect(self.start_bot)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Bot")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        right_layout.addLayout(control_layout)

        self.made_by_label = QLabel("Made by Kaan Akkaya")
        self.made_by_label.setObjectName("madeByLabel")
        self.made_by_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        right_layout.addWidget(self.made_by_label, alignment=Qt.AlignBottom | Qt.AlignRight)

        main_layout.addWidget(self.settings_panel)
        main_layout.addWidget(right_widget, stretch=1)

        self.animation = QPropertyAnimation(self.settings_panel, b"maximumWidth")
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.setDuration(300)
        self.is_settings_open = False

        self.ban_checker_thread = None
        self.load_config()

    def toggle_settings(self):
        if not self.is_settings_open:
            target_width = 360
            self.animation.stop()
            self.animation.setStartValue(self.settings_panel.width())
            self.animation.setEndValue(target_width)
            self.animation.start()
            self.is_settings_open = True
        else:
            self.animation.stop()
            self.animation.setStartValue(self.settings_panel.width())
            self.animation.setEndValue(0)
            self.animation.start()
            self.is_settings_open = False

    def load_config(self):
        load_dotenv()
        for key, widget in self.env_fields.items():
            value = os.getenv(key, "")
            if isinstance(widget, QLineEdit):
                widget.setText(value)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(value.lower() == "true")
        inventory_type_raw = os.getenv("INVENTORY_TYPE", "cs2")
        inventory_types = [x.strip() for x in inventory_type_raw.lower().split(",") if x.strip()]
        if "all" in inventory_types:
            for k in self.inventory_type_checkboxes:
                self.inventory_type_checkboxes[k].setChecked(k == "all")
        else:
            for k in ["cs2", "tf2", "dota2"]:
                self.inventory_type_checkboxes[k].setChecked(k in inventory_types)
            self.inventory_type_checkboxes["all"].setChecked(False)
        if self.inventory_type_checkboxes["all"].isChecked():
            for k in ["cs2", "tf2", "dota2"]:
                self.inventory_type_checkboxes[k].setEnabled(False)
        else:
            for k in ["cs2", "tf2", "dota2"]:
                self.inventory_type_checkboxes[k].setEnabled(True)
        interval = int(os.getenv("CHECK_INTERVAL", "20"))
        if interval < 20: interval = 20
        if interval > 300: interval = 300
        self.check_interval_slider.setValue(interval)

    def save_config(self):
        try:
            with open(".env", "w", encoding="utf-8") as f:
                for key, widget in self.env_fields.items():
                    value = widget.text() if isinstance(widget, QLineEdit) else str(widget.isChecked()).lower()
                    f.write(f"{key}={value}\n")
                if self.inventory_type_checkboxes["all"].isChecked():
                    f.write("INVENTORY_TYPE=all\n")
                else:
                    selected = [k for k in ["cs2", "tf2", "dota2"] if self.inventory_type_checkboxes[k].isChecked()]
                    if selected:
                        f.write("INVENTORY_TYPE=" + ",".join(selected) + "\n")
                    else:
                        f.write("INVENTORY_TYPE=cs2\n")
                f.write(f"CHECK_INTERVAL={self.check_interval_slider.value()}\n")
            if self.ban_checker_thread and self.ban_checker_thread.isRunning():
                self.stop_bot()
                time.sleep(0.5)
                self.start_bot()
                msg = QMessageBox()
                msg.setWindowTitle("Info")
                msg.setText("Configuration saved and bot restarted with new settings.")
                msg.setStyleSheet("QLabel { color: #D8D8D8; } QMessageBox { background-color: #23272A; }")
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Success")
                msg.setText("Configuration saved successfully!")
                msg.setStyleSheet("QLabel { color: #D8D8D8; } QMessageBox { background-color: #23272A; }")
                msg.exec_()
        except Exception as e:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to save configuration: {str(e)}")
            msg.setStyleSheet("QLabel { color: #D8D8D8; } QMessageBox { background-color: #23272A; }")
            msg.exec_()

    def start_bot(self):
        if not os.path.exists(".env"):
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please save configuration before starting!")
            msg.setStyleSheet("QLabel { color: #D8D8D8; } QMessageBox { background-color: #23272A; }")
            msg.exec_()
            return
        if not self.env_fields["ProfileToWatch"].text():
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("ProfileToWatch is required!")
            msg.setStyleSheet("QLabel { color: #D8D8D8; } QMessageBox { background-color: #23272A; }")
            msg.exec_()
            return

        if self.ban_checker_thread and self.ban_checker_thread.isRunning():
            self.ban_checker_thread.stop()
            self.ban_checker_thread.wait()

        self.ban_checker_thread = BanCheckerThread()
        self.ban_checker_thread.log_signal.connect(self.append_log)
        self.ban_checker_thread.status_signal.connect(self.update_status)
        self.ban_checker_thread.finished_signal.connect(self.on_process_finished)
        self.ban_checker_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #6699cc; font-family: 'Tahoma', 'Arial', sans-serif;")
        msg = QMessageBox()
        msg.setWindowTitle("Info")
        msg.setText("Bot started successfully!")
        msg.setStyleSheet("QLabel { color: #D8D8D8; } QMessageBox { background-color: #23272A; }")
        msg.exec_()

    def stop_bot(self):
        if self.ban_checker_thread and self.ban_checker_thread.isRunning():
            self.ban_checker_thread.stop()
            self.ban_checker_thread.wait()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Not Running")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #f2f2f2; font-family: 'Tahoma', 'Arial', sans-serif;")
        msg = QMessageBox()
        msg.setWindowTitle("Info")
        msg.setText("Bot stopped successfully!")
        msg.setStyleSheet("QLabel { color: #D8D8D8; } QMessageBox { background-color: #23272A; }")
        msg.exec_()

    def on_process_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Not Running")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #f2f2f2; font-family: 'Tahoma', 'Arial', sans-serif;")

    def append_log(self, text):
        if "[ERROR]" in text:
            color = "#cc3333"
        elif "[ALERT]" in text:
            color = "#ffd700"
        elif "[OK]" in text:
            color = "#43d14f"
        elif "[INFO]" in text:
            color = "#6699cc"
        elif "[ACTION]" in text:
            color = "#FFD580"
        elif "[CHECK]" in text:
            color = "#a6c8e0"
        else:
            color = "#d8d8d8"

        if "Checking profile" in text:
            import re
            match = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", text)
            if match:
                saat = match.group(1)
            else:
                match2 = re.search(r"(\d{4}-\d2-\d{2} \d{2}:\d{2}:\d{2})", text)
                saat = match2.group(1) if match2 else "?"
            self.last_check_label.setText(f"Last Check: {saat}")

        html = f'<span style="color: {color}; font-family: Tahoma, Arial, sans-serif;">{text}</span>'
        self.log_text.append(html)
        self.log_text.ensureCursorVisible()

    def update_status(self, status, color):
        self.status_label.setText(f"Status: {status}")
        self.status_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {color}; font-family: 'Tahoma', 'Arial', sans-serif;")
        if "Ban Detected" in status:
            msg = QMessageBox()
            msg.setWindowTitle("Alert")
            msg.setText("Ban detected! Trade process initiated.")
            msg.setStyleSheet("QLabel { color: #D8D8D8; } QMessageBox { background-color: #23272A; }")
            msg.exec_()
            QApplication.instance().beep()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Tahoma", 12))
    window = BanShieldGUI()
    window.show()
    sys.exit(app.exec_())
