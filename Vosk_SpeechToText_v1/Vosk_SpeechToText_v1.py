import sys
import json
import threading
import queue
import os
import sounddevice as sd
import numpy as np
import keyboard
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, 
                             QVBoxLayout, QHBoxLayout, QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from vosk import Model, KaldiRecognizer

# ==========================
#  پیدا کردن خودکار مسیر مدل
# ==========================
def find_model_path():
    possible_paths = [
        "models/vosk-model-fa-0.42",
        "vosk-model-fa-0.42",
        "models/vosk-model-fa-0.22",
        "vosk-model-fa-0.22",
    ]
    for path in possible_paths:
        if os.path.exists(os.path.join(path, "am", "final.mdl")):
            return path
    return None

# ==========================
#  کلاس تشخیص گفتار با Vosk
# ==========================
class SpeechRecognizer(QObject):
    text_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.model_path = find_model_path()
        if not self.model_path:
            raise FileNotFoundError("مدل Vosk پیدا نشد! لطفاً مسیر را بررسی کنید.")
        print(f"✅ مدل در مسیر {self.model_path} پیدا شد.")
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.model = None

    def start(self):
        if not self.model:
            self.model = Model(self.model_path)
        self.is_running = True
        threading.Thread(target=self._recognize_loop, daemon=True).start()

    def stop(self):
        self.is_running = False

    def _recognize_loop(self):
        try:
            recognizer = KaldiRecognizer(self.model, 16000)
            
            def callback(indata, frames, time, status):
                if status:
                    print(f"خطا: {status}")
                self.audio_queue.put(bytes(indata))

            with sd.RawInputStream(samplerate=16000, channels=1, dtype='int16',
                                   callback=callback, blocksize=4000):
                while self.is_running:
                    data = self.audio_queue.get()
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip()
                        if text:
                            self.text_ready.emit(text)
        except Exception as e:
            print(f"خطا در تشخیص صدا: {e}")

