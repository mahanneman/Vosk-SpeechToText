# -*- coding: utf-8 -*-
"""
برنامه تبدیل گفتار به متن با Vosk - نسخه نهایی ۴.۲
رفع خطاهای drawRoundedRect و setWindowIcon
"""

import sys
import json
import threading
import queue
import os
import re
import socket
import time
import shutil
import zipfile
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests
import sounddevice as sd
import keyboard
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QSystemTrayIcon, QMenu, QAction, QFrame, QComboBox, QRadioButton,
    QDialog, QProgressDialog, QMessageBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QTextEdit, QFileDialog,
    QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QObject, QTimer, QThread
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush
from vosk import Model, KaldiRecognizer

# =============================================
#  ترجمه‌های رابط کاربری (UI)
# =============================================
UI_STRINGS = {
    'fa': {
        'wait_title': '⏳ لطفاً صبر کنید...',
        'wait_text': 'در حال بارگذاری...',
        'no_model': '📥 هیچ مدلی یافت نشد. لطفاً مدل دانلود کنید.',
        'record_start': '👂 برای شروع ضبط، دکمه را بزنید',
        'recording': '🔴 در حال ضبط...',
        'stop': '⏹ توقف',
        'start': '🎤 شروع',
        'stopped': '✅ ضبط متوقف شد',
        'lang_changed': '🔄 زبان به {name} تغییر کرد',
        'lang_selector': 'زبان تشخیص:',
        'manage_models': '📥 مدیریت مدل‌ها',
        'debug_label': '📂 زبان‌های موجود: {list}',
        'debug_empty': '📂 زبان‌های موجود: (هیچ)',
        'status_timer_off': '⏱️ تایمر: غیرفعال | حالت: {mode} | زبان: {lang} | شروع: Ctrl+Shift+S | توقف: Ctrl+Shift+X | تغییر زبان: Ctrl+Shift+L',
        'status_timer_on': '⏱️ تایمر فعال: {time} | حالت: {mode} | زبان: {lang} | شروع: Ctrl+Shift+S | توقف: Ctrl+Shift+X | تغییر زبان: Ctrl+Shift+L',
        'mode_off': 'خاموش‌کن',
        'mode_on': 'روشن‌کن',
        'timer_action_off': '⏱️ تایمر: ضبط خاموش شد',
        'timer_action_off_already': '⏱️ تایمر: ضبط در حال حاضر خاموش است',
        'timer_action_on': '⏱️ تایمر: ضبط روشن شد',
        'timer_action_on_already': '⏱️ تایمر: ضبط در حال حاضر روشن است',
        'cmd_delete': '🗑️ پاک شد',
        'cmd_copy': '📋 کپی',
        'cmd_paste': '📋 چسباندن',
        'cmd_enter': '⏎ Enter',
        'cmd_undo': '↩️ Undo',
        'cmd_lang_en': '⚡ زبان → انگلیسی',
        'cmd_lang_fa': '⚡ Language → Persian',
        'clipboard_fallback': '📋 کپی شد (تایپ نشد)',
        'tray_message': 'در پس‌زمینه فعال است.',
        'tray_show': 'نمایش پنجره',
        'tray_quit': 'خروج',
        'model_manager_title': 'مدیریت مدل‌های زبان',
        'download_btn': '📥 دانلود انتخاب‌شده‌ها',
        'close_btn': 'بستن',
        'no_selection': 'هیچ مدلی برای دانلود انتخاب نشده.',
        'download_progress': 'در حال دانلود {name}...',
        'download_error': 'دانلود {code} ناموفق: {error}',
        'download_complete': 'دانلود مدل‌ها کامل شد.',
        'ui_lang': 'زبان برنامه:',
        'persian': 'فارسی',
        'english': 'English',
        'search_placeholder': 'جستجوی مدل...',
        'model_name': 'نام مدل',
        'size': 'حجم',
        'language': 'زبان',
        'license': 'مجوز',
        'notes': 'توضیحات',
        'download': 'دانلود',
        'status': 'وضعیت',
        'not_downloaded': 'دانلود نشده',
        'downloaded': 'دانلود شده',
        'downloading': 'در حال دانلود',
        'add_local_model': '➕ افزودن مدل محلی',
        'select_model_folder': 'انتخاب پوشه مدل',
        'model_path': 'مسیر مدل',
        'model_lang': 'کد زبان (مثال: fa)',
        'add_model': 'افزودن مدل',
        'help_tab': 'راهنما',
        'help_text': '''
        <h2>راهنمای مدیریت مدل‌ها</h2>
        <p>برای استفاده از برنامه، باید حداقل یک مدل زبان دانلود کنید.</p>
        <h3>روش‌های افزودن مدل:</h3>
        <ul>
            <li><b>دانلود از سرور:</b> از لیست مدل‌ها، مدل مورد نظر را انتخاب کرده و روی دکمه دانلود کلیک کنید.</li>
            <li><b>افزودن مدل محلی:</b> اگر مدلی را از قبل دانلود کرده‌اید، می‌توانید آن را به برنامه معرفی کنید.</li>
        </ul>
        <h3>از کجا مدل دانلود کنم؟</h3>
        <p>می‌توانید مدل‌های رسمی Vosk را از <a href="https://alphacephei.com/vosk/models">این صفحه</a> دانلود کنید.</p>
        <p>پس از دانلود، فایل zip را در پوشه‌ای extract کنید و از طریق گزینه "افزودن مدل محلی" به برنامه معرفی کنید.</p>
        <p><b>توجه:</b> پوشه مدل باید شامل زیرپوشه‌های am, conf, graph, ivector باشد.</p>
        ''',
        'internet_status': '🌐 وضعیت اینترنت: {status}',
        'online': 'متصل',
        'offline': 'قطع',
        'checking': 'در حال بررسی...',
        'refresh_models': '🔄 بروزرسانی لیست مدل‌ها',
        'eta': 'زمان باقیمانده: {time}',
        'speed': 'سرعت: {speed}',
        'downloaded_size': 'دانلود شده: {downloaded} از {total}',
        'download_finished': '✅ دانلود کامل شد!',
        'download_failed': '❌ دانلود ناموفق: {error}',
        'cancel': 'لغو',
        'confirm_delete': 'آیا از حذف مدل {name} اطمینان دارید؟',
        'delete': '🗑️ حذف',
        'delete_model': 'حذف مدل',
        'app_title': 'برنامه تبدیل گفتار به متن',
        'author': 'ساخته شده توسط MA.AD.GH',
        'version': 'نسخه 3',
    },
    'en': {
        'wait_title': '⏳ Please wait...',
        'wait_text': 'Loading...',
        'no_model': '📥 No model found. Please download a model.',
        'record_start': '👂 Press the button to start recording',
        'recording': '🔴 Recording...',
        'stop': '⏹ Stop',
        'start': '🎤 Start',
        'stopped': '✅ Stopped',
        'lang_changed': '🔄 Language changed to {name}',
        'lang_selector': 'Recognition language:',
        'manage_models': '📥 Manage Models',
        'debug_label': '📂 Available languages: {list}',
        'debug_empty': '📂 Available languages: (none)',
        'status_timer_off': '⏱️ Timer: disabled | Mode: {mode} | Language: {lang} | Start: Ctrl+Shift+S | Stop: Ctrl+Shift+X | Switch language: Ctrl+Shift+L',
        'status_timer_on': '⏱️ Timer active: {time} | Mode: {mode} | Language: {lang} | Start: Ctrl+Shift+S | Stop: Ctrl+Shift+X | Switch language: Ctrl+Shift+L',
        'mode_off': 'Turn off',
        'mode_on': 'Turn on',
        'timer_action_off': '⏱️ Timer: recording stopped',
        'timer_action_off_already': '⏱️ Timer: recording is already off',
        'timer_action_on': '⏱️ Timer: recording started',
        'timer_action_on_already': '⏱️ Timer: recording is already on',
        'cmd_delete': '🗑️ Deleted',
        'cmd_copy': '📋 Copied',
        'cmd_paste': '📋 Pasted',
        'cmd_enter': '⏎ Enter',
        'cmd_undo': '↩️ Undo',
        'cmd_lang_en': '⚡ Language → English',
        'cmd_lang_fa': '⚡ Language → Persian',
        'clipboard_fallback': '📋 Copied to clipboard (could not type)',
        'tray_message': 'Running in background.',
        'tray_show': 'Show Window',
        'tray_quit': 'Quit',
        'model_manager_title': 'Language Model Manager',
        'download_btn': '📥 Download selected',
        'close_btn': 'Close',
        'no_selection': 'No model selected for download.',
        'download_progress': 'Downloading {name}...',
        'download_error': 'Download {code} failed: {error}',
        'download_complete': 'Model download complete.',
        'ui_lang': 'UI Language:',
        'persian': 'Persian',
        'english': 'English',
        'search_placeholder': 'Search models...',
        'model_name': 'Model Name',
        'size': 'Size',
        'language': 'Language',
        'license': 'License',
        'notes': 'Notes',
        'download': 'Download',
        'status': 'Status',
        'not_downloaded': 'Not Downloaded',
        'downloaded': 'Downloaded',
        'downloading': 'Downloading',
        'add_local_model': '➕ Add Local Model',
        'select_model_folder': 'Select Model Folder',
        'model_path': 'Model Path',
        'model_lang': 'Language Code (e.g., fa)',
        'add_model': 'Add Model',
        'help_tab': 'Help',
        'help_text': '''
        <h2>Model Management Help</h2>
        <p>To use the application, you need to download at least one language model.</p>
        <h3>How to add a model:</h3>
        <ul>
            <li><b>Download from server:</b> Select a model from the list and click the download button.</li>
            <li><b>Add local model:</b> If you already have a model downloaded, you can add it to the application.</li>
        </ul>
        <h3>Where to download models?</h3>
        <p>You can download official Vosk models from <a href="https://alphacephei.com/vosk/models">this page</a>.</p>
        <p>After downloading, extract the zip file to a folder and add it through "Add Local Model".</p>
        <p><b>Note:</b> The model folder must contain am, conf, graph, ivector subfolders.</p>
        ''',
        'internet_status': '🌐 Internet Status: {status}',
        'online': 'Online',
        'offline': 'Offline',
        'checking': 'Checking...',
        'refresh_models': '🔄 Refresh Model List',
        'eta': 'Time remaining: {time}',
        'speed': 'Speed: {speed}',
        'downloaded_size': 'Downloaded: {downloaded} of {total}',
        'download_finished': '✅ Download complete!',
        'download_failed': '❌ Download failed: {error}',
        'cancel': 'Cancel',
        'confirm_delete': 'Are you sure you want to delete model {name}?',
        'delete': '🗑️ Delete',
        'delete_model': 'Delete Model',
        'app_title': 'Speech to Text',
        'author': 'Created by MA.AD.GH',
        'version': 'Version 3',
    }
}

