[🇬🇧 English](README.md) | [🇮🇷 فارسی](README.fa.md)

# 🎤 Vosk Voice Typing – Speech-to-Text Keyboard & Research Workspace
**Version 5.0 Pro** · Real-time speech recognition that types directly into any application, searches the web, and builds structured study & research notes.

Works offline, supports 20+ languages, floats above all windows with a PiP dock, and includes smart timers, voice commands, custom macros, Notion/EndNote-style study notes, and a built-in model manager.

---

## ✨ Features
- ✅ **Real-time speech recognition using the Vosk engine** – no internet required after model setup
- 🌍 **Supports 20+ languages** (Persian, English, Russian, German, French, Spanish, Italian, Chinese, Arabic, Turkish, and more)
- 🖥️ **Floating window & PiP dock** – always on top, draggable, semi-transparent, with active language badge (`FA` / `EN`) and one-click / double-click controls
- 📓 **Study & Research Workspace (Notion + EndNote style)** – organize notes by topics/chapters, add Note, Heading, Quote, Citation/Reference, and Action/Task blocks with tags and sources, search live, and export to **Markdown (`.md`)** or **BibTeX (`.bib`)**
- 🔎 **Voice web search & punctuation** – search directly in browser (`search ...` / `google ...`) and insert punctuation/blocks (`period`, `comma`, `question mark`, `new line`, `new paragraph`, `bullet`)
- ⚙️ **Custom voice macros (`macros.json`)** – trigger `hotkey`, `url`, `command`, or `text` actions hands-free
- ⏱️ **Smart timer** – automatically start or stop recording after a set countdown (`Turn off` and `Turn on` modes)
- ⌨️ **Global hotkeys** (work even when the app is not in focus):
  - `Ctrl+Shift+S` → Start recording
  - `Ctrl+Shift+X` → Stop recording
  - `Ctrl+Shift+L` → Switch recognition language (cycle)
- 🗣️ **Voice commands** – control the app hands-free (`copy`, `paste`, `enter`, `delete all`, `undo`, `note ...`, `topic ...`, `citation ...`, `quote ...`, and language switching)
- 📥 **Built-in model manager** – download models from the Vosk server, add local models, delete unwanted ones
- 🌐 **Full bilingual UI (Persian / English)** – switch UI language and layout direction (`RTL` / `LTR`) across windows and dialogs
- 🔔 **System tray icon** – run in the background
- 🎨 **Modern dark theme** with rounded corners and transparency

---

## 📸 Screenshots
*(Add your own screenshots here and update the file paths accordingly)*

- **Floating window & PiP dock** showing status, timer, language selector, Notes, and Macros
- **Study & Research Workspace** with topic sidebar, tags, citations, and Markdown/BibTeX export
- **Built-in Model Manager** for downloading, adding local models, or deleting installed models

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7 or higher
- Required Python libraries: `vosk`, `PyQt5`, `sounddevice`, `keyboard`, `requests`

### Steps
1. **Clone the repository**
   ```bash
   git clone https://github.com/mahanneman/vosk-voice-typing.git
   cd vosk-voice-typing
   ```

2. **Install dependencies**
   ```bash
   pip install vosk PyQt5 sounddevice keyboard requests
   ```
   **Linux users:** You may need to install PortAudio first:
   ```bash
   sudo apt install portaudio19-dev python3-pyaudio
   ```

3. **Run the application**
   ```bash
   python vosk_stt_pro.py
   ```

---

## 🧭 How to Use

### First Run
The app scans for existing models in the `models/` folder (and project folder).
If no model is found, you'll see a message: `"No model found. Please download a model."`
Click the **"📥 Models"** button to open the model manager.

### Managing Models
In the model manager you can:
- Download official Vosk models from the list (requires internet).
- Add a local model by selecting its folder (containing `am/final.mdl`) and entering the language code (e.g., `fa` for Persian, `en` for English).
- Delete unwanted models (only those inside the `models/` folder can be removed).

After adding a model, select it from the recognition language dropdown in the main window.

