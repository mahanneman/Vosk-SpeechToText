import sys
import json
import threading
import queue
import os
import sounddevice as sd
import keyboard
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, 
                             QVBoxLayout, QHBoxLayout, QSystemTrayIcon, QMenu, QAction,
                             QFrame, QComboBox, QRadioButton)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QObject, QTimer, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QDesktopServices
from vosk import Model, KaldiRecognizer

# =============================================
#  پیدا کردن مسیر مدل
# =============================================
def find_model_path(lang_code):
    model_map = {
        'fa': 'vosk-model-fa',
        'en': 'vosk-model-en-us',
    }
    model_name = model_map.get(lang_code)
    if not model_name:
        return None
    possible_paths = [
        os.path.join("models", model_name),
        model_name,
    ]
    for path in possible_paths:
        if os.path.exists(os.path.join(path, "am", "final.mdl")):
            return path
    return None

# =============================================
#  کلاس تشخیص گفتار (نسخه پایدار)
# =============================================
class SpeechRecognizer(QObject):
    text_ready = pyqtSignal(str)

    def __init__(self, lang_code='fa'):
        super().__init__()
        self.lang_code = lang_code
        self.model_path = find_model_path(lang_code)
        if not self.model_path:
            raise FileNotFoundError(f"مدل برای زبان {lang_code} پیدا نشد!")
        
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.model = None
        self.stream = None
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self.is_running:
                return
            
            if not self.model:
                self.model = Model(self.model_path)
            
            self.is_running = True
            self._stop_event.clear()
            
            # تخلیه کامل صف
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            self._thread = threading.Thread(target=self._recognize_loop, daemon=True)
            self._thread.start()

    def stop(self):
        with self._lock:
            if not self.is_running:
                return
            
            self.is_running = False
            self._stop_event.set()
            
            # بستن استریم
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None
            
            # تخلیه صف
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
        
        # صبر کردن تا ترد کامل تموم بشه (حداکثر ۱ ثانیه)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def _recognize_loop(self):
        try:
            recognizer = KaldiRecognizer(self.model, 16000)

            def callback(indata, frames, time_info, status):
                if status:
                    print(f"Audio status: {status}")
                if self.is_running and not self._stop_event.is_set():
                    try:
                        self.audio_queue.put(bytes(indata), block=False)
                    except queue.Full:
                        pass

            self.stream = sd.RawInputStream(
                samplerate=16000,
                channels=1,
                dtype='int16',
                callback=callback,
                blocksize=4000
            )
            self.stream.start()

            while self.is_running and not self._stop_event.is_set():
                try:
                    data = self.audio_queue.get(timeout=0.25)
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip()
                        if text:
                            self.text_ready.emit(text)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"خطا در پردازش: {e}")
                    break

        except Exception as e:
            print(f"خطا در حلقه تشخیص: {e}")
        finally:
            self.is_running = False
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None