# ==========================
#  پنجره اصلی
# ==========================
class FloatingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.recognizer = None
        self.init_ui()
        self.init_tray()

    def init_ui(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background: rgba(20, 20, 30, 220);
                border-radius: 16px;
                border: 1px solid #444;
            }
            QLabel {
                color: #eee;
                font-size: 18px;
                padding: 5px;
            }
            QPushButton {
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton#close_btn {
                background: transparent;
                color: #ff6b6b;
                border: none;
                font-size: 20px;
                border-radius: 15px;
                padding: 5px 10px;
            }
            QPushButton#close_btn:hover {
                background: #c0392b;
                color: white;
            }
            QPushButton#minimize_btn {
                background: transparent;
                color: #aaa;
                border: none;
                font-size: 20px;
            }
            QPushButton#minimize_btn:hover {
                color: white;
            }
            QLabel#footer {
                color: #7f8c8d;
                font-size: 11px;
            }
            QLabel#footer a {
                color: #4a9eff;
                text-decoration: none;
            }
        """)

        # دکمه‌های کنترل بالا
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setFixedSize(35, 35)
        self.close_btn.clicked.connect(self.quit_app)
        title_layout.addWidget(self.close_btn)

        self.minimize_btn = QPushButton("━")
        self.minimize_btn.setObjectName("minimize_btn")
        self.minimize_btn.setFixedSize(35, 35)
        self.minimize_btn.clicked.connect(self.minimize_to_tray)
        title_layout.addWidget(self.minimize_btn)

        # برچسب متن
        self.text_label = QLabel("👂 برای شروع ضبط، دکمه را بزنید")
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(50)

        # دکمه ضبط
        self.record_btn = QPushButton("🎤 شروع")
        self.record_btn.setFixedSize(100, 50)
        self.record_btn.clicked.connect(self.toggle_recording)

        # چیدمان
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.record_btn)

        # ===== بخش فوتر (نام، نسخه و لینک گیت‌هاب) =====
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 5, 0, 0)
        footer_layout.setSpacing(8)

        author_label = QLabel("ساخته شده توسط MA.AD.GH")
        author_label.setObjectName("footer")
        footer_layout.addWidget(author_label)

        version_label = QLabel("نسخه ۱.۰")
        version_label.setObjectName("footer")
        footer_layout.addWidget(version_label)

        link_label = QLabel('<a href="https://github.com/mahanneman">GitHub</a>')
        link_label.setObjectName("footer")
        link_label.setOpenExternalLinks(True)
        footer_layout.addWidget(link_label)

        footer_layout.addStretch()
        # ===== پایان فوتر =====

        # layout اصلی
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.addLayout(title_layout)
        layout.addWidget(self.text_label)
        layout.addLayout(btn_layout)
        layout.addLayout(footer_layout)   # اضافه کردن فوتر

        self.setLayout(layout)
        self.setFixedSize(450, 220)  # افزایش ارتفاع برای فوتر

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
            event.accept()

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if not self.recognizer:
            try:
                self.recognizer = SpeechRecognizer()
                self.recognizer.text_ready.connect(self.update_text)
            except FileNotFoundError as e:
                self.text_label.setText(f"❌ {e}")
                return
        self.recognizer.start()
        self.is_recording = True
        self.record_btn.setText("⏹ توقف")
        self.record_btn.setStyleSheet("background: #c0392b;")
        self.text_label.setText("🔴 در حال ضبط... (صحبت کنید)")

    def stop_recording(self):
        if self.recognizer:
            self.recognizer.stop()
        self.is_recording = False
        self.record_btn.setText("🎤 شروع")
        self.record_btn.setStyleSheet("background: #2980b9;")
        self.text_label.setText("✅ ضبط متوقف شد")

    # ==========================================
    #  🧠 پردازش فرمان‌های صوتی
    # ==========================================
    def execute_command(self, text):
        """
        بررسی می‌کند که متن شامل فرمان‌های خاص است یا خیر.
        اگر فرمان تشخیص داده شد، عمل مربوطه را انجام می‌دهد و True برمی‌گرداند.
        """
        text_lower = text.lower().strip()
        
        # --- لیست فرمان‌ها و عملیات مربوطه ---
        commands = {
            "delete all": self.cmd_delete_all,
            "clear": self.cmd_delete_all,
            "copy": self.cmd_copy,
            "ctrl c": self.cmd_copy,
            "paste": self.cmd_paste,
            "ctrl v": self.cmd_paste,
            "enter": self.cmd_enter,
            "new line": self.cmd_enter,
            "undo": self.cmd_undo,
            "ctrl z": self.cmd_undo,
        }
        
        # بررسی تطابق با فرمان‌ها (با احتساب کلمات کلیدی)
        for cmd, func in commands.items():
            if cmd in text_lower:
                # اجرای عمل
                func()
                # نمایش بازخورد در پنجره
                self.text_label.setText(f"⚡ اجرای فرمان: {cmd}")
                # بازنشانی پیام بعد از ۲ ثانیه
                QApplication.processEvents()
                return True
        
        return False

    # --- توابع عملیاتی ---
    def cmd_delete_all(self):
        """پاک کردن تمام متن (Ctrl+A + Delete)"""
        time.sleep(0.1)
        keyboard.press_and_release('ctrl+a')
        time.sleep(0.05)
        keyboard.press_and_release('backspace')

    def cmd_copy(self):
        """کپی کردن (Ctrl+C)"""
        time.sleep(0.1)
        keyboard.press_and_release('ctrl+c')
        self.text_label.setText("📋 متن کپی شد")

    def cmd_paste(self):
        """چسباندن (Ctrl+V)"""
        time.sleep(0.1)
        keyboard.press_and_release('ctrl+v')
        self.text_label.setText("📋 متن چسبانده شد")

    def cmd_enter(self):
        """زدن دکمه Enter"""
        time.sleep(0.1)
        keyboard.press_and_release('enter')
        self.text_label.setText("⏎ Enter زده شد")

    def cmd_undo(self):
        """بازگردانی (Ctrl+Z)"""
        time.sleep(0.1)
        keyboard.press_and_release('ctrl+z')
        self.text_label.setText("↩️ بازگردانی (Undo)")

    # ==========================================
    #  بروزرسانی متن (تایپ یا اجرای فرمان)
    # ==========================================
    def update_text(self, text):
        # ابتدا بررسی می‌کنیم که آیا فرمان است؟
        if self.execute_command(text):
            # اگر فرمان بود، دیگر تایپ نمی‌کنیم
            return
        
        # در غیر این صورت، متن را تایپ می‌کنیم
        try:
            keyboard.write(text + " ")
            self.text_label.setText(f"📝 {text}")
        except Exception as e:
            print(f"خطا در تایپ خودکار: {e}")
            # در صورت خطا، کپی در کلیپ‌بورد به‌عنوان پشتیبان
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.text_label.setText(f"📋 کپی شد (تایپ نشد)")

    # ==========================================
    #  سیستم تری (Tray)
    # ==========================================
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # ساخت آیکون ساده
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(100, 200, 255))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(10, 10, 44, 44)
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        show_action = QAction("نمایش پنجره", self)
        show_action.triggered.connect(self.show_window)
        quit_action = QAction("خروج", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def minimize_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            "برنامه‌ی تبدیل صدا به متن",
            "برنامه در پس‌زمینه فعال است.",
            QSystemTrayIcon.Information,
            2000
        )

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        if self.recognizer:
            self.recognizer.stop()
        QApplication.quit()

# ==========================
#  اجرا
# ==========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())