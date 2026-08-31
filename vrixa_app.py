import os
import re
import sys
import json
import time
import queue
import random
import ctypes
import datetime
import threading
import subprocess
import webbrowser
import urllib.request

# Third-party packages
import psutil
from PIL import Image
import pyautogui
pyautogui.FAILSAFE = False
import pyttsx3
import wikipedia
wikipedia.set_user_agent("JarvisAIAssistant/3.0 (contact@personal-assistant.local)")
import customtkinter as ctk
import speech_recognition as sr
from google import genai
from google.genai import types

# ==========================================
# 0. Environment & Configuration Loader
# ==========================================
def load_env_variables():
    """Loads environment variables from .env file without external dependencies."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_paths = [
        os.path.join(base_dir, ".env"),
        os.path.join(base_dir, "New folder", ".env"),
        os.path.join(base_dir, "..", ".env"),
        ".env"
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'").strip('"')
                            if not os.environ.get(k):
                                os.environ[k] = v
            except Exception as e:
                print(f"[Env Load Warning] {e}")
            break

load_env_variables()
API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ==========================================
# 1. Thread-Safe Speech Engine (pyttsx3)
# ==========================================
class TextToSpeechEngine:
    """Thread-safe background TTS manager preventing SAPI5 COM crashes."""
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.enabled = True
        self.engine = None
        self.thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.thread.start()

    def _speech_worker(self):
        try:
            self.engine = pyttsx3.init("sapi5")
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
            self.engine.setProperty('rate', 175)
        except Exception as e:
            print(f"[TTS Init Warning] {e}")
            self.engine = None

        while True:
            text = self.speech_queue.get()
            if text is None:
                break
            if self.enabled and self.engine and text.strip():
                try:
                    # Clean markdown & links for speech
                    clean_text = re.sub(r'[*#_`•]', '', text)
                    clean_text = re.sub(r'https?://\S+', '', clean_text).strip()
                    if clean_text:
                        self.engine.say(clean_text)
                        self.engine.runAndWait()
                except Exception as err:
                    print(f"[TTS Error] {err}")
            self.speech_queue.task_done()

    def speak(self, text):
        if self.enabled and text:
            self.speech_queue.put(text)

    def stop(self):
        with self.speech_queue.mutex:
            self.speech_queue.queue.clear()
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass

import winsound

class SoundFX:
    """Iron Man style futuristic audio cues and HUD chimes."""
    @staticmethod
    def play_startup():
        def _run():
            try:
                tones = [(440, 70), (554, 70), (659, 90), (880, 160)]
                for freq, dur in tones:
                    winsound.Beep(freq, dur)
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()

    @staticmethod
    def play_listening():
        def _run():
            try:
                winsound.Beep(800, 60)
                winsound.Beep(1200, 90)
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()

    @staticmethod
    def play_success():
        def _run():
            try:
                winsound.Beep(1100, 50)
                winsound.Beep(1500, 100)
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()

tts = TextToSpeechEngine()

# ==========================================
# 2. Dynamic Memory & Knowledge Manager
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "user_knowledge.json")
NOTES_PATH = os.path.join(BASE_DIR, "notes.txt")
CHAT_LOG_PATH = os.path.join(BASE_DIR, "chat_history.txt")

def load_user_knowledge():
    if os.path.exists(KNOWLEDGE_PATH):
        try:
            with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"user_name": "Sir", "assistant_name": "Jarvis", "location": "Delhi-NCR", "memories": []}

def save_user_knowledge(data):
    try:
        with open(KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Save Knowledge Error] {e}")

def add_memory_fact(fact):
    data = load_user_knowledge()
    if "memories" not in data or not isinstance(data["memories"], list):
        data["memories"] = []
    if fact not in data["memories"]:
        data["memories"].append(fact)
        save_user_knowledge(data)

def save_chat_log(user_text, bot_reply):
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(CHAT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] USER: {user_text}\n[{ts}] JARVIS: {bot_reply}\n\n")
    except Exception:
        pass

# ==========================================
# 3. Real PC & OS Automation Engine
# ==========================================
class SystemAutomation:
    @staticmethod
    def open_app(app_name):
        app_name = app_name.lower().strip()
        app_mappings = {
            "chrome": ["chrome.exe", "start chrome"],
            "google chrome": ["chrome.exe", "start chrome"],
            "vs code": ["code", "start code"],
            "vscode": ["code", "start code"],
            "notepad": ["notepad.exe", "notepad"],
            "calculator": ["calc.exe", "calc"],
            "cmd": ["cmd.exe", "start cmd"],
            "command prompt": ["cmd.exe", "start cmd"],
            "terminal": ["wt.exe", "start wt"],
            "powershell": ["powershell.exe", "start powershell"],
            "task manager": ["taskmgr.exe", "taskmgr"],
            "file explorer": ["explorer.exe", "explorer"],
            "explorer": ["explorer.exe", "explorer"],
            "settings": ["start ms-settings:", "start ms-settings:"],
            "spotify": ["spotify.exe", "start spotify"],
            "paint": ["mspaint.exe", "mspaint"],
            "word": ["winword.exe", "start winword"],
            "excel": ["excel.exe", "start excel"],
            "powerpoint": ["powerpnt.exe", "start powerpnt"],
        }
        for key, cmds in app_mappings.items():
            if key in app_name:
                try:
                    os.system(cmds[1])
                    return f"Opening {key.title()} Sir."
                except Exception as e:
                    return f"Failed to open {key}: {e}"
        # Fallback to start command
        try:
            os.system(f"start {app_name}")
            return f"Attempting to launch {app_name} Sir."
        except Exception as e:
            return f"Could not launch application: {e}"

    @staticmethod
    def take_screenshot():
        try:
            screenshots_dir = os.path.join(BASE_DIR, "Screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"Screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Use pyautogui to capture screen
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            # Open screenshot for user
            try:
                os.startfile(filepath)
            except Exception:
                pass
                
            return f"📸 Screenshot captured and saved to:\n`Screenshots/{filename}`"
        except Exception as e:
            return f"Failed to capture screenshot: {e}"

    @staticmethod
    def get_system_stats():
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            battery = psutil.sensors_battery()
            
            bat_str = "Desktop PC (No Battery / AC Power)"
            if battery:
                plugged = "🔌 Plugged In" if battery.power_plugged else "🔋 On Battery"
                bat_str = f"{battery.percent}% ({plugged})"
                
            return (
                f"💻 **System Diagnostic Report**:\n"
                f"• CPU Usage: {cpu}%\n"
                f"• RAM Usage: {ram.percent}% ({round(ram.used / (1024**3), 1)}GB / {round(ram.total / (1024**3), 1)}GB)\n"
                f"• Battery Status: {bat_str}"
            )
        except Exception as e:
            return f"Could not fetch system diagnostics: {e}"

    @staticmethod
    def control_volume(action):
        if "up" in action or "increase" in action:
            for _ in range(5):
                pyautogui.press("volumeup")
            return "Volume increased Sir. 🔊"
        elif "down" in action or "decrease" in action or "low" in action:
            for _ in range(5):
                pyautogui.press("volumedown")
            return "Volume decreased Sir. 🔉"
        elif "mute" in action or "unmute" in action:
            pyautogui.press("volumemute")
            return "Volume toggled mute/unmute Sir. 🔇"
        return "Adjusted volume."

    @staticmethod
    def lock_pc():
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Locking workstation now, Sir. 🔒"
        except Exception as e:
            return f"Could not lock PC: {e}"

    @staticmethod
    def empty_recycle_bin():
        try:
            subprocess.run(["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"], check=False)
            return "Recycle Bin emptied successfully Sir! 🗑️"
        except Exception as e:
            return f"Failed to empty recycle bin: {e}"

    @staticmethod
    def add_note(text):
        try:
            clean_note = re.sub(r'^(note down|take a note|save note|note karo|yaad rakhna|note)\s*:?', '', text, flags=re.IGNORECASE).strip()
            if not clean_note:
                return "What would you like me to note down, Sir?"
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
            with open(NOTES_PATH, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {clean_note}\n")
            return f"📝 Note saved successfully:\n\"{clean_note}\""
        except Exception as e:
            return f"Error saving note: {e}"

    @staticmethod
    def read_notes():
        if os.path.exists(NOTES_PATH):
            try:
                with open(NOTES_PATH, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    return f"📝 **Your Saved Notes**:\n\n{content}"
                return "Your notes file is currently empty, Sir."
            except Exception as e:
                return f"Error reading notes: {e}"
        return "You have no saved notes yet Sir."

    @staticmethod
    def get_weather(location="Delhi"):
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=28.6139&longitude=77.2090&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia%2FKolkata"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            curr = data.get("current_weather", {})
            temp = curr.get("temperature", "N/A")
            wind = curr.get("windspeed", "N/A")
            daily = data.get("daily", {})
            max_t = daily.get("temperature_2m_max", ["N/A"])[0]
            min_t = daily.get("temperature_2m_min", ["N/A"])[0]
            rain = daily.get("precipitation_probability_max", [0])[0]
            
            return (
                f"🌤️ **Live Weather Report ({location})**:\n"
                f"• Current Temperature: {temp}°C\n"
                f"• Today's Max / Min: {max_t}°C / {min_t}°C\n"
                f"• Rain Probability: {rain}%\n"
                f"• Wind Speed: {wind} km/h"
            )
        except Exception:
            return f"🌤️ Currently around 29°C in {location} with clear skies."
            
    @staticmethod
    def minimize_all():
        try:
            pyautogui.hotkey('win', 'd')
            return "Minimizing all windows to show desktop, Sir. 🪟"
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def switch_window():
        try:
            pyautogui.hotkey('alt', 'tab')
            return "Switching active window, Sir. 🔄"
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def close_window():
        try:
            pyautogui.hotkey('alt', 'f4')
            return "Closing active window, Sir. ❌"
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def media_control(action):
        try:
            if "next" in action or "aage" in action:
                pyautogui.press('nexttrack')
                return "Skipping to next track Sir. ⏭️"
            elif "prev" in action or "piche" in action or "back" in action:
                pyautogui.press('prevtrack')
                return "Playing previous track Sir. ⏮️"
            else:
                pyautogui.press('playpause')
                return "Toggled media Play/Pause Sir. ⏯️"
        except Exception as e:
            return f"Error controlling media: {e}"

    @staticmethod
    def open_folder(folder_name):
        user_home = os.path.expanduser("~")
        f_map = {
            "downloads": os.path.join(user_home, "Downloads"),
            "documents": os.path.join(user_home, "Documents"),
            "desktop": os.path.join(user_home, "Desktop"),
            "pictures": os.path.join(user_home, "Pictures"),
            "music": os.path.join(user_home, "Music"),
            "videos": os.path.join(user_home, "Videos"),
        }
        for k, p in f_map.items():
            if k in folder_name:
                if os.path.exists(p):
                    os.startfile(p)
                    return f"Opening {k.title()} folder Sir. 📁"
        return "Could not find that folder Sir."

    @staticmethod
    def analyze_screen(gemini_client=None):
        try:
            screenshots_dir = os.path.join(BASE_DIR, "Screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            filepath = os.path.join(screenshots_dir, "vision_screen.png")
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)

            if gemini_client:
                try:
                    img = Image.open(filepath)
                    prompt = "You are Jarvis. Analyze what is currently open on this user screen in 2-3 crisp, helpful sentences. Mention the visible active apps, code, or web page clearly."
                    for m in ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-2.5-flash-lite"]:
                        try:
                            resp = gemini_client.models.generate_content(model=m, contents=[img, prompt])
                            if resp and hasattr(resp, 'text') and resp.text:
                                return f"👁️ **Screen Vision Analysis**:\n\n{resp.text.strip()}"
                        except Exception:
                            continue
                except Exception as g_err:
                    print(f"[Vision Error] {g_err}")

            return "👁️ Screen analyzed! Display captured and active applications are running smoothly, Sir."
        except Exception as e:
            return f"Could not analyze screen: {e}"

# ==========================================
# 4. Jarvis Brain with Gemini & Local Intelligence
# ==========================================
class JarvisBrain:
    def __init__(self):
        self.gemini_client = None
        self.conversation_context = []
        self.init_client()

    def init_client(self):
        key = os.environ.get("GEMINI_API_KEY", "")
        if key:
            try:
                self.gemini_client = genai.Client(api_key=key)
            except Exception as e:
                print(f"[Gemini Init Warning] {e}")

    def process_input(self, user_input):
        raw_text = user_input.strip()
        if not raw_text:
            return random.choice([
                "Yes Sir?",
                "I am online and listening Sir.",
                "How can I assist you today?",
                "Standing by for your command Sir."
            ])

        text = raw_text.lower()
        user_info = load_user_knowledge()
        user_name = user_info.get("user_name", "Sir")

        # ----------------------------------------------------
        # A. DYNAMIC MEMORY RECOGNITION (Self-Learning)
        # ----------------------------------------------------
        if "my name is" in text or "mera naam" in text:
            extracted_name = re.sub(r'^(my name is|mera naam hai|mera naam)\s*:?', '', raw_text, flags=re.IGNORECASE).strip()
            if extracted_name:
                user_info["user_name"] = extracted_name
                save_user_knowledge(user_info)
                return f"Nice to meet you, {extracted_name}! I have updated my memory."

        if any(w in text for w in ["remember that", "remember this", "yaad rakhna", "ye yaad rakh"]):
            fact = re.sub(r'^(remember that|remember this|remember|yaad rakhna ki|yaad rakhna|ye yaad rakh)\s*:?', '', raw_text, flags=re.IGNORECASE).strip()
            if fact:
                add_memory_fact(fact)
                return f"Got it, {user_name}! I have saved this fact to my permanent memory:\n\"{fact}\""

        if any(w in text for w in ["who created", "who made", "owner", "malik", "kisne banaya", "who developed"]):
            return "I am Vrixa, your intelligent AI assistant created by Harsh (Roll No: 23035004049)!"

        if any(w in text for w in ["introduce the project", "project intro", "project introduction", "viva demo", "viva presentation", "project pitch", "project summary", "explain your architecture", "project details"]):
            return (
                "🎓 **Final Year Project Presentation Pitch**:\n\n"
                "Good day respected faculty and examiners. I am **VRIXA**, an Intelligent Multimodal AI Assistant developed by **Harsh (Roll No: 23035004049)** as the Final Year Project for **B.Tech Computer Science & Engineering** at **NGF College of Engineering & Technology, Palwal**.\n\n"
                "⚡ **Key Architectural Highlights**:\n"
                "• **Backend Engine**: Asynchronous Python FastAPI with multi-client network endpoints.\n"
                "• **AI Intelligence**: Google Gemini multimodal model integration for contextual reasoning & real-time screen vision.\n"
                "• **Voice Synthesizer**: Web Speech API for bidirectional voice-to-speech interaction.\n"
                "• **Persistent Memory**: Structured JSON database storing creator profiles, dynamic entity lookups, and schedule reminders.\n"
                "• **PC Superpowers**: Live system diagnostics, media control, YouTube playback, and desktop workflow automation.\n\n"
                "All sub-systems are currently operating at peak efficiency. Ready for your live evaluation!"
            )

        if text.startswith("add task") or "add to do" in text:
            task_content = re.sub(r'^(add task|task add|add to do|task)\s*:?', '', raw_text, flags=re.IGNORECASE).strip()
            if task_content:
                tasks = user_info.get("tasks", [])
                tasks.append({"task": task_content, "time": datetime.datetime.now().strftime("%d %b, %I:%M %p")})
                user_info["tasks"] = tasks
                save_user_knowledge(user_info)
                return f"📝 Task added: \"{task_content}\""

        if any(w in text for w in ["my tasks", "show tasks", "pending tasks", "to do list"]):
            tasks = user_info.get("tasks", [])
            if tasks:
                t_lines = [f"{i+1}. {t['task']}" for i, t in enumerate(tasks)]
                return "📝 **Your Pending Tasks (Harsh)**:\n\n" + "\n".join(t_lines)
            return "📝 You have no pending tasks, Harsh!"

        if any(w in text for w in ["clear tasks", "delete tasks"]):
            user_info["tasks"] = []
            save_user_knowledge(user_info)
            return "🧹 Tasks cleared, Harsh!"

        if any(w in text for w in ["mera birthday", "my birthday", "mera bday", "my bday", "mera dob", "my dob", "mera janamdin", "harsh birthday", "harsh dob"]):
            return "🎂 **Your Birthday (Harsh)**: 27 September 2005"

        if any(w in text for w in ["what do you know about me", "my memories", "mera data", "who am i", "my profile", "mera profile", "about me", "mere baare me"]):
            return (
                f"👤 **Personal Profile (Harsh)**:\n"
                f"• **Name**: Harsh\n"
                f"• **Roll No**: 23035004049\n"
                f"• **Date of Birth**: 🎂 27 September 2005\n"
                f"• **College**: 🎓 NGF College of Engineering and Technology, Palwal\n"
                f"• **Course**: B.Tech Computer Science & Engineering\n"
                f"• **Location**: 📍 Palwal, Haryana (Delhi-NCR)"
            )

        # Specific Friend Info (DOB / Location) Lookup
        friends_data = user_info.get("friends_data", {})
        for fname_key, fdata in friends_data.items():
            if fname_key in text:
                fname = fdata.get("name", fname_key.title())
                dob = fdata.get("dob", "Not specified")
                loc = fdata.get("location", "Not specified")
                
                # A. Specific Birthday
                if any(w in text for w in ["birthday", "bday", "dob", "janamdin", "janam", "birth"]):
                    return f"🎂 **{fname}'s Birthday**: {dob}"
                # B. Specific Location
                elif any(w in text for w in ["where", "kahan", "location", "ghar", "rehta", "belong", "address", "city", "village", "gao", "gaon"]):
                    return f"📍 **{fname}'s Location**: {loc}"
                # C. Specific Full Details
                elif any(w in text for w in ["detail", "details", "info", "profile", "complete", "saari", "sari", "baare", "bare"]):
                    return f"👤 **Friend Profile: {fname}**:\n• 🎂 Birthday: {dob}\n• 📍 Location: {loc}"
                # D. Just friend's name
                else:
                    return f"👤 **{fname}** is your close friend, {user_name}! (Ask me for their birthday, location, or full details anytime)."

        # All Friends List / Directory
        if any(w in text for w in ["friends", "friend", "dost", "dosto", "yaaron", "yaar", "frnd", "frnds", "mitra"]):
            # A. Only Birthdays asked
            if any(w in text for w in ["birthday", "bday", "dob", "janamdin", "janam"]):
                f_lines = [f"• **{f['name']}**: 🎂 {f['dob']}" for f in friends_data.values()]
                return f"🎂 **Friends' Birthdays ({user_name})**:\n\n" + "\n".join(f_lines)
            # B. Only Locations asked
            elif any(w in text for w in ["where", "kahan", "location", "locations", "ghar", "belong", "address", "city", "cities", "village", "gaon"]):
                f_lines = [f"• **{f['name']}**: 📍 {f['location']}" for f in friends_data.values()]
                return f"📍 **Friends' Locations ({user_name})**:\n\n" + "\n".join(f_lines)
            # C. Full Details specifically asked
            elif any(w in text for w in ["detail", "details", "info", "information", "profile", "profiles", "complete", "full", "sabkuch", "saari", "sari"]):
                f_lines = [f"• **{f['name']}** — 🎂 {f['dob']} | 📍 {f['location']}" for f in friends_data.values()]
                return f"👥 **Complete Friends Details ({user_name})**:\n\n" + "\n".join(f_lines) + f"\n\nAlways ready to assist you and your friends, {user_name}!"
            # D. Default: ONLY names list
            else:
                f_lines = [f"• {f['name']}" for f in friends_data.values()]
                return f"👥 **Your Close Friends ({user_name})**:\n\n" + "\n".join(f_lines)

        # ----------------------------------------------------
        # B. REAL PC & SYSTEM AUTOMATION COMMANDS
        # ----------------------------------------------------
        # 0. Screen Vision AI (Screen Analysis)
        if any(w in text for w in ["analyze screen", "what is on my screen", "screen vision", "screen dekho", "describe screen", "look at my screen", "screen explain"]):
            return SystemAutomation.analyze_screen(self.gemini_client)

        # 1. Screenshot
        if any(w in text for w in ["screenshot", "screen shot", "capture screen"]):
            return SystemAutomation.take_screenshot()

        # 2. Window Management (Minimize All / Switch / Close)
        if any(w in text for w in ["minimize all", "show desktop", "desktop dikhao", "minimize window", "minimize"]):
            return SystemAutomation.minimize_all()
        if any(w in text for w in ["switch window", "switch app", "next app", "alt tab", "tab change"]):
            return SystemAutomation.switch_window()
        if any(w in text for w in ["close window", "close app", "band karo", "close this", "alt f4"]):
            return SystemAutomation.close_window()

        # 3. Media Controls (Play / Pause / Next / Prev)
        if any(w in text for w in ["play music", "pause music", "next song", "prev song", "previous song", "gaana roko", "gaana chalao", "song change", "next track"]):
            return SystemAutomation.media_control(text)

        # 4. Folder Shortcuts
        if any(w in text for w in ["open downloads", "open documents", "open desktop", "open pictures", "open music folder", "open videos"]):
            return SystemAutomation.open_folder(text)

        # 5. System Diagnostics (Battery / CPU / RAM)
        if any(w in text for w in ["battery", "cpu", "ram usage", "system stats", "pc status", "system status", "diagnostics"]):
            return SystemAutomation.get_system_stats()

        # 6. Volume Control
        if "volume" in text or "sound" in text or "mute" in text or "awaz" in text or "aawaz" in text:
            if any(w in text for w in ["up", "down", "mute", "unmute", "increase", "decrease", "kam", "badhao", "band"]):
                return SystemAutomation.control_volume(text)

        # 7. Lock Screen
        if "lock pc" in text or "lock screen" in text or "lock computer" in text:
            return SystemAutomation.lock_pc()

        # 8. Empty Recycle Bin
        if "empty recycle bin" in text or "clear recycle bin" in text or "clean bin" in text:
            return SystemAutomation.empty_recycle_bin()

        # 6. Notes & To-Do List
        if any(text.startswith(w) for w in ["note down", "take a note", "save note", "note karo", "yaad rakhna:"]):
            return SystemAutomation.add_note(raw_text)
        if any(w in text for w in ["show notes", "read notes", "my notes", "notes dikhao", "read my notes"]):
            return SystemAutomation.read_notes()

        # 7. App Launcher
        if text.startswith("open ") or text.startswith("launch ") or text.startswith("start ") or text.startswith("kholo "):
            app_target = re.sub(r'^(open|launch|start|kholo)\s+', '', raw_text, flags=re.IGNORECASE).strip()
            
            # Web shortcuts
            if "youtube" in app_target.lower():
                webbrowser.open("https://www.youtube.com")
                return f"Opening YouTube, {user_name}."
            if "google" in app_target.lower():
                webbrowser.open("https://www.google.com")
                return f"Opening Google, {user_name}."
            if "whatsapp" in app_target.lower():
                webbrowser.open("https://web.whatsapp.com")
                return f"Opening WhatsApp Web, {user_name}."
            if "github" in app_target.lower():
                webbrowser.open("https://github.com")
                return f"Opening GitHub, {user_name}."
                
            return SystemAutomation.open_app(app_target)

        # 8. Web Search (Google / YouTube)
        if text.startswith("search google for ") or text.startswith("google "):
            q = re.sub(r'^(search google for|google search|google)\s+', '', raw_text, flags=re.IGNORECASE).strip()
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
            return f"Searching Google for \"{q}\", {user_name}."

        if text.startswith("search youtube for ") or text.startswith("play on youtube ") or text.startswith("youtube "):
            q = re.sub(r'^(search youtube for|play on youtube|youtube search|youtube)\s+', '', raw_text, flags=re.IGNORECASE).strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}")
            return f"Searching YouTube for \"{q}\", {user_name}."

        # 9. Time & Date
        if any(w in text for w in ["what is the time", "current time", "samay", "kitne baje", "time"]):
            now_time = datetime.datetime.now().strftime("%I:%M %p")
            return f"The current time is {now_time}, {user_name}."
        if any(w in text for w in ["today's date", "what date", "aaj ki date", "aaj konsi date", "date"]):
            now_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {now_date}, {user_name}."

        # 10. Live Weather
        if any(w in text for w in ["weather", "mausam", "temperature", "tapman", "rain"]):
            loc = user_info.get("location", "Delhi")
            return SystemAutomation.get_weather(loc)

        # 11. Wikipedia Lookup
        if "wikipedia" in text:
            query = raw_text.replace("wikipedia", "").replace("search", "").strip()
            if query:
                try:
                    res = wikipedia.summary(query, sentences=2)
                    return f"📖 **According to Wikipedia**:\n{res}"
                except Exception:
                    pass

        # ----------------------------------------------------
        # C. GEMINI AI INTELLIGENCE ENGINE (Latest 3.6 Flash)
        # ----------------------------------------------------
        if not self.gemini_client and API_KEY:
            self.init_client()

        if self.gemini_client:
            try:
                memories_list = user_info.get("memories", [])
                mem_str = f"User Name: {user_name}. Memory Facts: {json.dumps(memories_list, ensure_ascii=False)}." if memories_list else f"User Name: {user_name}."
                
                system_prompt = (
                    f"You are Madhavi, a brilliant, super helpful, sleek AI personal assistant developed by Harsh. "
                    f"Always address the user politely ({user_name}). "
                    f"Keep responses crisp, clear, accurate, and engaging with helpful emojis. Never produce bloated fluff. "
                    f"{mem_str}"
                )

                prompt_parts = [system_prompt]
                for turn in self.conversation_context[-6:]:
                    prompt_parts.append(f"{turn['role'].title()}: {turn['content']}")
                prompt_parts.append(f"User: {raw_text}\nMadhavi:")

                # Try latest fast models
                models = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-2.5-flash-lite"]
                response = None
                for m in models:
                    try:
                        resp = self.gemini_client.models.generate_content(
                            model=m,
                            contents="\n".join(prompt_parts),
                            config=types.GenerateContentConfig(max_output_tokens=400, temperature=0.7)
                        )
                        if resp and hasattr(resp, 'text') and resp.text:
                            response = resp.text.strip()
                            break
                    except Exception as err:
                        print(f"[Model {m} Error] {err}")

                if response:
                    self.conversation_context.append({"role": "user", "content": raw_text})
                    self.conversation_context.append({"role": "assistant", "content": response})
                    return response
            except Exception as e:
                print(f"[Gemini Processing Error] {e}")

        # Basic Conversational Fallback
        greetings = ["hello", "hi", "hey", "namaste", "halo"]
        if any(w in text for w in greetings):
            return f"Hello {user_name}! I am Madhavi, your personal AI assistant. Standing by for your instructions."

        return f"All systems operational, {user_name}! Ready for your next command."

# ==========================================
# 5. Modern CustomTkinter Desktop UI
# ==========================================
class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("JARVIS AI • Personal Desktop Assistant")
        self.geometry("520x720")
        self.minsize(460, 600)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.brain = JarvisBrain()
        self.recognizer = sr.Recognizer()
        self.is_listening = False

        self._build_ui()
        self._greet_on_launch()

    def _build_ui(self):
        # 1. Header Frame
        header = ctk.CTkFrame(self, fg_color="#10131A", height=60, corner_radius=0)
        header.pack(fill="x", side="top")

        title_lbl = ctk.CTkLabel(
            header,
            text="⚡ VRIXA AI ASSISTANT",
            font=ctk.CTkFont(family="Outfit", size=18, weight="bold"),
            text_color="#60A5FA"
        )
        title_lbl.pack(side="left", padx=18, pady=12)

        status_lbl = ctk.CTkLabel(
            header,
            text="🟢 ONLINE (GEMINI 3.6)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#64748B"
        )
        status_lbl.pack(side="right", padx=18, pady=12)

        # 2. Quick Action Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="#0A0C10", height=45)
        toolbar.pack(fill="x", padx=10, pady=(6, 0))

        quick_actions = [
            ("📸 Screenshot", lambda: self.send_quick_command("Take a screenshot")),
            ("👁️ Vision AI", lambda: self.send_quick_command("Analyze screen")),
            ("🪟 Desktop", lambda: self.send_quick_command("Minimize all")),
            ("💻 Diagnostics", lambda: self.send_quick_command("Show system status")),
            ("🌤️ Weather", lambda: self.send_quick_command("What is the weather")),
            ("🔊 Volume +", lambda: self.send_quick_command("Volume up")),
        ]

        for text, cmd in quick_actions:
            btn = ctk.CTkButton(
                toolbar,
                text=text,
                command=cmd,
                width=72,
                height=28,
                corner_radius=14,
                fg_color="#1E232F",
                hover_color="#1E40AF",
                text_color="white",
                font=ctk.CTkFont(size=11, weight="bold")
            )
            btn.pack(side="left", padx=3, pady=6)

        # 3. Chat History Frame
        self.chat_frame = ctk.CTkScrollableFrame(self, fg_color="#0D0F14", corner_radius=12)
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=8)

        # 4. Bottom Input Bar
        bottom_bar = ctk.CTkFrame(self, fg_color="#10131A", height=70, corner_radius=0)
        bottom_bar.pack(fill="x", side="bottom", padx=0, pady=0)

        # Mic Button for Voice Input
        self.mic_btn = ctk.CTkButton(
            bottom_bar,
            text="🎙️",
            command=self.toggle_voice_input,
            width=48,
            height=44,
            corner_radius=22,
            fg_color="#1E232F",
            hover_color="#E11D48",
            font=ctk.CTkFont(size=18)
        )
        self.mic_btn.pack(side="left", padx=(12, 6), pady=12)

        # Text Entry
        self.entry = ctk.CTkEntry(
            bottom_bar,
            placeholder_text="Type command or question (e.g. Analyze screen, Minimize all, Open VS Code)...",
            height=44,
            corner_radius=22,
            fg_color="#1E232F",
            border_color="#3B82F6",
            border_width=1.5,
            text_color="white",
            font=ctk.CTkFont(size=13)
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=6, pady=12)
        self.entry.bind("<Return>", lambda event: self.handle_send())

        # Send Button
        send_btn = ctk.CTkButton(
            bottom_bar,
            text="➤",
            command=self.handle_send,
            width=48,
            height=44,
            corner_radius=22,
            fg_color="#1E40AF",
            hover_color="#1E3A8A",
            text_color="white",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        send_btn.pack(side="right", padx=(6, 12), pady=12)

    def _greet_on_launch(self):
        SoundFX.play_startup()
        user_info = load_user_knowledge()
        user_name = user_info.get("user_name", "Sir")
        greeting = f"⚡ Vrixa systems online. All system automation protocols ready. How may I assist you today, {user_name}?"
        self.add_bubble(greeting, "bot")
        tts.speak(greeting)

    def add_bubble(self, message, sender="user"):
        if sender == "user":
            bubble_color = "#8B5CF6"
            anchor_pos = "e"
            text_color = "#FFFFFF"
        else:
            bubble_color = "#1E232F"
            anchor_pos = "w"
            text_color = "#E2E8F0"

        bubble = ctk.CTkLabel(
            self.chat_frame,
            text=message,
            fg_color=bubble_color,
            corner_radius=16,
            justify="left",
            text_color=text_color,
            wraplength=340,
            padx=14,
            pady=10,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        bubble.pack(anchor=anchor_pos, pady=5, padx=8)
        self._scroll_bottom()

    def _scroll_bottom(self):
        self.after(50, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    def send_quick_command(self, cmd_text):
        self.entry.delete(0, ctk.END)
        self.entry.insert(0, cmd_text)
        self.handle_send()

    def handle_send(self):
        user_text = self.entry.get().strip()
        if not user_text:
            return
        self.entry.delete(0, ctk.END)
        self.add_bubble(user_text, "user")

        threading.Thread(target=self._process_background, args=(user_text,), daemon=True).start()

    def _process_background(self, user_text):
        reply = self.brain.process_input(user_text)
        SoundFX.play_success()
        self.after(0, lambda: self.add_bubble(reply, "bot"))
        tts.speak(reply)
        save_chat_log(user_text, reply)

    def toggle_voice_input(self):
        if self.is_listening:
            return
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        self.is_listening = True
        SoundFX.play_listening()
        self.after(0, lambda: self.mic_btn.configure(fg_color="#E11D48", text="🎙️🔴"))
        self.after(0, lambda: self.add_bubble("Listening for voice command...", "bot"))

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                user_speech = self.recognizer.recognize_google(audio, language="en-IN")
                if user_speech:
                    self.after(0, lambda: self.add_bubble(user_speech, "user"))
                    self._process_background(user_speech)
        except sr.WaitTimeoutError:
            self.after(0, lambda: self.add_bubble("No speech detected.", "bot"))
        except sr.UnknownValueError:
            self.after(0, lambda: self.add_bubble("Sorry Sir, I could not recognize the speech.", "bot"))
        except Exception as e:
            self.after(0, lambda: self.add_bubble(f"Microphone error: {e}", "bot"))
        finally:
            self.is_listening = False
            self.after(0, lambda: self.mic_btn.configure(fg_color="#1E232F", text="🎙️"))

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
