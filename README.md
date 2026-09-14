# Vrixa AI Assistant

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Uvicorn](https://img.shields.io/badge/ASGI-Uvicorn-499848?style=flat-square&logo=gunicorn&logoColor=white)](https://www.uvicorn.org/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

An intelligent, multi-provider AI assistant engineered with an asynchronous Python FastAPI backend, a responsive cyber-themed HUD web dashboard, and a resilient multi-tier LLM failover orchestrator. Vrixa combines multimodal vision, bidirectional voice interactions, real-time system telemetry, and PC automation into a unified personal productivity platform.

---

## Overview

Vrixa is designed to address a fundamental limitation found in many AI assistant implementations: **single-point-of-failure reliance on a single LLM API**. When rate limits (HTTP 429), quota exhaustion, latency spikes, or service outages strike a single provider, standard assistants become unresponsive.

Vrixa resolves this by introducing an **intelligent multi-tier fallback architecture**:
- Incoming queries are evaluated against native local tools (system diagnostics, weather, desktop automation, personal schedules).
- Conversational and generative requests are dynamically routed through an automated cascade of top-tier cloud and local AI providers.
- If all cloud APIs become unreachable, Vrixa gracefully degrades to local daemon models or an offline knowledge engine, ensuring continuous operational availability.

In addition to intelligent query routing, Vrixa bridges cloud intelligence with the local operating system, offering hardware health monitoring, desktop automation, and camera/screen vision directly from a browser-based HUD.

---

## Key Features

### 1. Multi-AI Fallback Orchestration Engine
- **Cascading Failover**: Sequentially queries providers by priority: **Google Gemini** &rarr; **Groq Cloud** &rarr; **Anthropic Claude** &rarr; **OpenAI** &rarr; **Local Ollama** &rarr; **Offline Knowledge Base**.
- **Model Auto-Recovery**: If a specific model within a provider encounters quota limits, the router automatically cycles through compatible secondary models.
- **Key Rotation**: Supports comma-separated API keys for Google Gemini (`GEMINI_API_KEYS`) to balance traffic across multiple accounts.
- **Client & Server Key Configuration**: Keys can be configured globally on the server via environment variables or set on-the-fly per user in the Settings modal and cached in client `localStorage`.

### 2. Multimodal Vision & Image Analysis
- **Screen & Image Comprehension**: Accepts base64 image uploads or desktop screenshots alongside user prompts for visual question answering using Gemini Vision.
- **Remote / Local Screenshot Capture**: Native screenshot routine capturing full desktop frames with system telemetry overlays.

### 3. AI Image Generation (FLUX Engine)
- **High-Definition Synthesis**: Generates 1024x1024 high-res AI artwork directly from natural language prompts using the **FLUX.1** deep learning model.
- **Zero API Key Requirement**: 100% free, zero-config image synthesis with infinite quota and zero-cost operation.
- **Multilingual Intent Support**: Supports natural English (`generate image of...`, `draw a...`) and Hindi/Hinglish (`image banao`, `photo banao`, `tasveer banao`) voice and text triggers.
- **Interactive Cyber Card**: Generated images render directly in the Cyber HUD chat with full-screen expansion and instant one-click download.
- **Dedicated REST API**: Exposes `POST /api/generate-image` endpoint for external integrations.

### 4. Responsive Cyber HUD Web Interface
- **Mobile-First Responsive Layout**: Built with modern CSS custom properties, viewport-fit cover, and dynamic viewport units (`100dvh`) for seamless operation across desktop, tablet, and mobile devices.
- **Real-Time Audio Visualizer**: Canvas-based animated neon frequency visualizer responding to voice state.
- **Provider Status Chips**: Real-time visual indicators displaying the health and configuration status of each AI engine.
- **Session & Chat History Management**: Local session switching, new chat creation, and history persistence.

### 5. Bidirectional Voice Interaction
- **Speech Recognition**: Voice input powered by the Web Speech API with support for Indian English (`en-IN`) and bilingual queries.
- **Text-to-Speech (TTS)**: Clean synthesis of assistant replies using the native browser `speechSynthesis` engine with link and markdown stripping for clear audio output.

### 6. Live System Telemetry & Diagnostics
- Monitors hardware health in real-time via `psutil`:
  - CPU Utilization percentage
  - RAM memory usage (GB utilized vs. total available)
  - Storage disk availability
  - Battery percentage and power source (AC power vs. battery)

### 7. Desktop & OS Automation
- **App Launcher**: Opens local desktop software (VS Code, Google Chrome, Notepad, Calculator, Windows Terminal, Paint, Task Manager).
- **Audio Control**: System volume adjustment (volume up, volume down, mute/unmute) via `pyautogui`.
- **Security Lock**: Quick desktop workstation lock via Windows `ctypes` User32 API.

### 8. Built-in Local Tools & Quick Services
- **Weather Forecast**: Real-time meteorological data and rain probability for Palwal / Delhi-NCR via Open-Meteo API (no API key required).
- **Schedule & Calendar Store**: Structured event and birthday tracking with on-the-fly date parsing and reminders.
- **To-Do Task Checklist**: Voice- and text-driven task creation, listing, and clearing stored in persistent JSON storage.
- **Smart Web Actions**: Quick navigation to YouTube search, WhatsApp Web messaging, Gmail compose, and Indian e-commerce platforms (Amazon, Flipkart, Myntra, Meesho).
- **Instant Math Evaluator**: Safe local regex arithmetic evaluation for rapid calculations without LLM roundtrips.

### 9. Alternative Desktop GUI Client (`vrixa_app.py`)
- Independent dark-theme desktop application powered by **CustomTkinter**.
- Incorporates offline text-to-speech via `pyttsx3` (SAPI5), microphone voice recognition via `speech_recognition`, and futuristic system chimes via `winsound`.

---

## Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance asynchronous REST API and routing |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) | Production ASGI server running asynchronous event loops |
| **AI Image Generation** | [Pollinations AI (FLUX.1)](https://pollinations.ai/) | Zero-key high-resolution 1024x1024 text-to-image synthesis |
| **Primary AI Provider** | [Google GenAI SDK](https://github.com/googleapis/python-genai) | Gemini 3.6 Flash / 3.5 Flash multimodal reasoning and vision |
| **Cloud Fallback AI** | [Groq Cloud API](https://groq.com/) | Ultra-low latency Llama & Qwen inference via `httpx` |
| **Cloud Fallback AI** | [Anthropic Claude API](https://anthropic.com/) | Claude 3.5 Haiku high-accuracy reasoning |
| **Cloud Fallback AI** | [OpenAI API](https://openai.com/) | GPT-4o-mini conversational responses |
| **Local AI Provider** | [Ollama](https://ollama.com/) | Offline local model inference (Llama 3.2) on `localhost:11434` |
| **Offline Knowledge** | [Wikipedia API](https://pypi.org/project/wikipedia/) | Zero-cost encyclopedia lookups when cloud AI is unavailable |
| **System Automation** | `psutil`, `pyautogui`, `ctypes` | Hardware telemetry, audio volume control, workstation lock |
| **Image Processing** | [Pillow (PIL)](https://python-pillow.org/) | Screenshot capture, image resizing, and base64 transformations |
| **Frontend UI** | HTML5, Modern CSS3, JavaScript (ES6+) | Single-Page Application (SPA) Cyber HUD interface |
| **Voice / Audio** | Web Speech API | Bidirectional browser speech recognition and synthesis |
| **Desktop Client** | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), `pyttsx3`, `winsound` | Standalone Windows GUI client |
| **Weather API** | [Open-Meteo](https://open-meteo.com/) | Free real-time weather and precipitation forecasts |
| **Data Persistence** | JSON Storage | Persistent storage for user profile, schedules, and task lists |

---

## How It Works

### High-Level Request Flow

```
+-------------------------------------------------------------+
|                      User Interaction                       |
|         (Text Input, Voice Recognition, Image Upload)       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 FastAPI Backend (/api/chat)                 |
+-------------------------------------------------------------+
                              |
        +---------------------+---------------------+
        |                                           |
        v                                           v
+--------------------------------+  +--------------------------------+
|      Local Intent Matcher      |  |     Multi-AI Orchestrator      |
|  - System Hardware Stats       |  |  (If not handled by local)     |
|  - Live Weather Forecast       |  +--------------------------------+
|  - Desktop Automation (Volume) |                  |
|  - Task & Calendar Management  |                  v
|  - Math Evaluator & Web Links  |   Priority 1: Google Gemini Flash
+--------------------------------+                  | (on timeout/quota)
        |                                           v
        |                            Priority 2: Groq Cloud (Llama)
        |                                           | (on failure)
        |                                           v
        |                            Priority 3: Anthropic Claude
        |                                           | (on failure)
        |                                           v
        |                            Priority 4: OpenAI (GPT-4o)
        |                                           | (on failure)
        |                                           v
        |                            Priority 5: Local Ollama Daemon
        |                                           | (if offline)
        |                                           v
        |                            Priority 6: Offline Knowledge
        |                                        (Wikipedia Engine)
        |                                           |
        +---------------------+---------------------+
                              |
                              v
+-------------------------------------------------------------+
|                   Structured JSON Response                  |
|  { reply, provider, action_url, api_status, timestamp }     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      Client Web HUD                         |
|   - Chat bubble rendered with Markdown & provider badge     |
|   - Voice synthesizer speaks answer via Web Speech API      |
|   - Browser triggers action URL / media tab if required     |
+-------------------------------------------------------------+
```

---

## Project Structure

```
vrixa-ai-assistant/
│
├── .env.example               # Environment variables template with placeholders
├── .gitignore                 # Git ignore rules for environments, bytecode, logs
├── main.py                    # Application launcher: initializes network IP & web server
├── START_VRIXA.bat            # Windows 1-click batch launcher
├── requirements.txt           # Production Python dependencies for the web server
├── render.yaml                # Infrastructure-as-code deployment blueprint for Render
├── Procfile                   # Process file for cloud container process declaration
├── user_knowledge.json        # Persistent JSON store for profile, tasks, and calendar
├── vrixa_app.py               # Standalone CustomTkinter desktop GUI client
│
├── New folder/                # Core Web Application Package
│   ├── app.py                 # FastAPI backend: endpoints, intents, system tools
│   ├── ai_providers.py        # Multi-AI Fallback Orchestration Engine
│   ├── render.yaml            # Local service deployment reference
│   ├── requirements.txt       # Package dependency specification
│   ├── user_knowledge.json    # Application runtime knowledge database
│   ├── vrixa_assistant.py     # Desktop client module reference
│   ├── static/                # Static assets served by FastAPI
│   │   └── screenshots/       # Storage directory for captured desktop snapshots
│   └── templates/
│       └── index.html         # Responsive Cyber HUD Web Dashboard (HTML/CSS/JS)
│
├── vrixa-web/                 # Experimental React + Vite frontend client
│   ├── package.json           # Node.js project manifest
│   ├── vite.config.js         # Vite bundler configuration
│   ├── vercel.json            # Vercel static deployment manifest
│   └── src/                   # React components and services
│
└── Screenshots/               # Directory reserved for project showcase images
```

---

## Environment Variables

Create a `.env` file in the root directory by copying `.env.example`:

```bash
cp .env.example .env
```

| Variable | Required | Description | Default / Example |
| :--- | :---: | :--- | :--- |
| `GEMINI_API_KEY` | Optional* | Primary AI API key for Google Gemini models | `AIzaSy...` |
| `GEMINI_API_KEYS` | Optional | Comma-separated Gemini keys for auto-rotation | `key1,key2,key3` |
| `GROQ_API_KEY` | Optional* | API key for high-speed Groq Cloud inference | `gsk_...` |
| `CLAUDE_API_KEY` | Optional* | API key for Anthropic Claude models | `sk-ant-...` |
| `OPENAI_API_KEY` | Optional* | API key for OpenAI GPT models | `sk-...` |
| `OLLAMA_BASE_URL` | Optional | Host address for local Ollama daemon | `http://localhost:11434` |
| `OLLAMA_MODEL` | Optional | Default model for local Ollama inference | `llama3.2` |
| `PORT` | Optional | Port on which the Uvicorn web server listens | `8000` |
| `PYTHON_VERSION` | Optional | Target Python runtime for cloud deployment | `3.11.8` |

*\*Note: At least one AI API key or a local Ollama instance is recommended for online generative responses. If no keys are provided, Vrixa continues operating using native system tools, weather, diagnostics, and the Offline Knowledge Engine.*

---

## Installation & Setup

### Prerequisites
- **Python 3.11+** installed on your system ([python.org](https://www.python.org/downloads/))
- **Git** installed on your system ([git-scm.com](https://git-scm.com/))
- *(Optional)* [Ollama](https://ollama.com/) if you wish to run local offline models without third-party APIs.

### 1. Clone the Repository
```bash
git clone https://github.com/Harshcodes27/vrixa-ai-assistant.git
cd vrixa-ai-assistant
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and add your API credentials:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

---

## Running the Application

### Option A: Windows 1-Click Launcher
Double-click `START_VRIXA.bat` in the project root directory.

### Option B: Python Entry Point
```bash
python main.py
```
This script will:
1. Detect your local machine IP address on the Wi-Fi network.
2. Launch the Uvicorn ASGI server on `0.0.0.0:8000`.
3. Automatically open `http://127.0.0.1:8000` in your default web browser.
4. Display the LAN link (e.g., `http://192.168.1.X:8000`) so you can access the assistant from your smartphone on the same network.

### Option C: Direct Uvicorn CLI
```bash
uvicorn app:app --app-dir "New folder" --host 0.0.0.0 --port 8000 --reload
```

### Option D: Standalone Desktop GUI Client
To launch the CustomTkinter desktop window:
```bash
pip install customtkinter pyttsx3 speechrecognition
python vrixa_app.py
```

---

## Deployment

The repository includes native deployment definitions for [Render](https://render.com/).

### Deploying to Render via `render.yaml`

1. Push your repository to GitHub.
2. Sign in to the [Render Dashboard](https://dashboard.render.com/).
3. Select **New** &rarr; **Blueprint** and connect your GitHub repository.
4. Render will parse `render.yaml` with the following configuration:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --app-dir "New folder" --host 0.0.0.0 --port $PORT`
5. In the Render service dashboard, configure your environment variables under **Environment** (e.g., `GEMINI_API_KEY`, `GROQ_API_KEY`).

---

## Screenshots / Demo

*Add your UI screenshots or screen recordings below by placing images in the `Screenshots/` directory and referencing them here.*

| Cyber HUD Dashboard | System Diagnostics & Settings |
| :---: | :---: |
| ![Dashboard Screenshot](Screenshots/dashboard.png) | ![Diagnostics Screenshot](Screenshots/diagnostics.png) |

> **Live Demo**: *A live link can be added here once deployed (e.g. on Render).*

---

## Future Improvements

- [ ] **Repository Refactoring**: Consolidate application modules from `"New folder"` into a standardized `src/` or `app/` Python package.
- [ ] **Database Migration**: Migrate `user_knowledge.json` and in-memory session states to SQLite or PostgreSQL with an ORM (SQLAlchemy / SQLModel).
- [ ] **Authentication & Multi-User Support**: Add JWT-based user authentication to support isolated multi-tenant chat histories and personal knowledge bases.
- [ ] **Extensible Plugin / Tool Calling Architecture**: Convert PC automation functions into formal LLM function calling / tools.
- [ ] **Docker Containerization**: Add a multi-stage `Dockerfile` and `docker-compose.yml` for unified cross-platform deployment.

---

## Developer

**Harsh Hareprava**  
- **GitHub**: [@Harshcodes27](https://github.com/Harshcodes27)  
- **LinkedIn**: [Harsh Hareprava](https://www.linkedin.com/in/harshusuryavanshi/)  
- **Institution**: NGF College of Engineering & Technology, Palwal (B.Tech CSE)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
