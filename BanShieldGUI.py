import sys
import os
import subprocess
import time
import threading
import platform
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QFormLayout, QLineEdit, QTextEdit, QPushButton, QLabel, 
                             QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QIcon  # QIcon eklendi
from dotenv import load_dotenv

class BanCheckerThread(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)  # status, color
    finished_signal = pyqtSignal()  # Process bittiğinde sinyal

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
                        self.status_signal.emit("No Ban", "#4CAF50")
                    elif "BAN DETECTED" in line:
                        self.status_signal.emit("Ban Detected!", "#F44336")
                        QApplication.instance().beep()
                else:  # stderr
                    if "DeprecationWarning" not in line and "trace-deprecation" not in line:
                        self.log_signal.emit(f"[{timestamp}] [ERROR] {line.strip()}")
                        self.status_signal.emit("Error", "#F44336")

    def run(self):
        self.running = True
        try:
            python_cmd = "python3" if platform.system() == "Darwin" or platform.system() == "Linux" else "python"
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

            # Ayrı thread'lerde stdout ve stderr oku
            stdout_thread = threading.Thread(target=self.read_output, args=(self.process.stdout, "stdout"))
            stderr_thread = threading.Thread(target=self.read_output, args=(self.process.stderr, "stderr"))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            # Thread'lerin bitmesini bekle (process bitene kadar)
            stdout_thread.join()
            stderr_thread.join()

            while self.running:
                if self.process.poll() is not None:
                    self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] [INFO] BanChecker.py process finished with return code {self.process.returncode}")
                    self.finished_signal.emit()
                    break

        except Exception as e:
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] [ERROR] {str(e)}")
            self.status_signal.emit("Error", "#F44336")
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
        # İkon ekleme
        self.setWindowIcon(QIcon("icon.ico"))
        self.setStyleSheet("""
            QMainWindow { background-color: #2E2E2E; }
            QLabel { color: #FFFFFF; font-size: 14px; }
            QLineEdit { background-color: #424242; color: #FFFFFF; border: 1px solid #2196F3; padding: 5px; border-radius: 5px; }
            QTextEdit { background-color: #424242; color: #FFFFFF; border: 1px solid #2196F3; border-radius: 5px; }
            QPushButton { 
                background-color: #2196F3; 
                color: #FFFFFF; 
                border: none; 
                padding: 5px; 
                border-radius: 5px; 
                font-size: 14px; 
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #757575; }
            QCheckBox { color: #FFFFFF; }
            #settingsPanel { background-color: #333333; border-right: 1px solid #2196F3; }
            #toggleButton { 
                background-color: #2196F3; 
                color: #FFFFFF; 
                padding: 5px; 
                border-radius: 5px; 
                font-size: 16px; 
                qproperty-text: "☰"; 
            }
            #toggleButton:hover { background-color: #1976D2; }
            #madeByLabel { color: #B0BEC5; font-size: 12px; }
        """)

        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_widget.setLayout(main_layout)

        # Toggle düğmesi
        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.clicked.connect(self.toggle_settings)
        main_layout.addWidget(self.toggle_button)

        # Settings paneli
        self.settings_panel = QWidget()
        self.settings_panel.setObjectName("settingsPanel")
        self.settings_panel.setFixedWidth(0)  # Başlangıçta gizli
        settings_layout = QFormLayout()
        self.settings_panel.setLayout(settings_layout)

        # Konfigürasyon alanları
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
            "AutoAccept": QCheckBox()
        }
        self.env_fields["WatchingProfilePassword"].setEchoMode(QLineEdit.Password)
        self.env_fields["BankAccountPassword"].setEchoMode(QLineEdit.Password)
        self.env_fields["WatchingProfileSharedSecret"].setEchoMode(QLineEdit.Password)
        self.env_fields["WatchingProfileIdentitySecret"].setEchoMode(QLineEdit.Password)
        self.env_fields["BankAccountSharedSecret"].setEchoMode(QLineEdit.Password)

        for key, widget in self.env_fields.items():
            label = key.replace("ProfileToWatch", "Profile URL").replace("AutoAccept", "Auto Accept")
            settings_layout.addRow(label + ":", widget)

        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        settings_layout.addRow(save_button)

        # Sağ panel (log ve kontroller)
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        # Durum ekranı
        self.status_label = QLabel("Status: Not Running")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        right_layout.addWidget(self.status_label)

        self.last_check_label = QLabel("Last Check: N/A")
        self.last_check_label.setStyleSheet("color: #B0BEC5;")
        right_layout.addWidget(self.last_check_label)

        # Log ekranı
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_layout.addWidget(self.log_text, stretch=1)  # Log alanını esnek yap

        # Kontrol butonları
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Bot")
        self.start_button.clicked.connect(self.start_bot)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Bot")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        right_layout.addLayout(control_layout)

        # "Made by Kaan Akkaya" etiketi
        self.made_by_label = QLabel("Made by Kaan Akkaya")
        self.made_by_label.setObjectName("madeByLabel")
        self.made_by_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        right_layout.addWidget(self.made_by_label, alignment=Qt.AlignBottom | Qt.AlignRight)

        # Layout'ları birleştir
        main_layout.addWidget(self.settings_panel)
        main_layout.addWidget(right_widget, stretch=1)  # Sağ paneli esnek yap

        # Animasyon için ayarlar
        self.animation = QPropertyAnimation(self.settings_panel, b"maximumWidth")
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.setDuration(300)  # 300ms animasyon süresi
        self.is_settings_open = False

        # Thread başlatıcı (her start'ta yeniden oluşturulacak)
        self.ban_checker_thread = None

        # .env dosyasını yükle
        self.load_config()

    def toggle_settings(self):
        if not self.is_settings_open:
            target_width = 270  # Sabit 270px genişlik
            self.animation.setStartValue(self.settings_panel.maximumWidth())
            self.animation.setEndValue(target_width)
            self.animation.start()
            self.is_settings_open = True
        else:
            self.animation.setStartValue(self.settings_panel.maximumWidth())
            self.animation.setEndValue(0)
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

    def save_config(self):
        try:
            with open(".env", "w", encoding="utf-8") as f:
                for key, widget in self.env_fields.items():
                    value = widget.text() if isinstance(widget, QLineEdit) else str(widget.isChecked()).lower()
                    f.write(f"{key}={value}\n")
            if self.ban_checker_thread and self.ban_checker_thread.isRunning():
                self.stop_bot()
                time.sleep(0.5)
                self.start_bot()
                msg = QMessageBox()
                msg.setWindowTitle("Info")
                msg.setText("Configuration saved and bot restarted with new settings.")
                msg.setStyleSheet("QLabel { color: #FFFFFF; } QMessageBox { background-color: #2E2E2E; }")
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Success")
                msg.setText("Configuration saved successfully!")
                msg.setStyleSheet("QLabel { color: #FFFFFF; } QMessageBox { background-color: #2E2E2E; }")
                msg.exec_()
        except Exception as e:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to save configuration: {str(e)}")
            msg.setStyleSheet("QLabel { color: #FFFFFF; } QMessageBox { background-color: #2E2E2E; }")
            msg.exec_()

    def start_bot(self):
        if not os.path.exists(".env"):
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please save configuration before starting!")
            msg.setStyleSheet("QLabel { color: #FFFFFF; } QMessageBox { background-color: #2E2E2E; }")
            msg.exec_()
            return
        if not self.env_fields["ProfileToWatch"].text():
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("ProfileToWatch is required!")
            msg.setStyleSheet("QLabel { color: #FFFFFF; } QMessageBox { background-color: #2E2E2E; }")
            msg.exec_()
            return

        # Eğer eski bir thread varsa, önce kapat
        if self.ban_checker_thread and self.ban_checker_thread.isRunning():
            self.ban_checker_thread.stop()
            self.ban_checker_thread.wait()

        # HER SEFERİNDE YENİ THREAD OLUŞTUR
        self.ban_checker_thread = BanCheckerThread()
        self.ban_checker_thread.log_signal.connect(self.append_log)
        self.ban_checker_thread.status_signal.connect(self.update_status)
        self.ban_checker_thread.finished_signal.connect(self.on_process_finished)
        self.ban_checker_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        msg = QMessageBox()
        msg.setWindowTitle("Info")
        msg.setText("Bot started successfully!")
        msg.setStyleSheet("QLabel { color: #FFFFFF; } QMessageBox { background-color: #2E2E2E; }")
        msg.exec_()

    def stop_bot(self):
        if self.ban_checker_thread and self.ban_checker_thread.isRunning():
            self.ban_checker_thread.stop()
            self.ban_checker_thread.wait()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Not Running")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        msg = QMessageBox()
        msg.setWindowTitle("Info")
        msg.setText("Bot stopped successfully!")
        msg.setStyleSheet("QLabel { color: #FFFFFF; } QMessageBox { background-color: #2E2E2E; }")
        msg.exec_()

    def on_process_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Not Running")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")

    def append_log(self, text):
        # LOG RENGİ SEÇİMİ
        if "[ERROR]" in text:
            color = "#FF5370"
        elif "[ALERT]" in text:
            color = "#F2C94C"
        elif "[OK]" in text:
            color = "#36D399"
        elif "[INFO]" in text:
            color = "#82AAFF"
        elif "[ACTION]" in text:
            color = "#FFB86C"
        elif "[CHECK]" in text:
            color = "#9CDCFE"
        else:
            color = "#E0E0E0"

        # "Checking profile" logunda zamanı çekip Last Check alanını güncelle
        if "Checking profile" in text:
            import re
            # Önce [HH:MM:SS] formatını yakala
            match = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", text)
            if match:
                saat = match.group(1)
            else:
                # Alternatif: tarihli log (2025-07-05 22:10:36)
                match2 = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
                saat = match2.group(1) if match2 else "?"
            self.last_check_label.setText(f"Last Check: {saat}")

        html = f'<span style="color: {color}; font-family: JetBrains Mono, Consolas, monospace;">{text}</span>'
        self.log_text.append(html)
        self.log_text.ensureCursorVisible()

    def update_status(self, status, color):
        self.status_label.setText(f"Status: {status}")
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        if "Ban Detected" in status:
            msg = QMessageBox()
            msg.setWindowTitle("Alert")
            msg.setText("Ban detected! Trade process initiated.")
            msg.setStyleSheet("QLabel { color: #FFFFFF; } QMessageBox { background-color: #2E2E2E; }")
            msg.exec_()
            QApplication.instance().beep()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 12))
    window = BanShieldGUI()
    window.show()
    sys.exit(app.exec_())