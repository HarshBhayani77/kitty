# 🐱 Kitty AI - Desktop AI Companion & System Monitor

Kitty AI is a smart, interactive desktop pet and system companion built with Python and PyQt6. Featuring procedural QPainter vector animations, interactive conversational AI (Google Gemini, OpenAI, Claude, Local LLMs), and real-time hardware monitoring.

---

## ✨ Features

- **🐾 Interactive Desktop Pet**:
  - Transparent, borderless window with smooth drag-and-drop.
  - Spiky fluffy fur silhouette with smooth eye-tracking following the cursor.
  - Natural blinking, idle breathing, and state reactions.

- **📊 Hardware & System Snapshot (1st Click)**:
  - Single-click Kitty to reveal real-time hardware status:
    - **CPU**: Utilization %
    - **RAM**: Memory usage & percentage
    - **GPU**: Graphics card name & utilization % (via GPUtil)
    - **Disk**: Storage status %
    - **Battery**: Charge level & plugged-in state

- **💬 Conversational AI (2nd Click / Double Click)**:
  - Second-click or double-click opens the Meow Chat interface.
  - Supports **Google Gemini** (`gemini-2.5-flash`, `gemini-1.5-flash`, etc.), **OpenAI**, **Anthropic Claude**, and **Ollama / Local LLM**.
  - Contextual responses rendered in a modern speech bubble.

- **⚙️ Customization & Settings**:
  - Sizing slider and quick presets (Mini 40%, Tiny 50%, Small 65%, Normal 80%, Large 100%).
  - Configurable AI providers, model endpoints, and API keys.
  - Right-click context menu for quick controls, system inspection, settings, and exit.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ installed
- Windows, macOS, or Linux

### Running Kitty AI

#### On Windows:
Double-click `run.bat` or run:
```cmd
.\run.bat
```
*(The script will automatically set up the virtual environment, install dependencies, and launch Kitty).*

#### On Linux / macOS:
```bash
chmod +x run.sh
./run.sh
```

#### Manual Run:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r KittyAI/requirements.txt
python KittyAI/main.py
```

---

## 📁 Project Structure

```
├── KittyAI/
│   ├── assets/           # Pet frames, icons, sounds
│   ├── config/           # Default configurations
│   ├── core/             # AI manager, audio, system monitor, pet state
│   ├── database/         # SQLite database schema and manager
│   ├── features/         # Reminder, pomodoro, habit tracker, notes
│   ├── ui/               # PyQt6 windows, pet avatar, speech bubble, settings
│   ├── main.py           # Application entrypoint
│   └── requirements.txt  # Python package dependencies
├── run.bat               # Windows quick launcher
├── run.sh                # Linux/macOS quick launcher
└── README.md
```

---

## 📄 License

MIT License. Feel free to use and modify for your own desktop companion!
