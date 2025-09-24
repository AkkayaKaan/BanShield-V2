# BanShieldGUI.py — Final: Stable scrollable Settings, fixed label width, no squish + Dry-Run + Filters
import sys
import os
import subprocess
import time
import threading
import platform
import psutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QTextEdit, QPushButton, QLabel,
    QMessageBox, QCheckBox, QSizePolicy, QSlider, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont, QIcon
from dotenv import load_dotenv

# ------------------------------ Worker Thread ------------------------------
class BanCheckerThread(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal()

    def __init__(self, dry_run: bool = False):
        super().__init__()
        self.process = None
        self.running = False
        self.script_dir = os.path.abspath(os.path.dirname(__file__))
        self.dry_run = dry_run

    def read_output(self, stream, stream_type):
        while self.running and self.process:
            line = stream.readline()
            if not line:
                continue
            timestamp = time.strftime('%H:%M:%S')
            if stream_type == "stdout":
                self.log_signal.emit(f"[{timestamp}] [STDOUT] {line.strip()}")
                if "[DRY-RUN]" in line and "ban detected" in line.lower():
                    self.status_signal.emit("Simulated Ban Detected", "#86c47c")
                if "Simulation is about to end" in line:
                    self.status_signal.emit("Simulation: Listing Items", "#86c47c")
                elif "BAN DETECTED" in line and "[DRY-RUN]" not in line:
                    self.status_signal.emit("Ban Detected!", "#cc3333")
                    QApplication.instance().beep()
                elif "NO BAN" in line and "[DRY-RUN]" not in line:
                    self.status_signal.emit("No Ban", "#6699cc")
            else:
                if "DeprecationWarning" not in line and "trace-deprecation" not in line:
                    self.log_signal.emit(f"[{timestamp}] [ERROR] {line.strip()}")
                    self.status_signal.emit("Error", "#cc3333")

    def run(self):
        self.running = True
        try:
            python_cmd = "python3" if platform.system() in ["Darwin", "Linux"] else "python"
            mode = "DRY-RUN" if self.dry_run else "LIVE"
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] [INFO] Starting BanChecker.py ({mode}) with {python_cmd} in {self.script_dir}...")

            env = os.environ.copy()
            if self.dry_run:
                env["BANSHIELD_DRY_RUN"] = "1"

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
                env=env
            )

            threading.Thread(target=self.read_output, args=(self.process.stdout, "stdout"), daemon=True).start()
            threading.Thread(target=self.read_output, args=(self.process.stderr, "stderr"), daemon=True).start()

            while self.running:
                if self.process.poll() is not None:
                    self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] [INFO] BanChecker.py process finished with return code {self.process.returncode}")
                    self.finished_signal.emit()
                    break
                time.sleep(0.5)
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