# =============================================
#  توابع کمکی برای مدیریت مدل‌ها
# =============================================
def _application_base_dir():
    """Return the folder that contains the .py/.exe so models stay beside the app."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _application_base_dir()
MODEL_DIR = os.path.join(BASE_DIR, "models")
LOCAL_REGISTRY_FILE = os.path.join(MODEL_DIR, ".local_models.json")

LANGUAGE_NAMES = {
    'fa': ('فارسی', 'Persian'), 'en': ('انگلیسی', 'English'), 'ru': ('روسی', 'Russian'),
    'de': ('آلمانی', 'German'), 'fr': ('فرانسوی', 'French'), 'es': ('اسپانیایی', 'Spanish'),
    'it': ('ایتالیایی', 'Italian'), 'nl': ('هلندی', 'Dutch'), 'cn': ('چینی', 'Chinese'),
    'zh': ('چینی', 'Chinese'), 'hi': ('هندی', 'Hindi'), 'pt': ('پرتغالی', 'Portuguese'),
    'ar': ('عربی', 'Arabic'), 'tr': ('ترکی', 'Turkish'), 'vn': ('ویتنامی', 'Vietnamese'),
    'ja': ('ژاپنی', 'Japanese'), 'ko': ('کره‌ای', 'Korean'), 'uk': ('اوکراینی', 'Ukrainian'),
    'kz': ('قزاقی', 'Kazakh'), 'sv': ('سوئدی', 'Swedish'), 'pl': ('لهستانی', 'Polish'),
    'cs': ('چکی', 'Czech'), 'uz': ('ازبکی', 'Uzbek'), 'ca': ('کاتالان', 'Catalan'),
    'el': ('یونانی', 'Greek'), 'eo': ('اسپرانتو', 'Esperanto'), 'br': ('برتون', 'Breton'),
    'gu': ('گجراتی', 'Gujarati'), 'tg': ('تاجیکی', 'Tajik'), 'te': ('تلوگو', 'Telugu'),
    'ky': ('قرقیزی', 'Kyrgyz'), 'ka': ('گرجی', 'Georgian'), 'tl': ('فیلیپینی', 'Filipino'),
    'spk': ('تشخیص گوینده', 'Speaker ID')
}

def get_model_language_code(model_name):
    if not model_name:
        return None
    name = os.path.basename(str(model_name).rstrip('/\\')).lower()
    m = re.match(r'^vosk-model-(?:small-)?([a-z]{2})(?:-|$)', name)
    if m:
        return m.group(1)
    if name.startswith('vosk-model-spk'):
        return 'spk'
    m = re.match(r'^([a-z]{2})(?:-|$)', name)
    return m.group(1) if m else None

def _model_root_from_path(path):
    if not path:
        return None
    path = os.path.abspath(path)
    if os.path.isfile(os.path.join(path, 'am', 'final.mdl')):
        return path
    if not os.path.isdir(path):
        return None
    for root, dirs, files in os.walk(path):
        rel = os.path.relpath(root, path)
        depth = 0 if rel == '.' else rel.count(os.sep) + 1
        if depth > 3:
            dirs[:] = []
            continue
        if os.path.basename(root) == 'am' and 'final.mdl' in files:
            return os.path.dirname(root)
    return None

def _load_local_registry():
    try:
        with open(LOCAL_REGISTRY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _save_local_registry(data):
    os.makedirs(MODEL_DIR, exist_ok=True)
    tmp = LOCAL_REGISTRY_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, LOCAL_REGISTRY_FILE)

def scan_installed_models():
    found = {}
    registry = _load_local_registry()
    candidates = []
    for base in (BASE_DIR, MODEL_DIR):
        if not os.path.isdir(base):
            continue
        try:
            for item in os.listdir(base):
                p = os.path.abspath(os.path.join(base, item))
                if os.path.isdir(p):
                    candidates.append(p)
        except OSError:
            pass
    for key, meta in registry.items():
        if isinstance(meta, dict) and meta.get('path'):
            candidates.append(meta['path'])

    seen_paths = set()
    for candidate in candidates:
        root = _model_root_from_path(candidate)
        if not root:
            continue
        root = os.path.abspath(root)
        if root in seen_paths:
            continue
        seen_paths.add(root)
        model_name = os.path.basename(root)
        reg = registry.get(model_name, {}) if isinstance(registry.get(model_name), dict) else {}
        lang = reg.get('lang') or get_model_language_code(model_name)
        if not lang:
            continue
        found[model_name] = {
            'name': model_name, 'path': root, 'lang': lang,
            'external': not root.startswith(os.path.abspath(MODEL_DIR) + os.sep)
        }
    return found

def get_downloaded_models():
    return sorted({m['lang'] for m in scan_installed_models().values()})

def get_installed_model_names():
    return set(scan_installed_models().keys())

def find_model_path(lang_code):
    if not lang_code:
        return None
    installed = scan_installed_models()
    if lang_code in installed:
        return installed[lang_code]['path']
    matches = [m for m in installed.values() if m['lang'] == lang_code]
    if not matches:
        return None
    matches.sort(key=lambda m: (('small' in m['name'] or 'nano' in m['name']), m['name']))
    return matches[0]['path']

def parse_size(size_str):
    if size_str is None:
        return 0
    s = str(size_str).strip().upper().replace('IB', 'B')
    m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGT]?B?|[KMGT])?\s*$', s)
    if not m:
        return 0
    value = float(m.group(1)); unit = (m.group(2) or 'B').rstrip('B')
    return int(value * {'':1,'K':1024,'M':1024**2,'G':1024**3,'T':1024**4}.get(unit,1))

def format_size(bytes_size):
    value = float(bytes_size or 0)
    for unit in ['B','KB','MB','GB','TB']:
        if value < 1024 or unit == 'TB':
            return f"{value:.1f} {unit}"
        value /= 1024.0

def check_internet():
    # First check actual Vosk access; then fall back to general HTTPS connectivity.
    for url in ('https://alphacephei.com/vosk/models', 'https://www.google.com/generate_204'):
        try:
            r = requests.get(url, timeout=(3, 5), stream=True, allow_redirects=True)
            ok = 200 <= r.status_code < 500
            r.close()
            if ok:
                return True
        except requests.RequestException:
            pass
    try:
        with socket.create_connection(('1.1.1.1', 443), timeout=2):
            return True
    except OSError:
        return False

# =============================================
#  کلاس‌های کمکی برای دریافت و دانلود مدل
# =============================================
class _VoskTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows=[]; self.in_tr=False; self.in_td=False
        self.cells=[]; self.cell_text=[]; self.cell_href=None; self.current_group=''
    def handle_starttag(self, tag, attrs):
        tag=tag.lower()
        if tag=='tr': self.in_tr=True; self.cells=[]
        elif tag=='td' and self.in_tr:
            self.in_td=True; self.cell_text=[]; self.cell_href=None
        elif tag=='a' and self.in_td:
            self.cell_href=dict(attrs).get('href')
    def handle_data(self, data):
        if self.in_td: self.cell_text.append(data)
    def handle_endtag(self, tag):
        tag=tag.lower()
        if tag=='td' and self.in_td:
            txt=' '.join(''.join(self.cell_text).split())
            self.cells.append((txt,self.cell_href)); self.in_td=False
        elif tag=='tr' and self.in_tr:
            if self.cells: self.rows.append(self.cells)
            self.in_tr=False

_FALLBACK_MODEL_ROWS = [
('vosk-model-small-en-us-0.15','40M'),('vosk-model-en-us-0.22','1.8G'),('vosk-model-en-us-0.22-lgraph','128M'),('vosk-model-en-us-0.42-gigaspeech','2.3G'),
('vosk-model-en-us-daanzu-20200905','1.0G'),('vosk-model-en-us-daanzu-20200905-lgraph','129M'),('vosk-model-en-us-librispeech-0.2','845M'),('vosk-model-small-en-us-zamia-0.5','49M'),('vosk-model-en-us-aspire-0.2','1.4G'),('vosk-model-en-us-0.21','1.6G'),
('vosk-model-en-in-0.5','1G'),('vosk-model-small-en-in-0.4','36M'),('vosk-model-small-cn-0.22','42M'),('vosk-model-cn-0.22','1.3G'),('vosk-model-cn-kaldi-multicn-0.15','1.5G'),
('vosk-model-ru-0.42','1.8G'),('vosk-model-small-ru-0.22','45M'),('vosk-model-ru-0.22','1.5G'),('vosk-model-ru-0.10','2.5G'),
('vosk-model-small-fr-0.22','41M'),('vosk-model-fr-0.22','1.4G'),('vosk-model-small-fr-pguyot-0.3','39M'),('vosk-model-fr-0.6-linto-2.2.0','1.5G'),
('vosk-model-de-0.21','1.9G'),('vosk-model-de-tuda-0.6-900k','4.4G'),('vosk-model-small-de-zamia-0.3','49M'),('vosk-model-small-de-0.15','45M'),
('vosk-model-small-es-0.42','39M'),('vosk-model-es-0.42','1.4G'),('vosk-model-small-pt-0.3','31M'),('vosk-model-pt-fb-v0.1.1-20220516_2113','1.6G'),
('vosk-model-el-gr-0.7','1.1G'),('vosk-model-small-tr-0.3','35M'),('vosk-model-small-vn-0.4','32M'),('vosk-model-vn-0.4','78M'),
('vosk-model-small-it-0.22','48M'),('vosk-model-it-0.22','1.2G'),('vosk-model-small-nl-0.22','39M'),('vosk-model-nl-spraakherkenning-0.6','860M'),('vosk-model-nl-spraakherkenning-0.6-lgraph','100M'),
('vosk-model-small-ca-0.4','42M'),('vosk-model-ar-mgb2-0.4','318M'),('vosk-model-ar-0.22-linto-1.1.0','1.3G'),('vosk-model-small-ar-tn-0.1-linto','158M'),('vosk-model-ar-tn-0.1-linto','517M'),
('vosk-model-fa-0.42','1.6G'),('vosk-model-small-fa-0.42','53M'),('vosk-model-fa-0.5','1G'),('vosk-model-small-fa-0.5','60M'),('vosk-model-tl-ph-generic-0.6','320M'),
('vosk-model-small-uk-v3-nano','73M'),('vosk-model-small-uk-v3-small','133M'),('vosk-model-uk-v3','343M'),('vosk-model-uk-v3-lgraph','325M'),
('vosk-model-small-kz-0.42','58M'),('vosk-model-kz-0.42','1.3G'),('vosk-model-small-sv-rhasspy-0.15','289M'),('vosk-model-small-ja-0.22','48M'),('vosk-model-ja-0.22','1Gb'),
('vosk-model-small-eo-0.42','42M'),('vosk-model-small-hi-0.22','42M'),('vosk-model-hi-0.22','1.5Gb'),('vosk-model-small-cs-0.4-rhasspy','44M'),('vosk-model-small-pl-0.22','50M'),
('vosk-model-small-uz-0.22','49M'),('vosk-model-small-ko-0.22','82M'),('vosk-model-br-0.8','70M'),('vosk-model-gu-0.42','700M'),('vosk-model-small-gu-0.42','100M'),
('vosk-model-tg-0.22','327M'),('vosk-model-small-tg-0.22','50M'),('vosk-model-small-te-0.42','58M'),('vosk-model-small-ky-0.42','49M'),('vosk-model-ky-0.42','1.1G'),
('vosk-model-small-ka-0.42','45M'),('vosk-model-ka-0.42','700M'),('vosk-model-spk-0.4','13M')]

def fallback_model_catalog():
    installed=get_installed_model_names(); out={}
    for name,size in _FALLBACK_MODEL_ROWS:
        lang=get_model_language_code(name) or 'other'
        out[name]={'name':name,'url':f'https://alphacephei.com/vosk/models/{name}.zip','size':size,
                   'size_bytes':parse_size(size),'wer':'','notes':'Official Vosk model','license':'','lang':lang,
                   'downloaded':name in installed}
    return out

class ModelFetcher(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    def __init__(self):
        super().__init__(); self.models_url='https://alphacephei.com/vosk/models'
    def run(self):
        try:
            response=requests.get(self.models_url, timeout=12)
            response.raise_for_status()
            models=self.parse_models(response.text)
            if not models: raise ValueError('No Vosk model rows found in the page')
            self.finished.emit(models)
        except Exception as e:
            self.error.emit(str(e))
    def parse_models(self, html_text):
        parser=_VoskTableParser(); parser.feed(html_text)
        models={}; installed=get_installed_model_names(); current_group=''
        for cells in parser.rows:
            texts=[c[0] for c in cells]
            links=[c[1] for c in cells]
            model_idx=None
            for i,href in enumerate(links):
                if href and href.lower().endswith('.zip') and 'vosk-model-' in href:
                    model_idx=i; break
            if model_idx is None:
                if texts and texts[0] and all(not x for x in texts[1:]): current_group=texts[0]
                continue
            href=links[model_idx]
            url=urljoin(self.models_url, href)
            name=texts[model_idx].strip() or os.path.basename(url).rsplit('.',1)[0]
            if not name.startswith('vosk-model-'): continue
            size=texts[model_idx+1] if len(texts)>model_idx+1 else '?'
            wer=texts[model_idx+2] if len(texts)>model_idx+2 else ''
            notes=texts[model_idx+3] if len(texts)>model_idx+3 else ''
            license_text=texts[model_idx+4] if len(texts)>model_idx+4 else ''
            lang=get_model_language_code(name) or 'other'
            models[name]={'name':name,'url':url,'size':size,'size_bytes':parse_size(size),'wer':wer,
                          'notes':notes,'license':license_text,'lang':lang,'group':current_group,
                          'downloaded':name in installed}
        return models

class ModelDownloader(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(str, bool, str)
    eta_updated = pyqtSignal(str)
    def __init__(self, model_name, url, save_path):
        super().__init__(); self.model_name=model_name; self.url=url; self.save_path=save_path; self._is_cancelled=False
    def cancel(self): self._is_cancelled=True
    def run(self):
        temp_extract=None
        try:
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            response=requests.get(self.url, stream=True, timeout=(10,60)); response.raise_for_status()
            total=int(response.headers.get('content-length',0) or 0); downloaded=0; started=time.time(); speed=0.0
            with open(self.save_path,'wb') as f:
                for chunk in response.iter_content(chunk_size=128*1024):
                    if self._is_cancelled:
                        raise RuntimeError('Cancelled')
                    if not chunk: continue
                    f.write(chunk); downloaded += len(chunk)
                    elapsed=max(time.time()-started,0.001); speed=downloaded/elapsed
                    self.progress.emit(downloaded,total,format_size(speed)+'/s')
                    if total and speed:
                        self.eta_updated.emit(self.format_time((total-downloaded)/speed))
            if self._is_cancelled: raise RuntimeError('Cancelled')
            temp_extract=os.path.join(MODEL_DIR,'.extract-'+re.sub(r'[^A-Za-z0-9._-]','_',self.model_name))
            if os.path.exists(temp_extract): shutil.rmtree(temp_extract, ignore_errors=True)
            os.makedirs(temp_extract,exist_ok=True)
            with zipfile.ZipFile(self.save_path,'r') as z:
                base=os.path.abspath(temp_extract)+os.sep
                for member in z.infolist():
                    dest=os.path.abspath(os.path.join(temp_extract,member.filename))
                    if not (dest+os.sep).startswith(base) and dest != base[:-1]:
                        raise ValueError('Unsafe path in ZIP archive')
                z.extractall(temp_extract)
            root=_model_root_from_path(temp_extract)
            if not root: raise ValueError('Downloaded ZIP is not a valid Vosk ASR model (am/final.mdl missing)')
            target=os.path.abspath(os.path.join(MODEL_DIR,self.model_name))
            if os.path.exists(target): shutil.rmtree(target)
            if os.path.abspath(root)==os.path.abspath(temp_extract):
                os.replace(temp_extract,target); temp_extract=None
            else:
                shutil.move(root,target)
            self.finished.emit(self.model_name,True,'Download complete')
        except Exception as e:
            self.finished.emit(self.model_name,False,str(e))
        finally:
            try:
                if os.path.exists(self.save_path): os.remove(self.save_path)
            except OSError: pass
            if temp_extract and os.path.exists(temp_extract): shutil.rmtree(temp_extract,ignore_errors=True)
    @staticmethod
    def format_time(seconds):
        seconds=max(0,int(seconds))
        if seconds<60: return f'{seconds}s'
        if seconds<3600: return f'{seconds//60}m {seconds%60}s'
        return f'{seconds//3600}h {(seconds%3600)//60}m'

class ModelLoadWorker(QThread):
    loaded = pyqtSignal(object)
    failed = pyqtSignal(str)
    def __init__(self,path): super().__init__(); self.path=path
    def run(self):
        try: self.loaded.emit(Model(self.path))
        except Exception as e: self.failed.emit(str(e))

class InternetCheckWorker(QThread):
    checked = pyqtSignal(bool)
    def run(self): self.checked.emit(check_internet())

class LocalModelImporter(QThread):
    finished = pyqtSignal(str, str, bool, str)
    def __init__(self, source, lang): super().__init__(); self.source=source; self.lang=lang
    def run(self):
        try:
            root=_model_root_from_path(self.source)
            if not root: raise ValueError('am/final.mdl was not found in the selected folder')
            name=os.path.basename(root.rstrip('/\\')) or f'local-{self.lang}'
            if not name.startswith('vosk-model-'):
                name=f'vosk-model-{self.lang}-local-{re.sub(r"[^A-Za-z0-9._-]","_",name)}'
            target=os.path.abspath(os.path.join(MODEL_DIR,name))
            source_abs=os.path.abspath(root)
            os.makedirs(MODEL_DIR,exist_ok=True)
            if source_abs != target:
                if os.path.exists(target): raise FileExistsError(f'{name} already exists')
                shutil.copytree(source_abs,target)
            reg=_load_local_registry(); reg[name]={'lang':self.lang,'path':target}; _save_local_registry(reg)
            self.finished.emit(name,self.lang,True,'')
        except Exception as e:
            self.finished.emit('',self.lang,False,str(e))

# =============================================
#  کلاس تشخیص گفتار
# =============================================
class SpeechRecognizer(QObject):
    text_ready = pyqtSignal(str)
    error = pyqtSignal(str)
    stopped = pyqtSignal()

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
            # Re-resolve in case a model was added/replaced after this object was created.
            current_path = find_model_path(self.lang_code)
            if current_path:
                self.model_path = current_path
            if not self.model:
                self.model = Model(self.model_path)
            self.is_running = True
            self._stop_event.clear()
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
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
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
                    print(f"Error in processing: {e}")
                    break
        except Exception as e:
            print(f"Error in recognition loop: {e}")
            self.error.emit(str(e))
        finally:
            self.is_running = False
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None
            self.stopped.emit()

# =============================================
#  تابع ساخت آیکون (جهت استفاده در برنامه و سینی)
# =============================================
def create_app_icon(width=64, height=64):
    """ساخت آیکون میکروفون با QPainter - تابع مستقل برای استفاده در سراسر برنامه"""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    # دایره پس‌زمینه به رنگ آبی
    painter.setBrush(QBrush(QColor(52, 152, 219)))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, width-4, height-4)
    # بدنه میکروفون (مستطیل گرد)
    painter.setBrush(QBrush(QColor(255, 255, 255)))
    pen = QPen(QColor(255, 255, 255))
    pen.setWidth(2)
    painter.setPen(pen)
    rect_x = int(width * 0.25)
    rect_y = int(height * 0.2)
    rect_w = int(width * 0.5)
    rect_h = int(height * 0.4)
    painter.drawRoundedRect(rect_x, rect_y, rect_w, rect_h, 4, 4)
    # پایه میکروفون
    painter.drawLine(int(width * 0.5), int(height * 0.6), int(width * 0.5), int(height * 0.78))
    painter.drawArc(int(width * 0.35), int(height * 0.74), int(width * 0.3), int(height * 0.15), 0, 180 * 16)
    painter.end()
    return pixmap

# =============================================
#  پنجره اصلی
# =============================================
class FloatingWindow(QWidget):
    hotkey_switch_requested = pyqtSignal()
    hotkey_start_requested = pyqtSignal()
    hotkey_stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.recognizer = None
        self.current_lang = 'fa'
        self.ui_lang = 'fa'
        self.timer_seconds = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer_mode = "off"
        self.models = fallback_model_catalog()
        self.downloaders = {}
        self.is_online = False
        self.fetcher = None
        self.internet_worker = None
        self.model_loader = None
        self.model_importer = None
        self.model_wait_dialog = None
        self.model_manager_dialog = None
        self.drag_pos = None

        # اسپلش screen
        self.splash = QDialog(self)
        self.splash.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.splash.setStyleSheet("background: #1a1a2e; color: white; border-radius: 12px;")
        splash_layout = QVBoxLayout()
        splash_layout.addWidget(QLabel(UI_STRINGS['fa']['wait_title']))
        splash_layout.addWidget(QLabel(UI_STRINGS['fa']['wait_text']))
        self.splash.setLayout(splash_layout)
        self.splash.setFixedSize(300, 150)
        self.splash.show()
        QApplication.processEvents()

        self.init_ui()
        self.init_tray()
        # keyboard callbacks run outside the Qt GUI thread; route them through Qt signals.
        self.hotkey_switch_requested.connect(self.switch_language)
        self.hotkey_start_requested.connect(self.start_recording)
        self.hotkey_stop_requested.connect(self.stop_recording)
        self.setup_hotkeys()

        self.is_online = check_internet()
        self.update_internet_status()
        if self.is_online:
            self.fetch_models_from_server()
        else:
            self.refresh_language_list()

        self.internet_timer = QTimer(self)
        self.internet_timer.timeout.connect(self.check_internet_async)
        self.internet_timer.start(10000)

        self.splash.accept()
        self.splash = None

    # =====================
    #  رابط کاربری
    # =====================
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
                color: white;
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
                background: #2c3e50;
            }
            QPushButton#record_btn:hover {
                background: #34495e;
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
            QLineEdit {
                background: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
            }
            QTableWidget {
                background: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #444;
                border-radius: 8px;
                gridline-color: #444;
            }
            QTableWidget::item {
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 5px;
            }
            QTableWidget::item:selected {
                background: #4f86c6;
                color: white;
            }
            QHeaderView::section {
                background: #34495e;
                color: #ecf0f1;
                padding: 5px;
                border: 1px solid #444;
            }
            QTabWidget::pane {
                background: #1a1a2e;
                border: 1px solid #444;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 8px 16px;
                border-radius: 8px 8px 0 0;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #34495e;
            }
            QTextEdit {
                background: #1a1a2e;
                color: #ecf0f1;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
            }
            QGroupBox {
                color: #ecf0f1;
                border: 1px solid #444;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QProgressBar {
                border: 1px solid #444;
                border-radius: 8px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: #27ae60;
                border-radius: 8px;
            }
            #title_bar {
                background: rgba(40, 40, 50, 80);
                border-radius: 16px 16px 0 0;
                padding: 5px;
            }
            #title_bar:hover {
                background: rgba(50, 50, 60, 120);
            }
        """)

        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])

        # نوار عنوان
        title_bar = QFrame()
        title_bar.setObjectName("title_bar")
        title_bar.setFixedHeight(40)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 10, 0)

        icon_label = QLabel()
        icon_pixmap = create_app_icon(24, 24)
        icon_label.setPixmap(icon_pixmap)
        title_bar_layout.addWidget(icon_label)
        title_bar_layout.addStretch()

        self.minimize_btn = QPushButton("━")
        self.minimize_btn.setObjectName("minimize_btn")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.clicked.connect(self.minimize_to_tray)
        title_bar_layout.addWidget(self.minimize_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.quit_app)
        title_bar_layout.addWidget(self.close_btn)

        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move

        # بخش بالایی
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        self.lang_selector_label = QLabel(strings['lang_selector'])
        top_layout.addWidget(self.lang_selector_label)
        self.lang_selector = QComboBox()
        self.lang_selector.currentIndexChanged.connect(self.on_language_selected)
        top_layout.addWidget(self.lang_selector)

        self.ui_lang_label = QLabel(strings['ui_lang'])
        top_layout.addWidget(self.ui_lang_label)
        self.ui_lang_selector = QComboBox()
        self.ui_lang_selector.addItem(strings['persian'], "fa")
        self.ui_lang_selector.addItem(strings['english'], "en")
        self.ui_lang_selector.currentIndexChanged.connect(self.on_ui_language_changed)
        top_layout.addWidget(self.ui_lang_selector)

        self.manage_models_btn = QPushButton(strings['manage_models'])
        self.manage_models_btn.setStyleSheet("background: #2980b9;")
        self.manage_models_btn.clicked.connect(self.open_model_manager)
        top_layout.addWidget(self.manage_models_btn)

        self.internet_status_label = QLabel("🌐 " + strings['checking'])
        self.internet_status_label.setStyleSheet("color: #f1c40f; font-size: 11px;")
        top_layout.addWidget(self.internet_status_label)
        top_layout.addStretch()

        # Debug
        self.debug_label = QLabel(strings['debug_empty'])
        self.debug_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")

        # Text Label
        self.text_label = QLabel(strings['record_start'])
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(40)
        self.text_label.setAlignment(Qt.AlignCenter)

        # Controls
        control_layout = QHBoxLayout()
        control_layout.setSpacing(6)

        self.record_btn = QPushButton(strings['start'])
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
        self.radio_off = QRadioButton(strings['mode_off'])
        self.radio_off.setChecked(True)
        self.radio_off.toggled.connect(lambda checked: checked and self.set_timer_mode("off"))
        mode_layout.addWidget(self.radio_off)
        self.radio_on = QRadioButton(strings['mode_on'])
        self.radio_on.toggled.connect(lambda checked: checked and self.set_timer_mode("on"))
        mode_layout.addWidget(self.radio_on)
        control_layout.addWidget(mode_frame)

        # Status
        self.status_label = QLabel(strings['status_timer_off'].format(mode=strings['mode_off'], lang="?"))
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 2px;")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 2, 0, 0)
        footer_layout.setSpacing(8)
        self.author_label = QLabel(strings['author'])
        self.author_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        footer_layout.addWidget(self.author_label)
        self.version_label = QLabel(strings['version'])
        self.version_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        footer_layout.addWidget(self.version_label)
        link_label = QLabel('<a href="https://github.com/mahanneman" style="color: #4a9eff; text-decoration: none;">GitHub</a>')
        link_label.setStyleSheet("color: #4a9eff; font-size: 11px;")
        link_label.setOpenExternalLinks(True)
        footer_layout.addWidget(link_label)
        footer_layout.addStretch()

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(5)
        main_layout.addWidget(title_bar)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.text_label)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.debug_label)
        main_layout.addLayout(footer_layout)
        self.setLayout(main_layout)
        self.setFixedSize(820, 280)

        self.apply_ui_direction()

    def title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()

    def title_bar_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
            event.accept()

    def apply_ui_direction(self):
        self.setLayoutDirection(Qt.RightToLeft if self.ui_lang == 'fa' else Qt.LeftToRight)
        for w in (self.text_label, self.status_label, self.debug_label):
            w.setAlignment(Qt.AlignCenter)
        self.lang_selector.setLayoutDirection(Qt.LeftToRight)
        self.ui_lang_selector.setLayoutDirection(Qt.LeftToRight)

    def on_ui_language_changed(self, index):
        lang_code = self.ui_lang_selector.itemData(index)
        if lang_code == self.ui_lang:
            return
        self.ui_lang = lang_code
        self.update_ui_texts()
        self.apply_ui_direction()

    def update_ui_texts(self):
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.lang_selector_label.setText(strings['lang_selector'])
        self.ui_lang_label.setText(strings['ui_lang'])
        self.manage_models_btn.setText(strings['manage_models'])
        if hasattr(self, 'author_label'):
            self.author_label.setText(strings['author'])
        if hasattr(self, 'version_label'):
            self.version_label.setText(strings['version'])
        self.setWindowTitle(strings['app_title'])
        self.record_btn.setText(strings['stop'] if self.is_recording else strings['start'])
        self.record_btn.setStyleSheet('background: #c0392b; color:white;' if self.is_recording else 'background:#2c3e50;color:white;')
        self.radio_off.setText(strings['mode_off'])
        self.radio_on.setText(strings['mode_on'])
        if self.lang_selector.count() == 0:
            self.text_label.setText(strings['no_model'])
        elif self.is_recording:
            self.text_label.setText(strings['recording'])
        else:
            self.text_label.setText(strings['record_start'])
        self.ui_lang_selector.blockSignals(True)
        self.ui_lang_selector.clear()
        self.ui_lang_selector.addItem(strings['persian'], 'fa')
        self.ui_lang_selector.addItem(strings['english'], 'en')
        idx = self.ui_lang_selector.findData(self.ui_lang)
        if idx >= 0:
            self.ui_lang_selector.setCurrentIndex(idx)
        self.ui_lang_selector.blockSignals(False)
        if hasattr(self, 'tray_show_action'):
            self.tray_show_action.setText(strings['tray_show'])
            self.tray_quit_action.setText(strings['tray_quit'])
        self.refresh_language_list()
        self.update_status_label()
        self.update_debug_label()
        self.update_internet_status()
        self.apply_ui_direction()

    def update_debug_label(self):
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        installed = scan_installed_models()
        if installed:
            names = [m['name'] for m in installed.values()]
            self.debug_label.setText(strings['debug_label'].format(list=', '.join(names)))
        else:
            self.debug_label.setText(strings['debug_empty'])

    def update_internet_status(self):
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        status = strings['online'] if self.is_online else strings['offline']
        self.internet_status_label.setText(strings['internet_status'].format(status=status))
        self.internet_status_label.setStyleSheet(f"color: {'#27ae60' if self.is_online else '#e74c3c'}; font-size:11px;")

    def check_internet_async(self):
        if self.internet_worker and self.internet_worker.isRunning():
            return
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.internet_status_label.setText(strings['internet_status'].format(status=strings['checking']))
        self.internet_status_label.setStyleSheet("color:#f1c40f; font-size:11px;")
        self.internet_worker = InternetCheckWorker(self)
        self.internet_worker.checked.connect(self._internet_checked)
        self.internet_worker.start()

    def _internet_checked(self, online):
        was_online = self.is_online
        self.is_online = bool(online)
        self.update_internet_status()
        if hasattr(self, 'manager_internet_label') and self.manager_internet_label:
            strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
            status = strings['online'] if self.is_online else strings['offline']
            self.manager_internet_label.setText(strings['internet_status'].format(status=status))
            self.manager_internet_label.setStyleSheet(f"color: {'#27ae60' if self.is_online else '#e74c3c'};")
        if self.is_online and not was_online:
            self.fetch_models_from_server()

    def fetch_models_from_server(self):
        if self.fetcher and self.fetcher.isRunning():
            return
        self.fetcher = ModelFetcher()
        self.fetcher.finished.connect(self.on_models_fetched)
        self.fetcher.error.connect(self.on_fetch_error)
        self.fetcher.start()

    def _merge_installed_into_catalog(self):
        installed = scan_installed_models()
        for name, meta in installed.items():
            if name not in self.models:
                self.models[name] = {
                    'name': name, 'url': '', 'size': '?', 'size_bytes': 0,
                    'wer': '', 'notes': 'Local model', 'license': '', 'lang': meta['lang'],
                    'downloaded': True
                }
            else:
                self.models[name]['downloaded'] = True
        for name, info in self.models.items():
            info['downloaded'] = name in installed

    def on_models_fetched(self, models):
        self.models = models or fallback_model_catalog()
        self._merge_installed_into_catalog()
        self.is_online = True
        self.refresh_language_list()
        self.update_internet_status()
        if hasattr(self, 'models_table') and self.models_table:
            self.populate_models_table()

    def on_fetch_error(self, error):
        print(f'Error fetching models: {error}')
        if not self.models:
            self.models = fallback_model_catalog()
        self._merge_installed_into_catalog()
        self.refresh_language_list()
        if hasattr(self, 'models_table') and self.models_table:
            self.populate_models_table()

    def refresh_language_list(self):
        installed = scan_installed_models()
        current = self.current_lang
        by_lang = {}
        for meta in installed.values():
            by_lang.setdefault(meta['lang'], []).append(meta)

        self.lang_selector.blockSignals(True)
        self.lang_selector.clear()
        for lang in sorted(by_lang):
            choices = sorted(by_lang[lang], key=lambda m: (('small' in m['name'] or 'nano' in m['name']), m['name']))
            chosen = choices[0]
            fa, en = LANGUAGE_NAMES.get(lang, (lang, lang))
            display = fa if self.ui_lang == 'fa' else en
            self.lang_selector.addItem(f'{display} — {chosen["name"]}', lang)

        idx = self.lang_selector.findData(current)
        if idx < 0 and self.lang_selector.count() > 0:
            idx = 0
        if idx >= 0:
            self.lang_selector.setCurrentIndex(idx)
            self.current_lang = self.lang_selector.itemData(idx)
        else:
            self.current_lang = None
            strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
            self.text_label.setText(strings['no_model'])
        self.lang_selector.blockSignals(False)
        self._merge_installed_into_catalog()
        self.update_debug_label()
        self.update_status_label()

    def on_language_selected(self, index):
        if index < 0:
            return
        lang_code = self.lang_selector.itemData(index)
        if not lang_code or lang_code == self.current_lang:
            return
        was_recording = self.is_recording
        if was_recording:
            self.stop_recording()
        self.current_lang = lang_code
        self.recognizer = None
        self.update_status_label()
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.text_label.setText(strings['lang_changed'].format(name=self.lang_selector.currentText()))
        if was_recording:
            QTimer.singleShot(250, self.start_recording)

    def setup_hotkeys(self):
        try:
            keyboard.add_hotkey('ctrl+shift+l', self.toggle_language_hotkey, suppress=False)
            keyboard.add_hotkey('ctrl+shift+s', self.start_hotkey, suppress=False)
            keyboard.add_hotkey('ctrl+shift+x', self.stop_hotkey, suppress=False)
        except Exception as e:
            print(f"Error setting hotkeys: {e}")

    def toggle_language_hotkey(self):
        self.hotkey_switch_requested.emit()

    def start_hotkey(self):
        self.hotkey_start_requested.emit()

    def stop_hotkey(self):
        self.hotkey_stop_requested.emit()

    def switch_language(self):
        if self.lang_selector.count() == 0:
            return
        current_idx = self.lang_selector.currentIndex()
        next_idx = (current_idx + 1) % self.lang_selector.count()
        self.lang_selector.setCurrentIndex(next_idx)

    def adjust_timer(self, delta):
        self.timer_seconds = max(0, self.timer_seconds + delta)
        self.update_timer_display()
        if self.timer_seconds == 0:
            self.stop_timer()
        elif (self.timer_mode == "on" and not self.is_recording) or (self.timer_mode == "off" and self.is_recording):
            self.start_timer()
        self.update_status_label()

    def update_timer_display(self):
        self.timer_label.setText(self.format_time(self.timer_seconds))

    def format_time(self, seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def set_timer_mode(self, mode):
        self.timer_mode = mode
        if self.timer_seconds > 0:
            should_run = (mode == "on" and not self.is_recording) or (mode == "off" and self.is_recording)
            if should_run:
                self.start_timer()
            else:
                self.stop_timer()
        self.update_status_label()

    def update_status_label(self):
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        mode_text = strings['mode_off'] if self.timer_mode == 'off' else strings['mode_on']
        lang_text = self.lang_selector.currentText() if self.lang_selector.count() else '?'
        key = 'status_timer_on' if self.timer_seconds > 0 else 'status_timer_off'
        values = {'mode': mode_text, 'lang': lang_text, 'time': self.format_time(self.timer_seconds)}
        self.status_label.setText(strings[key].format(**values))

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
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        if self.timer_mode == "off":
            if self.is_recording:
                self.stop_recording()
                self.status_label.setText(strings['timer_action_off'])
            else:
                self.status_label.setText(strings['timer_action_off_already'])
        else:
            if not self.is_recording:
                self.start_recording()
                self.status_label.setText(strings['timer_action_on'])
            else:
                self.status_label.setText(strings['timer_action_on_already'])
        self.timer_seconds = 0
        self.update_timer_display()
        self.update_status_label()

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if self.is_recording or (self.model_loader and self.model_loader.isRunning()):
            return
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        if not self.current_lang or not find_model_path(self.current_lang):
            self.text_label.setText(strings['no_model'])
            self.refresh_language_list()
            return
        try:
            if self.recognizer is not None and self.recognizer.lang_code == self.current_lang and self.recognizer.model is not None:
                self._finish_start_recording()
                return
            self.recognizer = SpeechRecognizer(self.current_lang)
            self.recognizer.text_ready.connect(self.update_text)
            self.recognizer.error.connect(self.on_recognizer_error)
            self.recognizer.stopped.connect(self.on_recognizer_stopped)
            self.model_wait_dialog = QProgressDialog(strings['wait_text'], '', 0, 0, self)
            self.model_wait_dialog.setWindowTitle(strings['wait_title'])
            self.model_wait_dialog.setCancelButton(None)
            self.model_wait_dialog.setWindowModality(Qt.ApplicationModal)
            self.model_wait_dialog.setMinimumDuration(0)
            self.model_wait_dialog.show()
            QApplication.processEvents()
            self.model_loader = ModelLoadWorker(self.recognizer.model_path)
            self.model_loader.loaded.connect(self._model_loaded)
            self.model_loader.failed.connect(self._model_load_failed)
            self.model_loader.start()
        except Exception as e:
            self.text_label.setText(f'❌ {e}')
            self.is_recording = False

    def _model_loaded(self, model):
        if self.model_wait_dialog:
            self.model_wait_dialog.close()
            self.model_wait_dialog = None
        if not self.recognizer:
            return
        self.recognizer.model = model
        self._finish_start_recording()

    def _model_load_failed(self, error):
        if self.model_wait_dialog:
            self.model_wait_dialog.close()
            self.model_wait_dialog = None
        self.is_recording = False
        self.text_label.setText(f'❌ {error}')

    def _finish_start_recording(self):
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        try:
            self.recognizer.start()
            if not self.recognizer.is_running:
                raise RuntimeError('Recognizer did not start')
            self.is_recording = True
            self.record_btn.setText(strings['stop'])
            self.record_btn.setStyleSheet('background:#c0392b;color:white;')
            self.text_label.setText(strings['recording'])
            if self.timer_seconds > 0 and self.timer_mode == 'off':
                self.start_timer()
        except Exception as e:
            self.is_recording = False
            self.text_label.setText(f'❌ {e}')

    def on_recognizer_error(self, error):
        self.is_recording = False
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.record_btn.setText(strings['start'])
        self.record_btn.setStyleSheet("background: #2c3e50; color: white;")
        self.text_label.setText(f'❌ Audio/recognition error: {error}')
        self.update_status_label()

    def on_recognizer_stopped(self):
        # Keep UI synchronized if the audio thread stops by itself.
        if self.is_recording and (not self.recognizer or not self.recognizer.is_running):
            self.is_recording = False
            strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
            self.record_btn.setText(strings['start'])
            self.record_btn.setStyleSheet("background: #2c3e50; color: white;")
            self.update_status_label()

    def stop_recording(self):
        if not self.is_recording:
            return
        if self.recognizer:
            self.recognizer.stop()
        self.is_recording = False
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.record_btn.setText(strings['start'])
        self.record_btn.setStyleSheet("background: #2c3e50; color: white;")
        self.text_label.setText(strings['stopped'])
        self.stop_timer()
        if self.timer_seconds > 0 and self.timer_mode == "on":
            self.start_timer()

    def execute_command(self, text):
        text_lower = text.lower().strip()
        text_clean = text.strip()
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])

        if self.current_lang == 'fa':
            if any(x in text_clean for x in ["تغییر انگلیسی", "انگلیسی کن", "برو انگلیسی"]) or \
               any(x in text_lower for x in ["change english", "switch to english", "english please"]):
                for i in range(self.lang_selector.count()):
                    if self.lang_selector.itemData(i) == 'en':
                        self.lang_selector.setCurrentIndex(i)
                        break
                self.text_label.setText(strings['cmd_lang_en'])
                return True
        if self.current_lang == 'en':
            if any(x in text_lower for x in [
                "persian", "farsi", "persian change", "farsi change",
                "change to persian", "change to farsi",
                "switch to persian", "switch to farsi", "go persian"
            ]):
                for i in range(self.lang_selector.count()):
                    if self.lang_selector.itemData(i) == 'fa':
                        self.lang_selector.setCurrentIndex(i)
                        break
                self.text_label.setText(strings['cmd_lang_fa'])
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
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.text_label.setText(strings['cmd_delete'])

    def cmd_copy(self):
        time.sleep(0.08)
        keyboard.press_and_release('ctrl+c')
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.text_label.setText(strings['cmd_copy'])

    def cmd_paste(self):
        time.sleep(0.08)
        keyboard.press_and_release('ctrl+v')
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.text_label.setText(strings['cmd_paste'])

    def cmd_enter(self):
        time.sleep(0.08)
        keyboard.press_and_release('enter')
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.text_label.setText(strings['cmd_enter'])

    def cmd_undo(self):
        time.sleep(0.08)
        keyboard.press_and_release('ctrl+z')
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.text_label.setText(strings['cmd_undo'])

    def update_text(self, text):
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        if self.execute_command(text):
            return
        try:
            keyboard.write(text + " ")
            self.text_label.setText(f"📝 {text}")
        except Exception as e:
            print(f"Type error: {e}")
            QApplication.clipboard().setText(text)
            self.text_label.setText(strings['clipboard_fallback'])

    # =====================
    #  مدیریت مدل‌ها
    # =====================
    def _dialog_parent(self):
        return self.model_manager_dialog if self.model_manager_dialog and self.model_manager_dialog.isVisible() else self

    def open_model_manager(self):
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        dialog = QDialog(self)
        self.model_manager_dialog = dialog
        dialog.setWindowTitle(strings['model_manager_title'])
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setMinimumSize(980, 620)
        dialog.setStyleSheet("""
            QDialog, QWidget {
                background: #1a1a2e;
                color: #ecf0f1;
            }
            QLabel {
                color: #ecf0f1;
            }
            QLineEdit, QTextEdit, QTableWidget {
                background: #20243a;
                color: #ecf0f1;
                border: 1px solid #444;
            }
            QHeaderView::section {
                background: #2c3e50;
                color: white;
                padding: 6px;
                border: 1px solid #444;
            }
            QTableWidget::item {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QTableWidget::item:selected {
                background: #4f86c6;
                color: white;
            }
            QPushButton {
                color: white;
                padding: 6px;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #2c3e50;
                color: white;
                padding: 8px 14px;
            }
            QTabBar::tab:selected {
                background: #4f86c6;
            }
        """)
        layout = QVBoxLayout(dialog)
        tabs = QTabWidget(dialog)

        download_tab = QWidget()
        dl = QVBoxLayout(download_tab)
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(strings['search_placeholder'])
        self.search_input.textChanged.connect(self.filter_models_table)
        self.search_input.setLayoutDirection(Qt.LeftToRight)
        search_row.addWidget(self.search_input)
        self.manager_internet_label = QLabel(strings['internet_status'].format(
            status=strings['online'] if self.is_online else strings['offline']
        ))
        self.manager_internet_label.setStyleSheet(f"color: {'#27ae60' if self.is_online else '#e74c3c'};")
        search_row.addWidget(self.manager_internet_label)
        refresh_btn = QPushButton(strings['refresh_models'])
        refresh_btn.setStyleSheet('background:#2980b9;')
        refresh_btn.clicked.connect(self.refresh_models_from_server)
        search_row.addWidget(refresh_btn)
        dl.addLayout(search_row)

        self.models_table = QTableWidget()
        self.models_table.setColumnCount(7)
        self.models_table.setHorizontalHeaderLabels([
            strings['model_name'], strings['size'], strings['language'],
            strings['license'], strings['notes'], strings['status'], strings['download']
        ])
        self.models_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.models_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.models_table.setAlternatingRowColors(False)
        self.models_table.setSortingEnabled(False)
        self.models_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.models_table.setLayoutDirection(Qt.LeftToRight)
        dl.addWidget(self.models_table)

        br = QHBoxLayout()
        download_selected_btn = QPushButton(strings['download_btn'])
        download_selected_btn.setStyleSheet('background:#27ae60;')
        download_selected_btn.clicked.connect(self.download_selected_models)
        br.addWidget(download_selected_btn)
        br.addStretch()
        close = QPushButton(strings['close_btn'])
        close.setStyleSheet('background:#c0392b;')
        close.clicked.connect(dialog.accept)
        br.addWidget(close)
        dl.addLayout(br)
        tabs.addTab(download_tab, '📥 ' + strings['download'])

        local_tab = QWidget()
        ll = QVBoxLayout(local_tab)
        group = QGroupBox(strings['add_local_model'])
        grid = QGridLayout(group)
        grid.addWidget(QLabel(strings['model_path']), 0, 0)
        self.local_path_input = QLineEdit()
        self.local_path_input.setLayoutDirection(Qt.LeftToRight)
        grid.addWidget(self.local_path_input, 0, 1)
        browse = QPushButton('📂 ' + strings['select_model_folder'])
        browse.setStyleSheet('background:#2980b9;')
        browse.clicked.connect(self.browse_model_folder)
        grid.addWidget(browse, 0, 2)

        grid.addWidget(QLabel(strings['model_lang']), 1, 0)
        self.local_lang_input = QLineEdit()
        self.local_lang_input.setPlaceholderText('fa, en, de, ...')
        self.local_lang_input.setLayoutDirection(Qt.LeftToRight)
        grid.addWidget(self.local_lang_input, 1, 1)
        add = QPushButton(strings['add_model'])
        add.setStyleSheet('background:#27ae60;')
        add.clicked.connect(self.add_local_model)
        grid.addWidget(add, 1, 2)
        ll.addWidget(group)
        ll.addStretch()
        tabs.addTab(local_tab, '📁 ' + strings['add_local_model'])

        help_tab = QWidget()
        hl = QVBoxLayout(help_tab)
        ht = QTextEdit()
        ht.setHtml(strings['help_text'])
        ht.setReadOnly(True)
        hl.addWidget(ht)
        tabs.addTab(help_tab, '❓ ' + strings['help_tab'])

        layout.addWidget(tabs)
        dialog.setLayoutDirection(Qt.RightToLeft if self.ui_lang == 'fa' else Qt.LeftToRight)
        self.populate_models_table()
        dialog.exec_()
        self.model_manager_dialog = None
        # Avoid keeping references to widgets that belong to a closed dialog.
        self.models_table = None
        self.search_input = None
        self.manager_internet_label = None
        self.local_path_input = None
        self.local_lang_input = None
        self.refresh_language_list()
        self.update_ui_texts()

    def populate_models_table(self):
        if not hasattr(self, 'models_table') or self.models_table is None:
            return
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self._merge_installed_into_catalog()
        installed = scan_installed_models()
        self.models_table.setRowCount(0)
        for model_name in sorted(self.models):
            info = self.models[model_name]
            row = self.models_table.rowCount()
            self.models_table.insertRow(row)
            name_item = QTableWidgetItem(model_name)
            name_item.setData(Qt.UserRole, model_name)
            self.models_table.setItem(row, 0, name_item)
            self.models_table.setItem(row, 1, QTableWidgetItem(info.get('size', '?')))
            self.models_table.setItem(row, 2, QTableWidgetItem(info.get('lang', '?')))
            self.models_table.setItem(row, 3, QTableWidgetItem(info.get('license', '')))
            notes = info.get('notes', '') or ''
            self.models_table.setItem(row, 4, QTableWidgetItem(notes[:120] + ('…' if len(notes) > 120 else '')))
            is_installed = model_name in installed
            is_downloading = model_name in self.downloaders and self.downloaders[model_name].isRunning()
            if is_installed:
                status_text = strings['downloaded']
                status_color = QColor(39, 174, 96)
            elif is_downloading:
                status_text = strings['downloading']
                status_color = QColor(241, 196, 15)
            else:
                status_text = strings['not_downloaded']
                status_color = QColor(231, 76, 60)
            st = QTableWidgetItem(status_text)
            st.setForeground(status_color)
            self.models_table.setItem(row, 5, st)
            box = QWidget()
            bl = QHBoxLayout(box)
            bl.setContentsMargins(2, 2, 2, 2)
            if is_installed:
                btn = QPushButton('🗑️')
                btn.setToolTip(strings['delete_model'])
                btn.setStyleSheet('background:#c0392b;')
                btn.clicked.connect(lambda _, n=model_name: self.delete_model(n))
            elif info.get('url'):
                btn = QPushButton('⬇️')
                btn.setToolTip(strings['download'])
                btn.setStyleSheet('background:#27ae60;')
                btn.clicked.connect(lambda _, n=model_name: self.download_single_model(n))
            else:
                btn = QPushButton('—')
                btn.setEnabled(False)
            bl.addWidget(btn)
            self.models_table.setCellWidget(row, 6, box)
        self.models_table.resizeRowsToContents()

    def filter_models_table(self):
        q = self.search_input.text().strip().lower()
        for row in range(self.models_table.rowCount()):
            hay = ' '.join((self.models_table.item(row, c).text() if self.models_table.item(row, c) else '') for c in range(6)).lower()
            self.models_table.setRowHidden(row, q not in hay)

    def refresh_models_from_server(self):
        if not self.is_online:
            QMessageBox.warning(
                self._dialog_parent(),
                UI_STRINGS[self.ui_lang]['model_manager_title'],
                '⚠️ ' + UI_STRINGS[self.ui_lang]['offline']
            )
            self.check_internet_async()
            return
        self.fetch_models_from_server()

    def download_single_model(self, model_name):
        info = self.models.get(model_name, {})
        if not info.get('url'):
            QMessageBox.warning(
                self._dialog_parent(),
                UI_STRINGS[self.ui_lang]['model_manager_title'],
                f'URL not available for {model_name}'
            )
            return
        self.start_model_download(model_name, info['url'])

    def download_selected_models(self):
        rows = self.models_table.selectionModel().selectedRows()
        strings = UI_STRINGS[self.ui_lang]
        if not rows:
            QMessageBox.information(
                self._dialog_parent(),
                strings['model_manager_title'],
                strings['no_selection']
            )
            return
        installed = get_installed_model_names()
        for selected in rows:
            item = self.models_table.item(selected.row(), 0)
            model_name = item.data(Qt.UserRole) if item else None
            if model_name and model_name not in installed:
                self.download_single_model(model_name)

    def start_model_download(self, model_name, url):
        strings = UI_STRINGS[self.ui_lang]
        if model_name in self.downloaders and self.downloaders[model_name].isRunning():
            return
        os.makedirs(MODEL_DIR, exist_ok=True)
        zip_path = os.path.join(MODEL_DIR, '.download-' + re.sub(r'[^A-Za-z0-9._-]', '_', model_name) + '.zip')
        dlg = QProgressDialog(
            strings['download_progress'].format(name=model_name),
            strings['cancel'], 0, 100, self._dialog_parent()
        )
        dlg.setWindowTitle(strings['model_manager_title'])
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setMinimumDuration(0)
        dlg.show()
        d = ModelDownloader(model_name, url, zip_path)
        self.downloaders[model_name] = d
        if hasattr(self, 'models_table') and self.models_table:
            self.populate_models_table()
        d.progress.connect(lambda cur, total, speed, p=dlg: self.update_download_progress(p, cur, total, speed))
        d.eta_updated.connect(lambda eta, p=dlg: self.update_download_eta(p, eta))
        d.finished.connect(lambda name, ok, msg, p=dlg: self.on_download_finished(p, name, ok, msg))
        dlg.canceled.connect(d.cancel)
        d.start()

    def update_download_progress(self, dlg, current, total, speed):
        strings = UI_STRINGS[self.ui_lang]
        if total > 0:
            dlg.setMaximum(100)
            dlg.setValue(min(100, int(current * 100 / total)))
            dlg.setLabelText(
                strings['downloaded_size'].format(
                    downloaded=format_size(current), total=format_size(total)
                ) + '\n' + strings['speed'].format(speed=speed)
            )
        else:
            dlg.setMaximum(0)
            dlg.setValue(0)
            dlg.setLabelText(
                strings['downloaded_size'].format(
                    downloaded=format_size(current), total='?'
                ) + '\n' + strings['speed'].format(speed=speed)
            )

    def update_download_eta(self, dlg, eta):
        strings = UI_STRINGS[self.ui_lang]
        base = dlg.labelText().split('\n⏱')[0]
        dlg.setLabelText(base + '\n' + strings['eta'].format(time=eta))

    def on_download_finished(self, dlg, model_name, success, msg):
        dlg.close()
        self.downloaders.pop(model_name, None)
        strings = UI_STRINGS[self.ui_lang]
        if success:
            self._merge_installed_into_catalog()
            self.refresh_language_list()
            self.populate_models_table()
            QMessageBox.information(
                self._dialog_parent(),
                strings['model_manager_title'],
                strings['download_finished']
            )
        elif msg != 'Cancelled':
            QMessageBox.critical(
                self._dialog_parent(),
                strings['model_manager_title'],
                strings['download_failed'].format(error=msg)
            )

    def delete_model(self, model_name):
        strings = UI_STRINGS[self.ui_lang]
        installed = scan_installed_models()
        meta = installed.get(model_name)
        if not meta:
            self.populate_models_table()
            return
        if QMessageBox.question(
            self._dialog_parent(), strings['delete_model'],
            strings['confirm_delete'].format(name=model_name),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) != QMessageBox.Yes:
            return
        try:
            if self.recognizer and self.current_lang == meta['lang']:
                self.stop_recording()
                self.recognizer = None
            path = os.path.abspath(meta['path'])
            safe_base = os.path.abspath(MODEL_DIR) + os.sep
            if not path.startswith(safe_base):
                raise PermissionError('External local models are not deleted from their original location.')
            shutil.rmtree(path)
            reg = _load_local_registry()
            reg.pop(model_name, None)
            _save_local_registry(reg)
            self.models.get(model_name, {}).update({'downloaded': False})
            self.refresh_language_list()
            self.populate_models_table()
        except Exception as e:
            QMessageBox.critical(self._dialog_parent(), strings['delete_model'], str(e))

    def browse_model_folder(self):
        p = QFileDialog.getExistingDirectory(
            self._dialog_parent(),
            UI_STRINGS[self.ui_lang]['select_model_folder']
        )
        if p:
            self.local_path_input.setText(p)

    def add_local_model(self):
        strings = UI_STRINGS[self.ui_lang]
        path = self.local_path_input.text().strip()
        lang = self.local_lang_input.text().strip().lower()
        if not path or not lang or not re.fullmatch(r'[a-z]{2,3}', lang):
            QMessageBox.warning(
                self._dialog_parent(),
                strings['add_local_model'],
                'Please select a valid model folder and language code.'
            )
            return
        if not _model_root_from_path(path):
            QMessageBox.critical(
                self._dialog_parent(),
                strings['add_local_model'],
                'Invalid Vosk model: am/final.mdl was not found.'
            )
            return
        wait = QProgressDialog(strings['wait_text'], '', 0, 0, self._dialog_parent())
        wait.setWindowTitle(strings['wait_title'])
        wait.setCancelButton(None)
        wait.setWindowModality(Qt.ApplicationModal)
        wait.show()
        QApplication.processEvents()
        self.model_importer = LocalModelImporter(path, lang)

        def done(name, code, ok, msg):
            wait.close()
            if ok:
                self.models.setdefault(name, {
                    'name': name, 'url': '', 'size': '?', 'size_bytes': 0,
                    'wer': '', 'notes': 'Local model', 'license': '', 'lang': code,
                    'downloaded': True
                })
                self.refresh_language_list()
                self.populate_models_table()
                QMessageBox.information(
                    self._dialog_parent(),
                    strings['add_local_model'],
                    f'✅ {name}'
                )
                self.local_path_input.clear()
                self.local_lang_input.clear()
            else:
                QMessageBox.critical(self._dialog_parent(), strings['add_local_model'], msg)

        self.model_importer.finished.connect(done)
        self.model_importer.start()

    # =====================
    #  سینی سیستم
    # =====================
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        tray_pixmap = create_app_icon(64, 64)
        self.tray_icon.setIcon(QIcon(tray_pixmap))
        menu = QMenu()
        strings = UI_STRINGS[self.ui_lang]
        self.tray_show_action = QAction(strings['tray_show'], self)
        self.tray_show_action.triggered.connect(self.show_window)
        self.tray_quit_action = QAction(strings['tray_quit'], self)
        self.tray_quit_action.triggered.connect(self.quit_app)
        menu.addAction(self.tray_show_action)
        menu.addAction(self.tray_quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def minimize_to_tray(self):
        self.hide()
        strings = UI_STRINGS.get(self.ui_lang, UI_STRINGS['en'])
        self.tray_icon.showMessage(strings['app_title'], strings['tray_message'], QSystemTrayIcon.Information, 2000)

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

# =============================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # تنظیم آیکون برنامه با استفاده از تابع مستقل
    app_icon = QIcon(create_app_icon(64, 64))
    app.setWindowIcon(app_icon)
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())