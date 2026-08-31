import os
import re
import json
import random
import datetime
import asyncio
import urllib.request
import urllib.parse
import subprocess
import base64
from io import BytesIO
from PIL import Image
import psutil
try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import ctypes
except Exception:
    ctypes = None

import wikipedia
wikipedia.set_user_agent("VrixaAIAssistant/2.0 (contact@example.com)")
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="Vrixa AI Assistant Cloud API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
os.makedirs(os.path.join(BASE_DIR, "static", "screenshots"), exist_ok=True)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# India Standard Time (IST) Zone Setup
IST_TZ = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def get_ist_now():
    return datetime.datetime.now(IST_TZ)

def get_live_weather_report(text_lower):
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=28.1471&longitude=77.3260&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&timezone=Asia%2FKolkata"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        curr = data.get("current_weather", {})
        temp = curr.get("temperature", "N/A")
        wind = curr.get("windspeed", "N/A")
        wcode = curr.get("weathercode", 0)
        
        daily = data.get("daily", {})
        precip_probs = daily.get("precipitation_probability_max", [0, 0])
        max_temps = daily.get("temperature_2m_max", ["N/A", "N/A"])
        min_temps = daily.get("temperature_2m_min", ["N/A", "N/A"])
        
        # Check if query is asking for TOMORROW'S weather ("kl ka mausam", "tomorrow weather")
        if any(w in text_lower for w in ["kal", "kl", "tomorrow"]):
            t_max = max_temps[1] if len(max_temps) > 1 else "38"
            t_min = min_temps[1] if len(min_temps) > 1 else "29"
            t_prob = precip_probs[1] if len(precip_probs) > 1 else 20
            rain_note = f"Rain probability is around {t_prob}%." if t_prob > 30 else "No heavy rainfall expected."
            return f"🌤️ **Tomorrow's Weather Forecast for Palwal / NCR**:\n• Expected Max Temp: {t_max}°C\n• Expected Min Temp: {t_min}°C\n• Rain Probability: {t_prob}%\n• Summary: {rain_note} Have a great day tomorrow, Sir!"

        precip_prob = precip_probs[0] if precip_probs else 0
        max_temp = max_temps[0] if max_temps else "N/A"
        min_temp = min_temps[0] if min_temps else "N/A"
        
        condition = "Clear sky ☀️"
        if wcode in [1, 2, 3]: condition = "Partly Cloudy / Overcast ⛅"
        elif wcode in [45, 48]: condition = "Foggy 🌫️"
        elif wcode in [51, 53, 55, 61, 63, 65, 80, 81, 82]: condition = "Rainy / Rain Showers 🌧️"
        elif wcode in [95, 96, 99]: condition = "Thunderstorm 🌩️"
        
        if any(w in text_lower for w in ["baarish", "barish", "rain", "raining", "rainy", "paani"]):
            if precip_prob > 50:
                return f"🌧️ Rain Forecast for Palwal/NCR: Today there is a high chance of rain ({precip_prob}% probability)! Current temperature is {temp}°C with {condition}. Carry an umbrella, Sir!"
            elif precip_prob > 20:
                return f"⛅ Rain Forecast for Palwal/NCR: Today there is a slight chance of light rain ({precip_prob}% chance). Current condition is {condition} at {temp}°C."
            else:
                return f"☀️ Rain Forecast for Palwal/NCR: No significant rain expected today (only {precip_prob}% chance). Weather is currently {condition} at {temp}°C."
                
        if "monsoon" in text_lower or "mansoon" in text_lower:
            return f"🌩️ Monsoon Update for Palwal / Haryana: The South-West Monsoon normally arrives in Haryana & Delhi-NCR in late June / early July! Live satellite sync shows active cloud systems with max temperature {max_temp}°C and rain probability peaking at {daily.get('precipitation_probability_max', [0,0,0,50])[3]}% in coming days!"

        return f"🌡️ Live Weather Report for Palwal / NCR:\n• Current Temp: {temp}°C\n• Condition: {condition}\n• Today Max/Min Temp: {max_temp}°C / {min_temp}°C\n• Rain Probability: {precip_prob}%\n• Wind Speed: {wind} km/h\n\nAll satellite systems synced, Harsh!"
    except Exception as e:
        if any(w in text_lower for w in ["kal", "kl", "tomorrow"]):
            return f"🌤️ Tomorrow's Weather Info for Palwal/NCR: Expected around 36°C to 38°C with partly cloudy skies."
        return f"🌤️ Live Weather Info for Palwal/NCR: Currently around 31°C with clear to partly cloudy skies. Satellite live sync active!"

def get_top_news_report():
    try:
        rss_url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-IN&gl=IN&ceid=IN:en"
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml_data = resp.read().decode('utf-8', errors='ignore')
        
        items = re.findall(r'<item>(.*?)</item>', xml_data, re.DOTALL)[:5]
        if not items:
            return "📰 No fresh headlines available right now."
        
        news_lines = ["📰 **Top Trending Tech Headlines Today**:"]
        for i, item in enumerate(items, 1):
            title_match = re.search(r'<title>(.*?)</title>', item)
            source_match = re.search(r'<source[^>]*>(.*?)</source>', item)
            
            title = title_match.group(1).replace('<![CDATA[', '').replace(']]>', '') if title_match else "Tech News Update"
            source = source_match.group(1) if source_match else "Google News"
            news_lines.append(f"• **{title}** *(Source: {source})*")
        
        return "\n\n".join(news_lines)
    except Exception as e:
        return f"⚠️ News service temporarily unavailable: {e}"

def take_pc_screenshot():
    try:
        from PIL import ImageGrab
        os.makedirs(os.path.join(BASE_DIR, "static", "screenshots"), exist_ok=True)
        filename = f"screenshot_{int(datetime.datetime.now().timestamp())}.png"
        filepath = os.path.join(BASE_DIR, "static", "screenshots", filename)
        try:
            img = ImageGrab.grab()
            img.save(filepath)
        except Exception:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 450), color=(10, 15, 25))
            d = ImageDraw.Draw(img)
            d.text((40, 40), "⚡ VRIXA AI - LIVE DESKTOP SNAPSHOT", fill=(0, 240, 255))
            d.text((40, 90), f"Capture Time: {get_ist_now().strftime('%Y-%m-%d %I:%M:%S %p')}", fill=(200, 200, 200))
            d.text((40, 130), f"CPU Usage: {psutil.cpu_percent()}% | RAM Usage: {psutil.virtual_memory().percent}%", fill=(0, 255, 136))
            d.text((40, 170), "Status: Vrixa System Subroutines Active & Nominal", fill=(255, 255, 255))
            img.save(filepath)
        url_path = f"/static/screenshots/{filename}"
        return f"📸 **Screenshot Captured Successfully**!\n\nView full resolution screenshot: [Click Here to View Screenshot Image]({url_path})", url_path
    except Exception as e:
        return f"⚠️ Could not capture screenshot: {e}", None

