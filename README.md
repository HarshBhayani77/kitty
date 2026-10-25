# 🐱 Kitty AI - Desktop AI Companion & System Monitor

[![Live Web Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-7952ec?style=for-the-badge&logo=google-chrome&logoColor=white)](https://HarshBhayani77.github.io/kitty)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt-6-41cd52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

Kitty AI is a smart, interactive desktop pet and system companion built with Python and PyQt6. Featuring procedural QPainter vector animations, interactive conversational AI (Google Gemini, OpenAI, Claude, Local LLMs), and real-time hardware monitoring.

👉 **[Try the Live Web Demo in your Browser](https://HarshBhayani77.github.io/kitty)** *(Perfect for portfolios & live interactive previews!)*

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
├── KittyAI/              # Desktop Application (Python + PyQt6)
│   ├── assets/           # Pet frames, icons, sounds
│   ├── config/           # Default configurations
│   ├── core/             # AI manager, audio, system monitor, pet state
│   ├── database/         # SQLite database schema and manager
│   ├── features/         # Reminder, pomodoro, habit tracker, notes
│   ├── ui/               # PyQt6 windows, pet avatar, speech bubble, settings
│   ├── main.py           # Application entrypoint
│   └── requirements.txt  # Python package dependencies
├── docs/                 # Web Demo & Portfolio Website (GitHub Pages ready)
│   ├── index.html        # Interactive HTML5 Canvas showcase
│   ├── style.css         # Dark cyberpunk glassmorphism UI
│   └── kitty.js          # Vector Kitty math & Web Audio synthesis
├── run.bat               # Windows desktop app quick launcher
├── run.sh                # Linux/macOS desktop app quick launcher
└── README.md
```

---

## 🌐 Running the Web Demo Locally

To preview the portfolio web demo on your local machine:
```bash
python -m http.server 8000 --directory docs
```
Then open [http://localhost:8000](http://localhost:8000) in your web browser.

To deploy live on **GitHub Pages**:
1. Push your repository to GitHub.
2. In your repo, go to **Settings** → **Pages**.
3. Under **Build and deployment**, select source: **Deploy from a branch**.
4. Choose Branch: `main`, Folder: `/docs`, and click **Save**.
5. Your live demo will be published at `https://<your-username>.github.io/<repo-name>`!

---

## 📄 License

MIT License. Feel free to use and modify for your own desktop companion!