# ------------------------------ Main Window ------------------------------
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
                border-radius: 3px;
                font-size: 13px;
                font-family: 'Tahoma', 'Arial', sans-serif;
                padding: 6px 8px;
                min-height: 26px;
            }
            QCheckBox { color: #D8D8D8; font-size: 13px; min-height: 20px; }
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
            QSlider#checkIntervalSlider::groove:horizontal {
                background: #374a5e;
                height: 6px;
                border-radius: 3px;
            }
            QSlider#checkIntervalSlider::handle:horizontal {
                background: #86a1c6;
                border: 1px solid #334d66;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -7px 0;
            }
            #settingsPanel {
                background: #20232A;
                border-right: 2px solid #39495C;
            }
            /* QScrollArea'nın içindeki alanı ve widget'ı da tema ile uyumlu yap */
            QScrollArea, #settingsPanel QWidget {
                background-color: transparent;
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

        self.was_dry_run = False
        self.OPEN_WIDTH = 400   # geniş ama stabil; inputlar sıkışmaz
        self.LABEL_W = 150      # sabit label sütunu

        # Root layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)
        main_widget.setLayout(main_layout)

        # Toggle button (left)
        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.clicked.connect(self.toggle_settings)
        main_layout.addWidget(self.toggle_button)

        # ---------------- Settings (ScrollArea) ----------------
        self.settings_scroll = QScrollArea()
        self.settings_scroll.setObjectName("settingsPanel")
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_scroll.setMaximumWidth(self.OPEN_WIDTH)   # animasyon buna çalışacak

        settings_content = QWidget()
        content_wrap = QVBoxLayout()
        content_wrap.setContentsMargins(10, 12, 10, 12)  # padding
        content_wrap.setSpacing(10)
        settings_content.setLayout(content_wrap)

        settings_layout = QFormLayout()
        settings_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        settings_layout.setFormAlignment(Qt.AlignTop)
        settings_layout.setLabelAlignment(Qt.AlignLeft)
        settings_layout.setHorizontalSpacing(12)
        settings_layout.setVerticalSpacing(8)
        content_wrap.addLayout(settings_layout)

        self.settings_scroll.setWidget(settings_content)

        # ---------------- ENV fields ----------------
        def mklabel(txt: str) -> QLabel:
            lb = QLabel(txt)
            lb.setMinimumWidth(self.LABEL_W)
            lb.setMaximumWidth(self.LABEL_W)
            lb.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            return lb

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
            "TelegramNotify": QCheckBox(),
        }
        # secret echoes
        self.env_fields["WatchingProfilePassword"].setEchoMode(QLineEdit.Password)
        self.env_fields["BankAccountPassword"].setEchoMode(QLineEdit.Password)
        self.env_fields["WatchingProfileSharedSecret"].setEchoMode(QLineEdit.Password)
        self.env_fields["WatchingProfileIdentitySecret"].setEchoMode(QLineEdit.Password)
        self.env_fields["BankAccountSharedSecret"].setEchoMode(QLineEdit.Password)
        self.env_fields["TELEGRAM_BOT_TOKEN"].setEchoMode(QLineEdit.Password)

        for k, w in self.env_fields.items():
            if isinstance(w, QLineEdit):
                w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                w.setMinimumWidth(220)

        def add_row(key: str, label_txt: str):
            settings_layout.addRow(mklabel(label_txt + ":"), self.env_fields[key])

        add_row("ProfileToWatch", "Profile URL")
        add_row("WatchingProfileUsername", "WatchingProfileUsername")
        add_row("WatchingProfilePassword", "WatchingProfilePassword")
        add_row("WatchingProfileSharedSecret", "WatchingProfileSharedSecret")
        add_row("WatchingProfileIdentitySecret", "WatchingProfileIdentitySecret")
        add_row("BankAccountTradeURL", "BankAccountTradeURL")
        add_row("BankAccountUsername", "BankAccountUsername")
        add_row("BankAccountPassword", "BankAccountPassword")
        add_row("BankAccountSharedSecret", "BankAccountSharedSecret")
        add_row("AutoAccept", "Auto Accept")
        add_row("TELEGRAM_BOT_TOKEN", "Telegram Bot Token")
        add_row("TELEGRAM_CHAT_ID", "Telegram Chat ID")
        add_row("TelegramNotify", "Mobile/Telegram Alarm")

        # Inventory selection
        from functools import partial
        self.inventory_type_checkboxes = {
            "cs2": QCheckBox("CS2 Items"),
            "tf2": QCheckBox("TF2 Items"),
            "dota2": QCheckBox("Dota 2 Items"),
            "all": QCheckBox("All Inventory")
        }
        for cb in self.inventory_type_checkboxes.values():
            cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            cb.setMinimumHeight(20)

        inventory_type_widget = QWidget()
        inventory_type_vbox = QVBoxLayout()
        inventory_type_vbox.setContentsMargins(0, 0, 0, 0)
        inventory_type_vbox.setSpacing(4)
        for cb in self.inventory_type_checkboxes.values():
            inventory_type_vbox.addWidget(cb)
        inventory_type_widget.setLayout(inventory_type_vbox)
        settings_layout.addRow(mklabel("Inventory to Send:"), inventory_type_widget)

        def inventory_type_changed(_k):
            if self.inventory_type_checkboxes["all"].isChecked():
                for kk in ["cs2", "tf2", "dota2"]:
                    self.inventory_type_checkboxes[kk].setChecked(False)
                    self.inventory_type_checkboxes[kk].setEnabled(False)
            else:
                for kk in ["cs2", "tf2", "dota2"]:
                    self.inventory_type_checkboxes[kk].setEnabled(True)
        for k, cb in self.inventory_type_checkboxes.items():
            cb.stateChanged.connect(partial(inventory_type_changed, k))

        # Check Interval
        self.check_interval_slider = QSlider(Qt.Horizontal)
        self.check_interval_slider.setObjectName("checkIntervalSlider")
        self.check_interval_slider.setMinimum(20)
        self.check_interval_slider.setMaximum(300)
        self.check_interval_slider.setSingleStep(1)
        self.check_interval_slider.setValue(20)
        self.check_interval_slider.setTickInterval(10)
        self.check_interval_slider.setTickPosition(QSlider.TicksBelow)
        self.check_interval_label = QLabel("20 seconds")
        self.check_interval_label.setStyleSheet("color: #b0c4de; font-size: 13px; margin-left: 8px; font-family: 'Tahoma', 'Arial', sans-serif;")
        check_interval_widget = QWidget()
        check_interval_layout = QHBoxLayout()
        check_interval_layout.setContentsMargins(0, 0, 0, 0)
        check_interval_layout.setSpacing(6)
        check_interval_layout.addWidget(self.check_interval_slider)
        check_interval_layout.addWidget(self.check_interval_label)
        check_interval_widget.setLayout(check_interval_layout)
        def update_check_interval_label():
            val = self.check_interval_slider.value()
            self.check_interval_label.setText(f"{val} seconds")
        self.check_interval_slider.valueChanged.connect(update_check_interval_label)
        update_check_interval_label()
        settings_layout.addRow(mklabel("Check Interval:"), check_interval_widget)

        self.auto_restart_checkbox = QCheckBox("Auto Restart if Crash or Exit")
        settings_layout.addRow(mklabel(""), self.auto_restart_checkbox)
        self.scheduled_restart_checkbox = QCheckBox("Scheduled Restart (Every 2 Hours)")
        self.scheduled_restart_checkbox.setToolTip("Enables scheduled restart every 2 hours (set interval in code).")
        settings_layout.addRow(mklabel(""), self.scheduled_restart_checkbox)

        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        settings_layout.addRow(mklabel(""), save_button)

        # ---------------- Right Side ----------------
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)
        right_widget.setLayout(right_layout)

        status_ram_layout = QHBoxLayout()
        status_ram_layout.setContentsMargins(0, 0, 0, 0)
        status_ram_layout.setSpacing(8)

        self.status_label = QLabel("Status: Not Running")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #f2f2f2; font-family: 'Tahoma', 'Arial', sans-serif;")
        status_ram_layout.addWidget(self.status_label, alignment=Qt.AlignLeft)

        status_ram_layout.addStretch(1)

        self.sysmon_label = QLabel("RAM: --- MB")
        self.sysmon_label.setStyleSheet("font-size:12px; color: #CCCCCC; font-family: Tahoma, Arial, sans-serif; padding-right:8px;")
        self.sysmon_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sysmon_label.setFixedHeight(22)
        status_ram_layout.addWidget(self.sysmon_label, alignment=Qt.AlignRight)

        self.dry_run_button = QPushButton("Dry-Run (Simulation)")
        self.dry_run_button.setToolTip("Run a full simulation without sending any trades.")
        self.dry_run_button.setStyleSheet("background:#3d5a40; border:1px solid #2c4330;")
        self.dry_run_button.clicked.connect(self.start_dry_run)
        status_ram_layout.addWidget(self.dry_run_button, alignment=Qt.AlignRight)

        right_layout.addLayout(status_ram_layout)

        self.last_check_label = QLabel("Last Check: N/A")
        self.last_check_label.setStyleSheet("color: #b0c4de;")
        right_layout.addWidget(self.last_check_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_layout.addWidget(self.log_text, stretch=1)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)

        self.start_button = QPushButton("Start BanShield")
        self.start_button.clicked.connect(self.start_bot)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop BanShield")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.clicked.connect(self.clear_log)
        control_layout.addWidget(self.clear_log_button)

        right_layout.addLayout(control_layout)

        self.made_by_label = QLabel("Made by Kaan Akkaya")
        self.made_by_label.setObjectName("madeByLabel")
        self.made_by_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        right_layout.addWidget(self.made_by_label, alignment=Qt.AlignBottom | Qt.AlignRight)

        # Add panels
        main_layout.addWidget(self.settings_scroll)
        main_layout.addWidget(right_widget, stretch=1)

        # Slide animation uses maximumWidth on the scroll area
        self.animation = QPropertyAnimation(self.settings_scroll, b"maximumWidth")
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.setDuration(300)
        self.is_settings_open = True  # start opened

        # Runtime
        self.ban_checker_thread = None
        self.load_config()

        self.sysmon_timer = QTimer()
        self.sysmon_timer.timeout.connect(self.update_sysmon)
        self.sysmon_timer.start(1000)

        self.scheduled_restart_timer = QTimer()
        self.scheduled_restart_timer.timeout.connect(self.handle_scheduled_restart)
        self.scheduled_restart_elapsed = 0

    # ---------------- Helpers / UI ----------------
    def show_message(self, title, text, icon=QMessageBox.Information, timeout=6000):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setStyleSheet("QLabel { color: #D8D8D8; } QMessageBox { background-color: #23272A; }")
        timer = QTimer(msg)
        timer.setInterval(timeout)
        timer.setSingleShot(True)
        timer.timeout.connect(msg.accept)
        timer.start()
        msg.exec_()

    def toggle_settings(self):
        if not self.is_settings_open:
            self.animation.stop()
            self.animation.setStartValue(self.settings_scroll.width())
            self.animation.setEndValue(self.OPEN_WIDTH)
            self.animation.start()
            self.settings_scroll.setMaximumWidth(self.OPEN_WIDTH)
            self.is_settings_open = True
        else:
            self.animation.stop()
            self.animation.setStartValue(self.settings_scroll.width())
            self.animation.setEndValue(0)
            self.animation.start()
            self.settings_scroll.setMaximumWidth(0)
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

        auto_restart = os.getenv("AUTO_RESTART", "false").lower() == "true"
        self.auto_restart_checkbox.setChecked(auto_restart)
        scheduled_restart = os.getenv("SCHEDULED_RESTART", "false").lower() == "true"
        self.scheduled_restart_checkbox.setChecked(scheduled_restart)

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
                    f.write("INVENTORY_TYPE=" + (",".join(selected) if selected else "cs2") + "\n")

                f.write(f"CHECK_INTERVAL={self.check_interval_slider.value()}\n")
                f.write(f"AUTO_RESTART={str(self.auto_restart_checkbox.isChecked()).lower()}\n")
                f.write(f"SCHEDULED_RESTART={str(self.scheduled_restart_checkbox.isChecked()).lower()}\n")

            if self.ban_checker_thread and self.ban_checker_thread.isRunning():
                self.stop_bot()
                time.sleep(0.5)
                self.start_bot()
                self.show_message("Info", "Configuration saved and bot restarted with new settings.")
            else:
                self.show_message("Success", "Configuration saved successfully!")
        except Exception as e:
            self.show_message("Error", f"Failed to save configuration: {str(e)}", icon=QMessageBox.Critical)

    # ---------------- Control ----------------
    def start_bot(self):
        if not os.path.exists(".env"):
            self.show_message("Error", "Please save configuration before starting!", icon=QMessageBox.Critical)
            return
        if not self.env_fields["ProfileToWatch"].text():
            self.show_message("Error", "ProfileToWatch is required!", icon=QMessageBox.Critical)
            return

        self.clear_log()

        if self.ban_checker_thread and self.ban_checker_thread.isRunning():
            self.ban_checker_thread.stop()
            self.ban_checker_thread.wait()

        self.manual_stop = False
        self.was_dry_run = False
        self.ban_checker_thread = BanCheckerThread(dry_run=False)
        self.ban_checker_thread.log_signal.connect(self.append_log)
        self.ban_checker_thread.status_signal.connect(self.update_status)
        self.ban_checker_thread.finished_signal.connect(self.on_process_finished)
        self.ban_checker_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #6699cc; font-family: 'Tahoma', 'Arial', sans-serif;")
        self.show_message("Info", "Bot started successfully!")

        if self.scheduled_restart_checkbox.isChecked():
            self.scheduled_restart_elapsed = 0
            self.scheduled_restart_timer.start(1000)
        else:
            self.scheduled_restart_timer.stop()

    def start_dry_run(self):
        if not os.path.exists(".env"):
            self.show_message("Error", "Please save configuration before starting!", icon=QMessageBox.Critical)
            return
        if not self.env_fields["ProfileToWatch"].text():
            self.show_message("Error", "ProfileToWatch is required!", icon=QMessageBox.Critical)
            return

        self.show_message(
            "Dry-Run (Simulation)",
            "This mode will NOT actually trade any items.\n\n"
            "During the monitoring cycle, between the 3rd and 10th check, a VAC or Game ban will be simulated at a random moment. "
            "Then the accounts will be logged in and:\n\n"
            "Simulation is about to end...\n"
            "If you receive a ban in the future, these items will be sent to your backup account immediately:\n"
            "<all item names will be listed here>\n\n"
            "Press OK to continue.",
            icon=QMessageBox.Information,
            timeout=8000
        )

        if self.ban_checker_thread and self.ban_checker_thread.isRunning():
            self.ban_checker_thread.stop()
            self.ban_checker_thread.wait()

        self.manual_stop = False
        self.was_dry_run = True
        self.ban_checker_thread = BanCheckerThread(dry_run=True)
        self.ban_checker_thread.log_signal.connect(self.append_log)
        self.ban_checker_thread.status_signal.connect(self.update_status)
        self.ban_checker_thread.finished_signal.connect(self.on_process_finished)
        self.ban_checker_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Status: Running (DRY-RUN)")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #86c47c; font-family: 'Tahoma', 'Arial', sans-serif;")
        self.show_message("Info", "Dry-Run started. Watch the log for the simulated trigger.")

    def stop_bot(self):
        self.manual_stop = True
        self.clear_log()
        if self.ban_checker_thread and self.ban_checker_thread.isRunning():
            self.ban_checker_thread.stop()
            self.ban_checker_thread.wait()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Not Running")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #f2f2f2; font-family: 'Tahoma', 'Arial', sans-serif;")
        self.show_message("Info", "Bot stopped successfully!")
        self.scheduled_restart_timer.stop()

    def clear_log(self):
        self.log_text.clear()
        self.last_check_label.setText("Last Check: N/A")

    def on_process_finished(self):
        if self.was_dry_run:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Status: Simulation Finished")
            self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #86c47c; font-family: 'Tahoma', 'Arial', sans-serif;")
            self.scheduled_restart_timer.stop()
            self.manual_stop = False
            return

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Not Running")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #f2f2f2; font-family: 'Tahoma', 'Arial', sans-serif;")
        auto_restart = self.auto_restart_checkbox.isChecked()
        if auto_restart and not self.manual_stop:
            self.append_log("[INFO] BanChecker.py crashed or exited, restarting...")
            time.sleep(1)
            self.start_bot()
        self.manual_stop = False

    # ---------------- UI updates ----------------
    def append_log(self, text):
        if "[ERROR]" in text:
            color = "#cc3333"
        elif "[ALERT]" in text:
            color = "#ffd700"
        elif "[DRY-RUN]" in text or "Status: Running (DRY-RUN)" in text:
            color = "#86c47c"
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
            m = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", text)
            if m:
                t = m.group(1)
            else:
                m2 = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
                t = m2.group(1) if m2 else "?"
            self.last_check_label.setText(f"Last Check: {t}")

        html = f'<span style="color: {color}; font-family: Tahoma, Arial, sans-serif;">{text}</span>'
        self.log_text.append(html)
        self.log_text.ensureCursorVisible()

    def update_status(self, status, color):
        self.status_label.setText(f"Status: {status}")
        self.status_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {color}; font-family: 'Tahoma', 'Arial', sans-serif;")
        if "Ban Detected" in status and "Simulated" not in status:
            self.show_message("Alert", "Ban detected! Trade process initiated.")

    def update_sysmon(self):
        pids = {os.getpid()}
        if self.ban_checker_thread and self.ban_checker_thread.process:
            pids.add(self.ban_checker_thread.process.pid)
            try:
                proc = psutil.Process(self.ban_checker_thread.process.pid)
                for child in proc.children(recursive=True):
                    pids.add(child.pid)
            except Exception:
                pass
        mem_total = 0
        for pid in pids:
            try:
                mem_total += psutil.Process(pid).memory_info().rss
            except Exception:
                continue
        self.sysmon_label.setText(f"RAM: {mem_total/(1024*1024):.1f} MB")

    def handle_scheduled_restart(self):
        if not self.scheduled_restart_checkbox.isChecked():
            self.scheduled_restart_timer.stop()
            self.scheduled_restart_elapsed = 0
            return
        interval_seconds = 7200
        self.scheduled_restart_elapsed += 1
        if self.scheduled_restart_elapsed >= interval_seconds:
            self.append_log("[INFO] Scheduled Restart: BanChecker.py is being restarted.")
            self.scheduled_restart_elapsed = 0
            self.stop_bot()
            QTimer.singleShot(1000, self.start_bot)

# ------------------------------ Boot ------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Tahoma", 12))
    window = BanShieldGUI()
    window.show()
    sys.exit(app.exec_())