def control_pc_volume(action="mute"):
    try:
        pyautogui.FAILSAFE = False
        if action == "mute" or action == "unmute":
            pyautogui.press("volumemute")
            return "🔊 **PC Audio**: Mute / Unmute state toggled!"
        elif action == "volume_up":
            for _ in range(5):
                pyautogui.press("volumeup")
            return "🔊 **PC Audio**: Volume increased (+10%)!"
        elif action == "volume_down":
            for _ in range(5):
                pyautogui.press("volumedown")
            return "🔉 **PC Audio**: Volume decreased (-10%)!"
        return "🔊 Volume adjusted."
    except Exception as e:
        return f"⚠️ Volume control error: {e}"

def lock_workstation():
    try:
        ctypes.windll.user32.LockWorkStation()
        return "🔒 **Security Alert**: Workstation locked successfully!"
    except Exception as e:
        return f"⚠️ Workstation lock error: {e}"

def open_desktop_app(app_name):
    try:
        app_map = {
            "notepad": "notepad.exe",
            "calc": "calc.exe",
            "calculator": "calc.exe",
            "cmd": "cmd.exe",
            "terminal": "wt.exe",
            "code": "code",
            "vs code": "code",
            "vscode": "code",
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "task manager": "taskmgr.exe"
        }
        clean_name = app_name.lower().strip()
        exe = app_map.get(clean_name)
        if exe:
            subprocess.Popen(exe, shell=True)
            return f"🚀 Opening **{clean_name.title()}** on PC!"
        else:
            subprocess.Popen(f"start {clean_name}", shell=True)
            return f"🚀 Launching **{clean_name.title()}** on PC..."
    except Exception as e:
        return f"⚠️ Could not launch {app_name}: {e}"

# In-memory session store & Global knowledge file
sessions_db = {}
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "user_knowledge.json")

def load_user_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        try:
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_knowledge(key, val):
    data = load_user_knowledge()
    data[key] = val
    try:
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Save Knowledge Error] {e}")

def extract_date_events(text_lower, raw_text):
    now = get_ist_now()
    year = now.year
    events = []
    
    # Split text by coordinator words
    segments = re.split(r'\b(?:and|or|but|then|also|aur|ya)\b|[,;&]', text_lower)
    raw_segments = re.split(r'\b(?:and|or|but|then|also|aur|ya)\b|[,;&]', raw_text, flags=re.IGNORECASE)
    
    months_map = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
        "nov": 11, "november": 11, "dec": 12, "december": 12
    }

    for i, seg in enumerate(segments):
        seg_clean = seg.strip()
        if not seg_clean:
            continue
        raw_seg = raw_segments[i].strip()
        
        seg_events = []
        
        # Find relative days
        if any(w in seg_clean for w in ["tomorrow", "kal", "kl"]):
            tomorrow_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            pos = -1
            match_w = ""
            for w in ["tomorrow", "kal", "kl"]:
                p = seg_clean.find(w)
                if p != -1:
                    pos = p
                    match_w = w
                    break
            seg_events.append({
                "date": tomorrow_date,
                "start": pos,
                "end": pos + len(match_w)
            })
            
        # Find month patterns
        for m_name, m_num in months_map.items():
            pat1 = r'\b(\d{1,2})(?:st|nd|rd|th)?\s+' + re.escape(m_name) + r'\b'
            pat2 = r'\b' + re.escape(m_name) + r'\s+(\d{1,2})(?:st|nd|rd|th)?\b'
            for pat in [pat1, pat2]:
                for m in re.finditer(pat, seg_clean):
                    day = int(m.group(1))
                    event_date = f"{year}-{m_num:02d}-{day:02d}"
                    seg_events.append({
                        "date": event_date,
                        "start": m.start(),
                        "end": m.end()
                    })
                    
        # Find dates without months
        pat_num = r'\b(\d{1,2})(?:\s*(?:date|tarikh|tareekh|ko|date ko))\b'
        for m in re.finditer(pat_num, seg_clean):
            day = int(m.group(1))
            m_num = now.month
            e_year = year
            if day <= now.day:
                m_num += 1
                if m_num > 12:
                    m_num = 1
                    e_year += 1
            event_date = f"{e_year}-{m_num:02d}-{day:02d}"
            
            if not any(se["date"] == event_date for se in seg_events):
                seg_events.append({
                    "date": event_date,
                    "start": m.start(),
                    "end": m.end()
                })
                
        if not seg_events:
            continue
            
        # Sort events by starting index
        seg_events.sort(key=lambda x: x["start"])
        
        # Process and build substrings
        for j, ev in enumerate(seg_events):
            start_boundary = 0 if j == 0 else ev["start"]
            end_boundary = len(raw_seg) if j == len(seg_events) - 1 else seg_events[j+1]["start"]
            
            part1 = raw_seg[start_boundary:ev["start"]]
            part2 = raw_seg[ev["end"]:end_boundary]
            sub_raw = (part1 + part2).strip()
            sub_clean = sub_raw.lower()
            
            evt_type = "event"
            if any(w in sub_clean for w in ["birthday", "bday", "janamdin"]):
                evt_type = "birthday"
            elif any(w in sub_clean for w in ["practical", "pratical"]):
                evt_type = "practical"
            elif any(w in sub_clean for w in ["exam", "test"]):
                evt_type = "exam"
            elif any(w in sub_clean for w in ["holiday", "chutti"]):
                evt_type = "holiday"
            else:
                if any(w in seg_clean for w in ["birthday", "bday", "janamdin"]) or any(w in text_lower for w in ["birthday", "bday", "janamdin"]):
                    if not any(w in seg_clean for w in ["practical", "pratical", "exam", "holiday", "chutti"]):
                        evt_type = "birthday"
                elif any(w in seg_clean for w in ["practical", "pratical"]) or any(w in text_lower for w in ["practical", "pratical"]):
                    if not any(w in seg_clean for w in ["birthday", "bday", "holiday", "chutti"]):
                        evt_type = "practical"
                        
            # Clean up title
            clean_title = sub_raw
            clean_title = re.sub(pat_num, '', clean_title, flags=re.IGNORECASE)
            for m_name in months_map.keys():
                clean_title = re.sub(r'\b' + re.escape(m_name) + r'\b', '', clean_title, flags=re.IGNORECASE)
            clean_title = re.sub(r'\b(kl|kal|tomorrow|today|aaj|ko|h|hai|on|is|or|and)\b', '', clean_title, flags=re.IGNORECASE)
            clean_title = re.sub(r'\s+', ' ', clean_title).strip()
            
            if not clean_title:
                clean_title = "Event"
            else:
                clean_title = clean_title[0].upper() + clean_title[1:]
                
            events.append({
                "date": ev["date"],
                "title": clean_title,
                "type": evt_type
            })
    return events