# =============================================
#  پنجره اصلی
# =============================================
class FloatingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.recognizer = None
        self.current_lang = 'fa'
        self.timer_seconds = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer_mode = "off"
        
        self.init_ui()
        self.init_tray()
        self.setup_hotkeys()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background: rgba(20, 20, 30, 220);
                border-radius: 16px;
                border: 1px solid #444;
            }
            QLabel {
                color: #eee;
                font-size: 15px;
                padding: 3px;
            }
            QPushButton {
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                padding: 6px;
            }
            QPushButton#close_btn {
                background: transparent;
                color: #ff6b6b;
                border: none;
                font-size: 18px;
                border-radius: 12px;
                padding: 4px 8px;
            }
            QPushButton#close_btn:hover {
                background: #c0392b;
                color: white;
            }
            QPushButton#minimize_btn {
                background: transparent;
                color: #aaa;
                border: none;
                font-size: 18px;
                padding: 4px 8px;
            }
            QPushButton#minimize_btn:hover {
                color: white;
            }
            QPushButton#timer_btn {
                background: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #555;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
                font-size: 14px;
            }
            QPushButton#timer_btn:hover {
                background: #34495e;
            }
            QPushButton#record_btn {
                min-width: 80px;
                max-width: 80px;
                min-height: 40px;
                max-height: 40px;
                font-size: 14px;
            }
            QComboBox {
                background: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 4px 8px;
                min-width: 80px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #2c3e50;
                color: #ecf0f1;
                selection-background-color: #34495e;
            }
            QRadioButton {
                color: #ccc;
                font-size: 12px;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid #555;
                background: #2c3e50;
            }
            QRadioButton::indicator:checked {
                background: #27ae60;
                border: 1px solid #27ae60;
            }
        """)

        title_layout = QHBoxLayout()
        title_layout.addStretch()
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.quit_app)
        title_layout.addWidget(self.close_btn)
        self.minimize_btn = QPushButton("━")
        self.minimize_btn.setObjectName("minimize_btn")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.clicked.connect(self.minimize_to_tray)
        title_layout.addWidget(self.minimize_btn)

        self.text_label = QLabel("👂 برای شروع ضبط، دکمه را بزنید")
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(40)
        self.text_label.setAlignment(Qt.AlignCenter)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(6)

        self.record_btn = QPushButton("🎤 شروع")
        self.record_btn.setObjectName("record_btn")
        self.record_btn.clicked.connect(self.toggle_recording)
        control_layout.addWidget(self.record_btn)

        timer_frame = QFrame()
        timer_frame.setStyleSheet("border: 1px solid #444; border-radius: 8px; padding: 2px;")
        timer_layout = QHBoxLayout(timer_frame)
        timer_layout.setSpacing(2)
        timer_layout.setContentsMargins(4, 2, 4, 2)
        self.timer_minus_btn = QPushButton("−")
        self.timer_minus_btn.setObjectName("timer_btn")
        self.timer_minus_btn.clicked.connect(lambda: self.adjust_timer(-5))
        timer_layout.addWidget(self.timer_minus_btn)
        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet("color: #f1c40f; font-size: 16px; font-weight: bold; min-width: 45px; text-align: center;")
        self.timer_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.timer_label)
        self.timer_plus_btn = QPushButton("+")
        self.timer_plus_btn.setObjectName("timer_btn")
        self.timer_plus_btn.clicked.connect(lambda: self.adjust_timer(5))
        timer_layout.addWidget(self.timer_plus_btn)
        control_layout.addWidget(timer_frame)

        mode_frame = QFrame()
        mode_frame.setStyleSheet("border: 1px solid #444; border-radius: 8px; padding: 2px;")
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setSpacing(4)
        mode_layout.setContentsMargins(6, 2, 6, 2)
        self.radio_off = QRadioButton("خاموش‌کن")
        self.radio_off.setChecked(True)
        self.radio_off.toggled.connect(lambda: self.set_timer_mode("off"))
        mode_layout.addWidget(self.radio_off)
        self.radio_on = QRadioButton("روشن‌کن")
        self.radio_on.toggled.connect(lambda: self.set_timer_mode("on"))
        mode_layout.addWidget(self.radio_on)
        control_layout.addWidget(mode_frame)

        lang_frame = QFrame()
        lang_frame.setStyleSheet("border: 1px solid #444; border-radius: 8px; padding: 2px;")
        lang_layout = QHBoxLayout(lang_frame)
        lang_layout.setSpacing(4)
        lang_layout.setContentsMargins(6, 2, 6, 2)
        lang_label = QLabel("🌐")
        lang_label.setStyleSheet("color: #ecf0f1; font-size: 14px;")
        lang_layout.addWidget(lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("فارسی", "fa")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        control_layout.addWidget(lang_frame)

        self.status_label = QLabel("⏱️ تایمر: غیرفعال | حالت: خاموش‌کن | زبان: فارسی | شورت‌کات: Ctrl+Shift+L")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 2px;")
        self.status_label.setAlignment(Qt.AlignCenter)

        # ===== بخش فوتر (نام، نسخه و لینک گیت‌هاب) =====
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 2, 0, 0)
        footer_layout.setSpacing(8)

        author_label = QLabel("ساخته شده توسط MA.AD.GH")
        author_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        footer_layout.addWidget(author_label)

        version_label = QLabel("نسخه ۲.۰")
        version_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        footer_layout.addWidget(version_label)

        link_label = QLabel('<a href="https://github.com/mahanneman" style="color: #4a9eff; text-decoration: none;">GitHub</a>')
        link_label.setStyleSheet("color: #4a9eff; font-size: 11px;")
        link_label.setOpenExternalLinks(True)
        footer_layout.addWidget(link_label)

        footer_layout.addStretch()
        # ===== پایان فوتر =====

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(5)
        main_layout.addLayout(title_layout)
        main_layout.addWidget(self.text_label)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(footer_layout)   # اضافه کردن فوتر
        self.setLayout(main_layout)
        self.setFixedSize(680, 190)  # افزایش ارتفاع برای جا دادن فوتر

    # ===== شورت‌کات =====
    def setup_hotkeys(self):
        try:
            keyboard.add_hotkey('ctrl+shift+l', self.toggle_language_hotkey, suppress=False)
        except Exception as e:
            print(f"خطا در ثبت شورت‌کات: {e}")

    def toggle_language_hotkey(self):
        QTimer.singleShot(0, self.switch_language)

    def switch_language(self):
        if self.current_lang == 'fa':
            self.lang_combo.setCurrentIndex(1)
        else:
            self.lang_combo.setCurrentIndex(0)

    # ===== تایمر =====
    def adjust_timer(self, delta):
        self.timer_seconds = max(0, self.timer_seconds + delta)
        self.update_timer_display()
        self.update_status_label()

    def update_timer_display(self):
        self.timer_label.setText(self.format_time(self.timer_seconds))

    def format_time(self, seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def set_timer_mode(self, mode):
        self.timer_mode = mode
        self.update_status_label()

    def update_status_label(self):
        mode_text = "خاموش‌کن" if self.timer_mode == "off" else "روشن‌کن"
        lang_text = "فارسی" if self.current_lang == "fa" else "انگلیسی"
        if self.timer_seconds > 0:
            self.status_label.setText(f"⏱️ تایمر فعال: {self.format_time(self.timer_seconds)} | حالت: {mode_text} | زبان: {lang_text} | شورت‌کات: Ctrl+Shift+L")
        else:
            self.status_label.setText(f"⏱️ تایمر: غیرفعال | حالت: {mode_text} | زبان: {lang_text} | شورت‌کات: Ctrl+Shift+L")

    def start_timer(self):
        if self.timer_seconds > 0:
            self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()

    def on_timer_tick(self):
        if self.timer_seconds > 0:
            self.timer_seconds -= 1
            self.update_timer_display()
            if self.timer_seconds == 0:
                self.execute_timer_action()
        else:
            self.stop_timer()

    def execute_timer_action(self):
        if self.timer_mode == "off":
            if self.is_recording:
                self.stop_recording()
                self.status_label.setText("⏱️ تایمر: ضبط خاموش شد")
            else:
                self.status_label.setText("⏱️ تایمر: ضبط در حال حاضر خاموش است")
        else:
            if not self.is_recording:
                self.start_recording()
                self.status_label.setText("⏱️ تایمر: ضبط روشن شد")
            else:
                self.status_label.setText("⏱️ تایمر: ضبط در حال حاضر روشن است")
        self.timer_seconds = 0
        self.update_timer_display()
        self.update_status_label()

    # ===== تغییر زبان (بهینه‌شده) =====
    def on_language_changed(self, index):
        lang_code = self.lang_combo.itemData(index)
        if lang_code == self.current_lang:
            return

        was_recording = self.is_recording
        
        # اول کامل متوقف کن
        if was_recording:
            self.stop_recording()
        
        self.current_lang = lang_code
        # recognizer قبلی رو دور بنداز تا مدل جدید ساخته بشه
        self.recognizer = None
        self.update_status_label()
        
        lang_name = "فارسی" if lang_code == "fa" else "انگلیسی"
        self.text_label.setText(f"🔄 زبان به {lang_name} تغییر کرد")
        
        # اگر قبلاً ضبط می‌کرد، بعد از کمی تأخیر دوباره شروع کن
        if was_recording:
            QTimer.singleShot(500, self.start_recording)

    # ===== ضبط =====
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if self.is_recording:
            return
            
        try:
            # هر بار recognizer جدید بساز تا وضعیت تمیز باشه
            if self.recognizer is None or self.recognizer.lang_code != self.current_lang:
                self.recognizer = SpeechRecognizer(self.current_lang)
                self.recognizer.text_ready.connect(self.update_text)
            
            self.recognizer.start()
            self.is_recording = True
            self.record_btn.setText("⏹ توقف")
            self.record_btn.setStyleSheet("background: #c0392b;")
            self.text_label.setText("🔴 در حال ضبط...")
            
            if self.timer_seconds > 0 and self.timer_mode == "off":
                self.start_timer()
                
        except FileNotFoundError as e:
            self.text_label.setText(f"❌ {e}")
            self.is_recording = False
        except Exception as e:
            self.text_label.setText(f"❌ خطا در شروع: {e}")
            self.is_recording = False
            print(f"Start error: {e}")

    def stop_recording(self):
        if not self.is_recording:
            return
            
        if self.recognizer:
            self.recognizer.stop()
        
        self.is_recording = False
        self.record_btn.setText("🎤 شروع")
        self.record_btn.setStyleSheet("background: #2c3e50;")
        self.text_label.setText("✅ ضبط متوقف شد")
        self.stop_timer()
        
        if self.timer_seconds > 0 and self.timer_mode == "on":
            self.start_timer()

    # ===== فرمان‌های صوتی =====
    def execute_command(self, text):
        text_lower = text.lower().strip()
        text_clean = text.strip()

        # تغییر زبان
        if self.current_lang == 'fa':
            if any(x in text_clean for x in ["تغییر انگلیسی", "انگلیسی کن", "برو انگلیسی"]) or \
               any(x in text_lower for x in ["change english", "switch to english", "english please"]):
                QTimer.singleShot(0, lambda: self.lang_combo.setCurrentIndex(1))
                self.text_label.setText("⚡ زبان → انگلیسی")
                return True

        if self.current_lang == 'en':
            if any(x in text_lower for x in [
                "persian", "farsi", "persian change", "farsi change",
                "change to persian", "change to farsi",
                "switch to persian", "switch to farsi", "go persian"
            ]):
                QTimer.singleShot(0, lambda: self.lang_combo.setCurrentIndex(0))
                self.text_label.setText("⚡ Language → Persian")
                return True

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
        for cmd, func in commands.items():
            if cmd in text_lower:
                func()
                self.text_label.setText(f"⚡ {cmd}")
                return True
        return False

    def cmd_delete_all(self):
        time.sleep(0.08)
        keyboard.press_and_release('ctrl+a')
        time.sleep(0.04)
        keyboard.press_and_release('backspace')
        self.text_label.setText("🗑️ پاک شد")

    def cmd_copy(self):
        time.sleep(0.08)
        keyboard.press_and_release('ctrl+c')
        self.text_label.setText("📋 کپی")

    def cmd_paste(self):
        time.sleep(0.08)
        keyboard.press_and_release('ctrl+v')
        self.text_label.setText("📋 چسباندن")

    def cmd_enter(self):
        time.sleep(0.08)
        keyboard.press_and_release('enter')
        self.text_label.setText("⏎ Enter")

    def cmd_undo(self):
        time.sleep(0.08)
        keyboard.press_and_release('ctrl+z')
        self.text_label.setText("↩️ Undo")

    def update_text(self, text):
        if self.execute_command(text):
            return
        try:
            keyboard.write(text + " ")
            self.text_label.setText(f"📝 {text}")
        except Exception as e:
            print(f"Type error: {e}")
            QApplication.clipboard().setText(text)
            self.text_label.setText("📋 کپی شد (تایپ نشد)")

    # ===== تری =====
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
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
        self.tray_icon.showMessage("برنامه", "در پس‌زمینه فعال است.", QSystemTrayIcon.Information, 2000)

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
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
            event.accept()

# =============================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())