### Start Recording
Click the **"🎤 Start"** button or press `Ctrl+Shift+S` (or double-click the floating PiP icon).
Recognised text is typed automatically into the currently focused application when **Auto type** is enabled.
If **Auto type** is disabled or typing fails in a restricted window, the text is copied to the clipboard instead.

### Stop Recording
Click **"⏹ Stop"** or press `Ctrl+Shift+X` (or double-click the floating PiP icon).

### Switch Language
Use the recognition language dropdown in the main window, press `Ctrl+Shift+L` to cycle through installed languages, or use the **UI Lang** selector to switch the interface language across windows.
You can also switch recognition language by voice: say `"persian"` or `"farsi"` (when in English mode), or `"انگلیسی کن"` / `"برو انگلیسی"` (when in Persian mode).

### Study & Research Workspace (Notion + EndNote Style)
Click **"📓 Research Notes"** to open the workspace:
- Create and switch between **Topics / Chapters** (`notes/research_notebooks.json`), or say `"topic <name>"` / `"مبحث جدید <نام>"`.
- Record structured entries by voice or form:
  - `"note <text>"` / `"یادداشت کن <متن>"` → Note block
  - `"citation <ref>"` / `"منبع <رفرنس>"` → Citation / Reference block
  - `"quote <text>"` / `"نکته مهم <متن>"` → Quote / Key Insight block
- Search across notes, tags, and sources, copy to clipboard, or export to **Markdown (`.md`)** and **BibTeX (`.bib`)**.

### Smart Timer
Set a countdown using the `+` and `−` buttons:
- **Turn off** mode – when the timer expires, recording stops.
- **Turn on** mode – when the timer expires, recording starts.

The timer runs in the background and its status is shown in the status bar.

### Voice Commands
While recording, say any of these phrases to execute the corresponding action:

| Command | Action |
| :--- | :--- |
| `copy` / `ctrl c` | Copy selected text |
| `paste` / `ctrl v` | Paste from clipboard |
| `enter` / `new line` | Press Enter |
| `delete all` / `clear` | Clear all text in the active field |
| `undo` / `ctrl z` | Undo the last action |
| `search ...` / `google ...` | Search phrase in browser |
| `note ...` / `topic ...` / `citation ...` / `quote ...` | Add note, create topic, save citation, or save quote |
| `period` / `comma` / `new paragraph` / `bullet` | Insert punctuation or formatting block |
| `persian` / `farsi` (when in English) | Switch recognition language to Persian |

---

## ⌨️ Global Hotkeys

| Hotkey | Action |
| :--- | :--- |
| `Ctrl+Shift+S` | Start recording |
| `Ctrl+Shift+X` | Stop recording |
| `Ctrl+Shift+L` | Cycle through available languages |

These hotkeys work globally – the app does not need to be in focus.

---

## 📦 Building an Executable (Optional)
You can create a standalone executable (Windows, Linux, macOS) with PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed vosk_stt_pro.py
```

---

## 🐧 Linux-Specific Notes
To access the microphone, ensure your user is in the `audio` group:
```bash
sudo usermod -a -G audio $USER
```
Some distributions may require additional packages:
```bash
sudo apt install python3-pyqt5 python3-pyqt5.qtsvg
```
If audio is not captured, check your default input device in system settings or use `pavucontrol`.

---

## 📂 Folder Structure
```text
vosk-voice-typing/
├── vosk_stt_pro.py          # Main application
├── README.md                # English documentation
├── README.fa.md             # Persian documentation
├── macros.json              # Voice macros configuration (created automatically)
├── models/                  # Downloaded & local Vosk models
└── notes/                   # Research notebooks & exported .md / .bib files
```

---

## 🌐 Downloading More Models
Official Vosk models are available at [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models).
After downloading a `.zip` file, extract it to a folder and use **"Add Local Model"** in the app to import it.

---

## 🤝 Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.
For bugs or feature requests, please create an issue.

## 📜 License
This project is licensed under the MIT License – see the `LICENSE` file for details.

## 👤 Author
**MA.AD.GH**  
[GitHub](https://github.com/mahanneman)

## 🙏 Acknowledgements
- The Vosk team for their excellent speech recognition engine
- `PyQt5`, `sounddevice`, `keyboard`, and `requests` libraries