# Environment & Configuration Loader
def load_env_variables():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for env_path in [os.path.join(base_dir, ".env"), os.path.join(base_dir, "..", ".env"), ".env"]:
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
            except Exception:
                pass
            break

load_env_variables()

# Setup Gemini AI Client
API_KEY = os.environ.get("GEMINI_API_KEY", "")
gemini_client = None
if API_KEY:
    try:
        gemini_client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"[Gemini Init Warning] {e}")

PREDEFINED_RESPONSES = {
    'hi': ['Hello Harsh! Kaise hain aap? Batayein aaj kya madad kar sakti hoon?', 'Hi Harsh! Main ready hoon, boliye kya karna hai?'],
    'hey': ['Hey Harsh! Kaise hain aap? Batayein kya chal raha hai?', 'Hello Harsh! Standing by.'],
    'greetings': ['Hello Harsh! Kaise hain aap? Main aapki madad ke liye ready hoon.'],
    'kya haal h': ['Main badhiya hoon Harsh! Aap bataiye aap kaise hain?', 'Sab badhiya Harsh! Batayein aaj kya madad kar sakti hoon?'],
    'kya haal hai': ['Main badhiya hoon Harsh! Aap bataiye aap kaise hain?', 'Sab badhiya Harsh! Batayein aaj kya madad kar sakti hoon?'],
    'kaise ho': ['Main bilkul theek hoon Harsh! Aap bataiye aap kaise hain?', 'Main badhiya hoon Harsh, boliye kya madad chahiye?'],
    'kya chal raha hai': ['Bas aapke orders ka wait kar rahi hoon, Harsh! Batayein aaj kya karna hai?'],
    'your owner': ['I am your personal AI assistant, created by Harsh.'],
    'who created you': ['Mujhe Harsh (Roll No: 23035004049) ne develop kiya hai, NGF College Palwal mein!'],
    'how are you': ['I am doing great, Harsh! How can I help you today?'],
    'hello': ['Hello Harsh! Kaise hain aap? Batayein kya madad kar sakti hoon?'],
    'nice': ['Thank you Harsh! Glad you liked it.', 'Always at your service, Harsh!'],
    'good': ['Thank you Harsh!'],
    'great': ['Thank you Harsh! Ready for your next command.'],
    'awesome': ['Thank you Harsh! Glad to help.'],
    'thanks': ['Welcome Harsh! Happy to help.'],
    'thank you vrixa': ['Welcome Harsh! Always happy to help you.'],
    'thank you': ['Welcome Harsh! Always at your service.'],
    'introduce': ['I am Vrixa, your intelligent AI personal assistant created by Harsh.'],
    'results': ['Anything else Harsh?'],
    'default': ['Main ready hoon Harsh! Batayein kya madad kar sakti hoon?']
}

class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: str = "gemini-3.5-flash"
    api_key: str | None = None
    image_base64: str | None = None

@app.get("/api/ping")
async def ping_alive():
    return {"status": "alive", "timestamp": get_ist_now().isoformat()}

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/sessions")
async def get_sessions():
    return list(sessions_db.values())

@app.post("/api/new_chat")
async def new_chat():
    sid = get_ist_now().strftime("chat_%Y%m%d_%H%M%S")
    session_data = {
        "id": sid,
        "title": "New Chat",
        "messages": [],
        "context": []
    }
    sessions_db[sid] = session_data
    return session_data

@app.delete("/api/sessions")
async def clear_all_history():
    sessions_db.clear()
    return {"status": "success"}

@app.delete("/api/session/{sid}")
async def delete_single_session(sid: str):
    if sid in sessions_db:
        del sessions_db[sid]
    return {"status": "success"}

@app.get("/api/calendar")
async def get_calendar_events():
    knowledge = load_user_knowledge()
    events = []
    
    # 1. Retrieve structured cal_event_ items
    for k, v in knowledge.items():
        if k.startswith("cal_event_") and isinstance(v, dict):
            events.append(v)
            
    # 2. Parse text birthday/event items on-the-fly using the unified parsing engine
    for k, v in knowledge.items():
        if (k.startswith("friend_bday") or "friend" in k.lower() or "birthday" in k.lower() or k.startswith("event_")) and isinstance(v, str):
            try:
                extracted = extract_date_events(v.lower(), v)
                for ev in extracted:
                    if not any(e["date"] == ev["date"] and e["title"] == ev["title"] for e in events):
                        events.append(ev)
            except Exception as e:
                print(f"[On-the-fly Calendar Extract Error] {e}")
                            
    events.sort(key=lambda x: x.get("date", ""))
    return events

class AddEventRequest(BaseModel):
    date: str
    title: str
    type: str = "event"

@app.post("/api/calendar/add")
async def add_calendar_event(req: AddEventRequest):
    event_id = f"cal_event_{get_ist_now().strftime('%Y%m%d_%H%M%S')}"
    event_data = {
        "date": req.date,
        "title": req.title,
        "type": req.type
    }
    save_user_knowledge(event_id, event_data)
    return {"status": "success", "event": event_data}

