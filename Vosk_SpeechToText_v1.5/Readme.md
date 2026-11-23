# 🎤 Floating Speech-to-Text (Vosk + PyQt5)

Offline floating speech-to-text application with support for **Persian** and **English**.

Built with Vosk and PyQt5. Recognized text is typed automatically.

---

## ✨ Features

- Fully offline speech recognition (no internet required)
- Support for Persian and English languages
- Always-on-top floating window
- Language switch hotkey: `Ctrl + Shift + L`
- Voice commands for language switching
- Timer for automatic start/stop of recording
- Helpful voice commands:
  - `copy` / `ctrl c`
  - `paste` / `ctrl v`
  - `delete all` / `clear`
  - `enter` / `new line`
  - `undo` / `ctrl z`
- System tray support
- Draggable window

---

## 📦 Requirements

### 1. Install dependencies

```bash
pip install vosk sounddevice keyboard PyQt5

2. Vosk Models

Download the models and place them in one of these locations:
Text

models/
├── vosk-model-fa/
└── vosk-model-en-us/

Or next to the main script:
Text

vosk-model-fa/
vosk-model-en-us/

Download links:

    Persian: [vosk-model-fa](https://alphacephei.com/vosk/models)
    English: [vosk-model-en-us](https://alphacephei.com/vosk/models)

    Note: Folder names must match exactly (vosk-model-fa and vosk-model-en-us).

🚀 Run
Bash

python main.py

⌨️ Hotkeys & Voice Commands
Action	How
Start / Stop recording	Microphone button
Switch language	Ctrl + Shift + L
Switch to English (when Persian)	Say: «تغییر انگلیسی»
Switch to Persian (when English)	Say: persian / farsi / persian change
Copy	Say: copy
Paste	Say: paste
Delete all	Say: delete all or clear
Enter	Say: enter
Undo	Say: undo
⚙️ Timer

    Use + and − buttons to set the timer.
    Off mode: Stops recording when timer ends.
    On mode: Starts recording when timer ends.

🛠️ Troubleshooting

After stopping, it won't start again
Current version uses thread.join and a lock to fix this issue. Fully close and reopen the app if needed.

Model not found
Make sure the model folder contains am/final.mdl and is in the correct path.

Microphone not working
Check Windows microphone permissions and default input device.
📁 Suggested Project Structure
Text

SpeechApp/
├── main.py
├── models/
│   ├── vosk-model-fa/
│   └── vosk-model-en-us/
├── README.md
└── README_F.md

📝 Notes

    Completely offline
    Best results in a quiet environment
    Smaller models are recommended for better speed