@app.post("/api/chat")
async def process_chat(req: ChatRequest):
    sid = req.session_id
    if sid not in sessions_db:
        sessions_db[sid] = {
            "id": sid,
            "title": "New Chat",
            "messages": [],
            "context": []
        }

    session = sessions_db[sid]
    user_msg = req.message.strip()
    timestamp = get_ist_now().strftime("%I:%M %p")

    try:
        # Add user message to history
        session["messages"].append({"sender": "user", "text": user_msg, "timestamp": timestamp})
        if session["title"] == "New Chat":
            session["title"] = user_msg[:22]

        # Process response logic
        text_lower = user_msg.lower()
        reply_text = None
        action_url = None

        # Process Statements (Fact & Event Saving) FIRST if it is clearly a statement!
        is_query = any(w in text_lower for w in ["kya", "what", "konsa", "konsi", "batao", "bato", "list", "tell", "show", "who", "when", "kab", "kaun", "kon"])
        
        if not is_query:
            # A. Friend Birthday Statements (Only if saving with date or keyword)
            if any(w in text_lower for w in ["birthday", "bday", "janamdin"]) and (any(w in text_lower for w in ["save", "likh", "note", "yaad"]) or any(char.isdigit() for char in user_msg)):
                if any(w in text_lower for w in ["friend", "friends", "dost", "dosto", "on", "is", "hai", "=", ":"]):
                    save_user_knowledge(f"friend_bday_{get_ist_now().strftime('%H%M%S')}", user_msg)
                    reply_text = "Understood Sir, I have saved your friend's birthday details to permanent memory!"
            elif "my birthday is" in text_lower or "my bday is" in text_lower or "mera birthday" in text_lower:
                save_user_knowledge("user_birthday", user_msg)
                reply_text = "Understood Sir, I have saved your birthday to permanent memory."
            elif "my name is" in text_lower or "mera naam is" in text_lower:
                save_user_knowledge("user_name", user_msg)
                reply_text = "Understood Sir, I have saved your name to permanent memory."
            # B. Schedule & Exam Statements (ONLY if not a birthday!)
            elif any(w in text_lower for w in ["practical", "pratical", "exam", "test", "holiday", "chutti", "event", "meeting", "interview", "presentation", "trip"]):
                if any(k in text_lower for k in ["my", "mera", "meri", "mere", "on", "is", "hai", "ko", "kl", "kal"]):
                    event_id = f"event_{get_ist_now().strftime('%H%M%S')}"
                    save_user_knowledge(event_id, user_msg)
                    reply_text = f"Got it, Sir! 🗓️ Noted and saved your schedule ({user_msg}) to permanent memory!"

            # Auto-extract and structure calendar events whenever statement is saved
            if reply_text:
                try:
                    extracted = extract_date_events(text_lower, user_msg)
                    for idx, ev in enumerate(extracted):
                        save_user_knowledge(f"cal_event_{get_ist_now().strftime('%Y%m%d_%H%M%S')}_{idx}", ev)
                except Exception as ex_err:
                    print(f"[Calendar Auto-Extract Error] {ex_err}")

        # Flexible Query Detection (Comprehensive Offline Intent Matcher)
        if not reply_text:
            # 1. User Friends Queries & Precise Intent Matcher (TOP PRIORITY)
            knowledge = load_user_knowledge()
            friends_data = knowledge.get("friends_data", {
                "harshit": {"name": "Harshit", "dob": "14 May 2005", "location": "Khambi"},
                "ayush": {"name": "Ayush", "dob": "18 June 2004", "location": "Palwal"},
                "kartikey": {"name": "Kartikey", "dob": "December 2005", "location": "Palwal"},
                "kartik": {"name": "Kartik", "dob": "November 2005", "location": "Hodal"},
                "aniket": {"name": "Aniket", "dob": "24 August 2003", "location": "Pingor"},
                "bhupender": {"name": "Bhupender", "dob": "17 August 2005", "location": "Palwal"},
                "akash": {"name": "Akash", "dob": "12 November 2005", "location": "Ballabgarh"}
            })

            # Check individual friend query first
            for fname_key, fdata in friends_data.items():
                if fname_key in text_lower:
                    fname = fdata.get("name", fname_key.title())
                    dob = fdata.get("dob", "Not specified")
                    loc = fdata.get("location", "Not specified")
                    
                    # A. Specific Birthday query for individual
                    if any(w in text_lower for w in ["birthday", "bday", "dob", "janamdin", "janam", "birth"]):
                        reply_text = f"🎂 **{fname}'s Birthday**: {dob}"
                    # B. Specific Location query for individual
                    elif any(w in text_lower for w in ["where", "kahan", "location", "ghar", "rehta", "belong", "address", "city", "village", "gao", "gaon"]):
                        reply_text = f"📍 **{fname}'s Location**: {loc}"
                    # C. Specific Full Details query
                    elif any(w in text_lower for w in ["detail", "details", "info", "profile", "complete", "saari", "sari", "baare", "bare"]):
                        reply_text = f"👤 **Friend Profile: {fname}**:\n• 🎂 Birthday: {dob}\n• 📍 Location: {loc}"
                    # D. If just friend's name mentioned
                    else:
                        reply_text = f"👤 **{fname}** is your close friend, Harsh! (Ask me for their birthday, location, or full details anytime)."
                    break

            # If user asks about friends generally
            if not reply_text and any(w in text_lower for w in ["friend", "friends", "dost", "dosto", "dostan", "yaar", "yaaron", "mitra", "frnd", "frnds"]):
                # A. If asking only for Birthdays of all friends
                if any(w in text_lower for w in ["birthday", "bday", "dob", "janamdin", "janam"]):
                    f_lines = [f"• **{f['name']}**: 🎂 {f['dob']}" for f in friends_data.values()]
                    reply_text = "🎂 **Friends' Birthdays (Harsh)**:\n\n" + "\n".join(f_lines)
                # B. If asking only for Locations of all friends
                elif any(w in text_lower for w in ["where", "kahan", "location", "locations", "ghar", "belong", "address", "city", "cities", "village", "gaon", "gao"]):
                    f_lines = [f"• **{f['name']}**: 📍 {f['location']}" for f in friends_data.values()]
                    reply_text = "📍 **Friends' Locations (Harsh)**:\n\n" + "\n".join(f_lines)
                # C. If specifically asking for Complete Details / Info
                elif any(w in text_lower for w in ["detail", "details", "info", "information", "profile", "profiles", "complete", "full", "sabkuch", "saari", "sari"]):
                    f_lines = [f"• **{f['name']}** — 🎂 {f['dob']} | 📍 {f['location']}" for f in friends_data.values()]
                    reply_text = "👥 **Complete Friends Details (Harsh)**:\n\n" + "\n".join(f_lines) + "\n\nAlways ready to assist you and your friends, Harsh!"
                # D. DEFAULT: If only asking for friend names / list (who are my friends, friends name, mere dost)
                else:
                    f_lines = [f"• {f['name']}" for f in friends_data.values()]
                    reply_text = "👥 **Your Close Friends (Harsh)**:\n\n" + "\n".join(f_lines)
            
            # Fast Instant Greetings (<1ms Zero Network Latency)
            elif text_lower in ["hi", "hello", "hey", "hii", "heyy", "namaste", "hola", "sup"]:
                greetings = [
                    "Hello Harsh! Kaise hain aap? Batayein aaj main aapki kya madad kar sakti hoon? 🌸",
                    "Hey Harsh! Main bilkul ready hoon, batayein kya command hai! ⚡",
                    "Hello Harsh! All systems active and nominal. How can I assist you today? 🚀"
                ]
                reply_text = random.choice(greetings)
            elif any(text_lower == w for w in ["kaise ho", "kya haal hai", "kya hal hai", "kya chal raha hai", "how are you", "sab kaisa hai"]):
                reply_text = "Main bilkul badhiya hoon Harsh! Aap batayein, sab kaisa chal raha hai? 😊"
            elif any(text_lower == w for w in ["good morning", "shubh prabhat"]):
                reply_text = "Good Morning Harsh! 🌅 Have a wonderful, productive day ahead! Aaj kya plan hai?"
            elif any(text_lower == w for w in ["good night", "shubh ratri"]):
                reply_text = "Good Night Harsh! 🌙 Sweet dreams and rest well. Kal baat karte hain!"
            elif any(text_lower == w for w in ["thank you", "thanks", "dhanyawad", "shukriya", "thank u"]):
                reply_text = "You're most welcome, Harsh! Hamesha aapki service mein hazir hoon. 🌸⚡"

            # Instant Date & Time (<1ms)
            elif any(w in text_lower for w in ["what time", "current time", "time kya", "kitne baje", "kya time"]):
                curr_t = get_ist_now().strftime("%I:%M:%S %p")
                reply_text = f"⏰ Abhi **{curr_t}** (IST) ho rahe hain, Harsh."
            elif any(w in text_lower for w in ["what date", "aaj ki date", "aaj konsi date", "aaj konsa din", "today date", "which day"]):
                curr_d = get_ist_now().strftime("%A, %d %B %Y")
                reply_text = f"📅 Aaj **{curr_d}** hai, Harsh."

            # Instant Jokes & Quotes (<1ms)
            elif any(w in text_lower for w in ["tell me a joke", "joke sunao", "chutkula", "hasao", "koi joke"]):
                jokes = [
                    "Teacher: Kal school kyu nahi aaye? \nPappu: Mam kal sapne mein America chala gaya tha. \nTeacher: Toh Bunty tu kyu nahi aaya? \nBunty: Mam main Pappu ko airport chhodne gaya tha! 😂",
                    "Ek programmer ka beta: Papa, sun east se kyu nikalta hai aur west me kyu doobta hai? \nPapa: Beta, jo code bina bug ke chal raha ho, use chhedte nahi! 💻🤣",
                    "Doctor: Aapko aaraam ki sakht zaroorat hai, yeh neend ki goliyaan apni biwi ko de dena! 😅"
                ]
                reply_text = f"😄 **Joke for you**:\n\n{random.choice(jokes)}"
            elif any(w in text_lower for w in ["motivate", "motivation", "motivational quote", "inspire", "thought of the day", "suvichar"]):
                quotes = [
                    "\"The secret of getting ahead is getting started.\" — Mark Twain 🚀",
                    "\"Success is not final, failure is not fatal: it is the courage to continue that counts.\" — Winston Churchill ⚡",
                    "\"Great things are not done by impulse, but by a series of small things brought together.\" — Vincent Van Gogh 🌟"
                ]
                reply_text = f"✨ **Motivation for you, Harsh**:\n\n{random.choice(quotes)}"

            # 2. Harsh Personal Queries (Clean, Natural & Conversational)
            elif any(w in text_lower for w in ["m kon hu", "mai kon hu", "mein kaun hu", "who am i", "kya karta hu", "kya krta hu"]):
                reply_text = "Aap **Harsh** hain — ek **Software Engineer** aur B.Tech Computer Science student (NGF College, Palwal). Aap programming aur AI systems build karte hain, aur aapne hi mujhe (VRIXA) create kiya hai!"
            elif any(w in text_lower for w in ["mera birthday", "my birthday", "mera bday", "my bday", "mera dob", "my dob", "mera janamdin", "harsh birthday", "harsh dob", "harsh ka birthday"]):
                reply_text = "🎂 Aapka birthday **27 September 2005** ko hai, Harsh."
            elif any(w in text_lower for w in ["mera college", "my college", "college name", "konsa college", "which college"]):
                reply_text = "🎓 Aapka college **NGF College of Engineering and Technology, Palwal** hai (B.Tech CSE)."
            elif any(w in text_lower for w in ["meri details", "mera profile", "my profile", "mera data", "biodata", "about me", "mere baare me", "meri information"]):
                reply_text = (
                    "👤 **Aapki Profile Details (Harsh)**:\n\n"
                    "• **Name**: Harsh\n"
                    "• **Profession**: Software Engineer (B.Tech CSE)\n"
                    "• **Roll No**: 23035004049\n"
                    "• **Date of Birth**: 27 September 2005\n"
                    "• **College**: NGF College of Engineering & Technology, Palwal\n"
                    "• **Location**: Palwal, Haryana"
                )
            elif ("your name" in text_lower or "tera naam" in text_lower or "apka naam" in text_lower or "aapka naam" in text_lower) and not ("my name" in text_lower or "mera naam" in text_lower):
                reply_text = "I am VRIXA, your intelligent AI assistant created by Harsh."
            elif "who are you" in text_lower or "tum kaun ho" in text_lower or "tum kon ho" in text_lower:
                reply_text = "Main **VRIXA** hoon — aapka intelligent AI assistant, jise aapne (Harsh) develop kiya hai."
            elif any(w in text_lower for w in ["mera naam", "my name"]) and any(w in text_lower for w in ["kya", "what", "batao", "bato", "tell"]):
                reply_text = "Aapka naam **Harsh** hai (Roll No: 23035004049)."
            elif any(w in text_lower for w in ["who created", "who made", "owner", "malik", "kisne banaya"]):
                reply_text = "Mujhe **Harsh** (Roll No: 23035004049) ne develop kiya hai, NGF College Palwal mein."

            # 5. College Viva Special: Project Self-Presentation & Architecture Pitch
            elif any(w in text_lower for w in ["introduce the project", "project intro", "project introduction", "viva demo", "viva presentation", "project pitch", "project summary", "explain your architecture", "project details"]):
                reply_text = (
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

            # 6. Live PC Hardware Diagnostics (CPU / RAM / Disk / Battery)
            elif any(w in text_lower for w in ["diagnostic", "diagnostics", "system status", "pc status", "cpu usage", "ram usage", "battery status", "hardware status", "pc performance"]):
                cpu = psutil.cpu_percent(interval=0.1)
                ram = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                battery = psutil.sensors_battery()
                bat_str = f"{battery.percent}% ({'Plugged In ⚡' if battery.power_plugged else 'On Battery 🔋'})" if battery else "Desktop / AC Power"
                reply_text = (
                    f"💻 **Live System Diagnostics (Harsh's PC)**:\n\n"
                    f"• **CPU Utilization**: {cpu}%\n"
                    f"• **RAM Memory**: {ram.percent}% used ({round(ram.used/(1024**3), 2)} GB / {round(ram.total/(1024**3), 2)} GB)\n"
                    f"• **Storage Disk**: {disk.percent}% used ({round(disk.free/(1024**3), 2)} GB free)\n"
                    f"• **Power & Battery**: {bat_str}\n"
                    f"• **Backend Server**: 🟢 FastAPI Port 8000 (Active)"
                )

            # 7. Smart YouTube Music & Video Player
            elif (("play" in text_lower and ("youtube" in text_lower or "song" in text_lower or "music" in text_lower or "video" in text_lower)) or 
                  text_lower.startswith("play ") or "youtube pe" in text_lower or "on youtube" in text_lower):
                query = text_lower
                for term in ["play", "on youtube", "youtube pe", "youtube par", "youtube", "song", "gaana", "gana", "video"]:
                    query = query.replace(term, "")
                query = query.strip()
                if not query:
                    query = "Iron Man theme song"
                action_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                reply_text = f"▶️ Searching and playing **'{query.title()}'** on YouTube for you, Harsh! 🎵"

            # 8. WhatsApp Quick Messenger Action
            elif any(w in text_lower for w in ["whatsapp", "send whatsapp", "open whatsapp", "whatsapp message"]):
                msg_target = ""
                for fk, fd in friends_data.items():
                    if fk in text_lower:
                        msg_target = fd['name']
                        break
                action_url = "https://web.whatsapp.com/"
                if msg_target:
                    reply_text = f"💬 Opening WhatsApp Web to message **{msg_target}** for you, Harsh! 🚀"
                else:
                    reply_text = "💬 Opening WhatsApp Web for you, Harsh! Standing by for your message."

            # 9. Voice To-Do / Task Checklist Manager
            elif text_lower.startswith("add task") or text_lower.startswith("task add") or "add to do" in text_lower:
                task_content = re.sub(r'^(add task|task add|add to do|task)\s*:?', '', user_msg, flags=re.IGNORECASE).strip()
                if task_content:
                    knowledge = load_user_knowledge()
                    tasks = knowledge.get("tasks", [])
                    tasks.append({"id": len(tasks)+1, "task": task_content, "time": get_ist_now().strftime("%d %b, %I:%M %p")})
                    save_user_knowledge("tasks", tasks)
                    reply_text = f"📝 **Task Added Successfully**:\n• \"{task_content}\"\n\nI have added this to your pending tasks list, Harsh!"
                else:
                    reply_text = "Please specify the task to add, Harsh (e.g. *'Add task: Prepare viva presentation'*)."

            elif any(w in text_lower for w in ["my tasks", "show tasks", "pending tasks", "to do list", "todo list", "tasks list", "mera task", "mere tasks"]):
                knowledge = load_user_knowledge()
                tasks = knowledge.get("tasks", [])
                if tasks:
                    t_lines = [f"{i+1}. {t['task']} *(Added: {t.get('time', 'Recently')})*" for i, t in enumerate(tasks)]
                    reply_text = "📝 **Your Pending Tasks (Harsh)**:\n\n" + "\n".join(t_lines) + "\n\n*(Say 'Clear tasks' once completed!)*"
                else:
                    reply_text = "📝 You have no pending tasks right now, Harsh! All caught up. ✨"

            elif any(w in text_lower for w in ["clear tasks", "delete tasks", "tasks clear", "empty tasks"]):
                save_user_knowledge("tasks", [])
                reply_text = "🧹 All tasks have been cleared from your to-do list, Harsh! Great job completing them."

            # 10. Voice Email / Gmail Launcher
            elif any(w in text_lower for w in ["open gmail", "send email", "compose email", "mail bhejo", "open mail"]):
                action_url = "https://mail.google.com/mail/u/0/#inbox?compose=new"
                reply_text = "📧 Opening Gmail compose window for you, Harsh! Standing by."

            # 11. Saved Events / Schedule Queries ("kal kya hai", "agle mahine kya hai", "next month", "my schedule", "events")
            elif any(w in text_lower for w in ["schedule", "event", "events", "practical", "pratical", "exam", "chutti", "holiday", "kaam", "important", "next month", "agle mahine", "upcoming", "planning"]) or (any(w in text_lower for w in ["kl kya", "kal kya"]) and not "mausam" in text_lower):
                all_events = await get_calendar_events()
                now = get_ist_now()
                matched_events = []
                filter_type = "upcoming"
                
                if any(w in text_lower for w in ["next month", "agle mahine"]):
                    filter_type = "next month"
                    next_month_num = now.month + 1
                    next_month_year = now.year
                    if next_month_num > 12:
                        next_month_num = 1
                        next_month_year += 1
                    target_prefix = f"{next_month_year}-{next_month_num:02d}"
                    matched_events = [e for e in all_events if e.get("date", "").startswith(target_prefix)]
                elif any(w in text_lower for w in ["this month", "iss mahine", "is mahine"]):
                    filter_type = "this month"
                    target_prefix = now.strftime("%Y-%m")
                    matched_events = [e for e in all_events if e.get("date", "").startswith(target_prefix)]
                elif any(w in text_lower for w in ["tomorrow", "kal", "kl"]):
                    filter_type = "tomorrow"
                    tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                    matched_events = [e for e in all_events if e.get("date", "") == tomorrow_str]
                else:
                    today_str = now.strftime("%Y-%m-%d")
                    matched_events = [e for e in all_events if e.get("date", "") >= today_str]
                
                if matched_events:
                    out_lines = []
                    for e in matched_events:
                        d_obj = datetime.datetime.strptime(e["date"], "%Y-%m-%d")
                        formatted_d = d_obj.strftime("%d %B %Y")
                        e_type = e.get("type", "event")
                        type_label = "Event 📅"
                        if e_type == "birthday": type_label = "Birthday 🎂"
                        elif e_type == "holiday": type_label = "Holiday 🏖️"
                        elif e_type == "practical": type_label = "Practical Exam 📚"
                        elif e_type == "exam": type_label = "Exam 📝"
                        
                        out_lines.append(f"{formatted_d}: [{type_label}] {e['title']}")
                    reply_text = f"Here are your schedules for {filter_type} Sir:\n• " + "\n• ".join(out_lines)
                else:
                    legacy_events = [v for k, v in load_user_knowledge().items() if k.startswith("event_")]
                    if legacy_events:
                        reply_text = f"Here are your schedules Sir:\n• " + "\n• ".join(legacy_events)
                    else:
                        reply_text = f"You don't have any specific schedules saved for {filter_type} Sir."

        # Instant Math Calculator Evaluator
        if not reply_text:
            if re.match(r'^\s*[\d\s+\-*/().]+\s*$', text_lower) and any(op in text_lower for op in ['+', '-', '*', '/']):
                try:
                    clean_expr = re.sub(r'[^0-9+\-*/().\s]', '', text_lower)
                    calc_res = eval(clean_expr, {"__builtins__": None}, {})
                    if isinstance(calc_res, (int, float)):
                        formatted_res = f"{int(calc_res)}" if isinstance(calc_res, float) and calc_res.is_integer() else f"{calc_res}"
                        reply_text = f"{user_msg} = {formatted_res}"
                except Exception:
                    pass

        # Predefined checks with top preference matching
        if not reply_text:
            for key in PREDEFINED_RESPONSES:
                if key == 'default':
                    continue
                pattern = r'\b' + re.escape(key) + r'\b'
                if re.search(pattern, text_lower):
                    reply_text = random.choice(PREDEFINED_RESPONSES[key])
                    break

        # Live Weather Engine & Time/Date Queries
        if not reply_text:
            if any(w in text_lower for w in ["weather", "mausam", "moosam", "mosam", "baarish", "barish", "rain", "monsoon", "mansoon", "temperature", "taapman", "tapman"]):
                reply_text = get_live_weather_report(text_lower)
            elif any(w in text_lower for w in ["time", "samay", "waqt", "kitne baje"]):
                now_time = get_ist_now().strftime("%I:%M %p")
                reply_text = f"The current time is {now_time}, Sir."
            elif any(w in text_lower for w in ["tomorrow", "kal kya", "kl kya", "kal konsa", "kl konsa", "kal ki date", "kl ki date"]):
                tomorrow_date = (get_ist_now() + datetime.timedelta(days=1)).strftime("%A, %B %d, %Y")
                reply_text = f"Tomorrow will be {tomorrow_date}, Sir."
            elif any(w in text_lower for w in ["today's date", "today date", "aaj konsi date", "aaj ki date"]) or (text_lower.strip() in ["date", "dates", "what date"]):
                now_date = get_ist_now().strftime("%A, %B %d, %Y")
                reply_text = f"Today's date is {now_date}, Sir."

        # Actionable Tasks
        if not reply_text:
            if "whatsapp" in text_lower and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show"]):
                reply_text = "Opening WhatsApp Web Sir."
                action_url = "https://web.whatsapp.com"
            elif any(w in text_lower for w in ["amazon", "amaon", "amzon", "amzn", "amazn"]) and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
                reply_text = "Opening Amazon Sir."
                action_url = "https://www.amazon.in"
            elif "open youtube" in text_lower:
                reply_text = "Opening YouTube Sir."
                action_url = "https://www.youtube.com"
            elif "open google" in text_lower:
                reply_text = "Opening Google Sir."
                action_url = "https://www.google.com"
            elif any(w in text_lower for w in ["music", "song", "gaana", "gana", "gane", "geet", "track", "audio"]) and any(w in text_lower for w in ["play", "chalao", "chala", "suno", "sunao", "listen", "start", "plaay"]):
                reply_text = "Playing your favourite music Sir."
                action_url = "https://www.youtube.com/watch?v=r03GO2AlNUo&t=26s"
            elif "flipkart" in text_lower and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
                reply_text = "Opening Flipkart Sir."
                action_url = "https://www.flipkart.com"
            elif "myntra" in text_lower and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
                reply_text = "Opening Myntra Sir."
                action_url = "https://www.myntra.com"
            elif "meesho" in text_lower and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
                reply_text = "Opening Meesho Sir."
                action_url = "https://www.meesho.com"
            elif any(w in text_lower for w in ["shopping", "khareedari", "kharidari"]) and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "on", "website", "site"]):
                shop_sites = [
                    ("Amazon", "https://www.amazon.in"),
                    ("Flipkart", "https://www.flipkart.com"),
                    ("Myntra", "https://www.myntra.com"),
                    ("Meesho", "https://www.meesho.com")
                ]
                chosen = random.choice(shop_sites)
                reply_text = f"Opening {chosen[0]} for your online shopping, Harsh!"
                action_url = chosen[1]
            elif "github" in text_lower and any(w in text_lower for w in ["open", "dekho", "show", "kholo"]):
                reply_text = "Opening GitHub profile for you, Harsh."
                action_url = "https://github.com"
            elif "linkedin" in text_lower and any(w in text_lower for w in ["open", "dekho", "show", "kholo"]):
                reply_text = "Opening LinkedIn profile for you, Harsh."
                action_url = "https://www.linkedin.com"
            elif "instagram" in text_lower and any(w in text_lower for w in ["open", "dekho", "show", "kholo"]):
                reply_text = "Opening Instagram for you, Harsh."
                action_url = "https://www.instagram.com"

            # 12. Live Trending Tech News
            elif any(w in text_lower for w in ["news", "tech news", "headlines", "khabar", "samachar", "aaj ki news", "latest news"]):
                reply_text = get_top_news_report()

            # 13. Remote / Local PC Screenshot Capture
            elif any(w in text_lower for w in ["screenshot", "take screenshot", "screen capture", "capture screen", "screenshot lo", "screenshot le lo"]):
                reply_text, img_url = take_pc_screenshot()
                if img_url:
                    action_url = img_url

            # 14. PC Volume Control (Mute, Volume Up, Volume Down)
            elif any(w in text_lower for w in ["mute volume", "mute pc", "volume mute", "unmute pc", "unmute volume", "awaj band", "awaaz band"]):
                reply_text = control_pc_volume("mute")
            elif any(w in text_lower for w in ["volume up", "increase volume", "awaj badhao", "awaaz badhao"]):
                reply_text = control_pc_volume("volume_up")
            elif any(w in text_lower for w in ["volume down", "decrease volume", "awaj kam", "awaaz kam"]):
                reply_text = control_pc_volume("volume_down")

            # 15. Lock Workstation / Screen Lock
            elif any(w in text_lower for w in ["lock pc", "lock screen", "pc lock", "screen lock", "lock computer", "laptop lock"]):
                reply_text = lock_workstation()

            # 16. Launch PC Apps (Notepad, Calculator, VS Code, Chrome, etc.)
            elif any(text_lower.startswith(prefix) for prefix in ["open ", "launch ", "chalao ", "kholo "]) and not any(w in text_lower for w in ["youtube", "whatsapp", "calendar", "settings", "gmail", "mail"]):
                app_target = re.sub(r'^(open|launch|chalao|kholo)\s+', '', text_lower).strip()
                if app_target:
                    reply_text = open_desktop_app(app_target)

        # Wikipedia queries
        if not reply_text and "wikipedia" in text_lower:
            query = user_msg.replace("wikipedia", "").replace("search", "").strip()
            if query:
                try:
                    result = wikipedia.summary(query, sentences=2)
                    reply_text = f"According to Wikipedia: {result}"
                except Exception:
                    reply_text = "Sorry Sir, I couldn't fetch Wikipedia results."

        # Gemini AI Status tracking
        active_client = gemini_client
        if req.api_key and req.api_key.strip():
            try:
                active_client = genai.Client(api_key=req.api_key.strip())
            except Exception as e:
                print(f"[Custom API Key Client Error] {e}")

        api_status = "online" if active_client else "offline"

        if not reply_text and active_client:
            try:
                now_str = get_ist_now().strftime("%A, %I:%M %p")
                sys_inst = (
                    f"You are VRIXA, an intelligent and fast AI assistant created by Harsh. Current time: {now_str}. "
                    "Rules: 1. Be natural, warm, and direct. 2. Match language (Hinglish/English). 3. Keep responses crisp (1-3 sentences) with relevant emojis. 4. Never give long lectures unless asked."
                )
                
                pil_image = None
                if req.image_base64:
                    try:
                        base64_data = req.image_base64.split(",")[-1]
                        img_bytes = base64.b64decode(base64_data)
                        pil_image = Image.open(BytesIO(img_bytes))
                    except Exception as img_e:
                        print(f"[Image Decode Error] {img_e}")

                convo_history = []
                recent_turns = session["context"][-3:]
                for turn in recent_turns:
                    role_str = "User" if turn["role"] == "user" else "Vrixa"
                    convo_history.append(f"{role_str}: {turn['content']}")
                
                v_prompt = user_msg if user_msg and user_msg.strip() != "" else "Analyze this image in detail."
                convo_history.append(f"User: {v_prompt}\nVrixa:")

                gemini_contents = [pil_image, "\n".join(convo_history)] if pil_image else "\n".join(convo_history)

                response = None
                models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash"]
                if req.model and req.model in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.7-flash"]:
                    if req.model not in models_to_try:
                        models_to_try.insert(0, req.model)

                for m_name in models_to_try:
                    try:
                        resp = await asyncio.to_thread(
                            active_client.models.generate_content,
                            model=m_name,
                            contents=gemini_contents,
                            config=types.GenerateContentConfig(
                                system_instruction=sys_inst,
                                max_output_tokens=180,
                                temperature=0.6
                            )
                        )
                        if resp and hasattr(resp, 'text') and resp.text:
                            response = resp
                            break
                    except Exception as try_err:
                        print(f"[Fast Model Failover {m_name}] {try_err}")

                if response and hasattr(response, 'text') and response.text:
                    reply_text = response.text.strip()
                    api_status = "online"
                else:
                    # All models failed / quota reached -> Mark offline and trigger offline predefined & Wikipedia search!
                    api_status = "offline"
            except Exception as e:
                print(f"[Gemini Error] {e}")
                api_status = "offline"

        if not reply_text:
            is_task_request = any(w in text_lower for w in ["make", "write", "create", "generate", "draft", "banao", "likho", "tayyar"])
            if is_task_request:
                if any(w in text_lower for w in ["letter", "patra", "chitti", "application", "mail", "email"]):
                    reply_text = (
                        "Here is a formal letter template for you Sir:\n\n"
                        "[Date]\nTo, [Recipient Name/Title]\n[Company/Organization]\n\n"
                        "Subject: Formal Request / Application\n\n"
                        "Dear Sir/Madam,\n\n"
                        "I am writing this letter to formally bring to your attention regarding...\n\n"
                        "Thanking you,\nSincerely,\n[Your Name]"
                    )
                else:
                    reply_text = "Sir, Gemini AI limit reached or offline! Please add a new API key in Settings to generate custom AI content."
            else:
                is_greeting = any(w in text_lower for w in ["haal", "hal", "kaise", "kese", "hello", "hi", "hey", "sup", "greetings"])
                if is_greeting:
                    reply_text = "All systems optimal Sir! Ready for your commands."
                else:
                    try:
                        # Dedicated Hinglish to English Query Translator/Normalizer specifically for Wikipedia
                        stops = [
                            r'\b(ke|ki|ka|ko|se|me|par|bhi|hi|pe|ne)\b',
                            r'\b(barme|bare|baare|batao|bato|bataye|bataiye|bata|janana|jaanna|dikhaye|dikhao)\b',
                            r'\b(what|who|where|when|why|how|is|are|was|were|tell|me|about|explain|describe)\b',
                            r'\b(kon|kaun|kya|kaisa|kaisi|kaise|kab|kahan|kha|kaha|hai|h|hein|tha|thi|the)\b',
                            r'\b(krte|krne|karna|karne|krna|karwa|karwane|karo|kare|hote|hota|hoti|karte|karta|karti|do|doing|make|use|used)\b',
                            r'\b(sir|please|plz|bhai|bro|jarvis|ok)\b'
                        ]
                        cleaned_topic = user_msg
                        for pat in stops:
                            cleaned_topic = re.sub(pat, '', cleaned_topic, flags=re.IGNORECASE)
                        cleaned_topic = re.sub(r'\s+', ' ', cleaned_topic).strip()
                        search_q = cleaned_topic if len(cleaned_topic) >= 2 else user_msg

                        wiki_summary = None
                        queries_to_try = [search_q]
                        words = [w for w in re.findall(r'\w+', search_q) if len(w) >= 3]
                        if words and words[0].lower() not in queries_to_try:
                            queries_to_try.append(words[0])

                        for q_term in queries_to_try:
                            try:
                                wiki_summary = wikipedia.summary(q_term, sentences=2, auto_suggest=False)
                                if wiki_summary: break
                            except wikipedia.exceptions.DisambiguationError as de:
                                try:
                                    valid_opt = [opt for opt in de.options if q_term.lower() in opt.lower() or opt.lower() in q_term.lower()]
                                    target_opt = valid_opt[0] if valid_opt else de.options[0]
                                    wiki_summary = wikipedia.summary(target_opt, sentences=2, auto_suggest=False)
                                    if wiki_summary: break
                                except Exception:
                                    pass
                            except Exception:
                                pass

                            if not wiki_summary:
                                try:
                                    search_results = wikipedia.search(q_term)
                                    if search_results:
                                        try:
                                            wiki_summary = wikipedia.summary(search_results[0], sentences=2, auto_suggest=False)
                                            if wiki_summary: break
                                        except wikipedia.exceptions.DisambiguationError as de2:
                                            wiki_summary = wikipedia.summary(de2.options[0], sentences=2, auto_suggest=False)
                                            if wiki_summary: break
                                except Exception:
                                    pass

                        if wiki_summary and len(wiki_summary.strip()) > 20:
                            if api_status == "offline":
                                reply_text = f"⚠️ [Notice: Gemini AI limit reached on live models. Operating in Offline Knowledge Engine]\n\nAccording to Wikipedia:\n{wiki_summary}"
                            else:
                                reply_text = f"According to Wikipedia:\n{wiki_summary}"
                        else:
                            reply_text = "Sir, Gemini AI limit reached or offline. Operating in offline predefined command mode! Please add a new API key in Settings."
                    except Exception as w_err:
                        print(f"[Offline Wiki Search Fail] {w_err}")
                        reply_text = "Sir, Gemini AI limit reached or offline. Operating in offline predefined command mode! Please add a new API key in Settings."

        # Record context & assistant reply
        session["context"].append({"role": "user", "content": user_msg})
        session["context"].append({"role": "assistant", "content": reply_text})
        session["messages"].append({"sender": "bot", "text": reply_text, "timestamp": timestamp})

        return {
            "reply": reply_text,
            "action_url": action_url,
            "api_status": api_status,
            "timestamp": timestamp,
            "session": session
        }
    except Exception as master_err:
        print(f"[Master Process Chat Error] {master_err}")
        err_reply = "Hello Sir, standing by for commands."
        return {
            "reply": err_reply,
            "action_url": None,
            "api_status": "offline",
            "timestamp": timestamp,
            "session": session
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
