"""
Nova Voice Assistant - Python Project
AICTE OASIS INFOBYTE Internship
"""

import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import wikipedia
import threading
import time
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# CONFIG
WAKE_WORD        = "nova"
EMAIL_ADDRESS    = ""
EMAIL_PASSWORD   = ""
MIC_INDEX        = 2
ENERGY_THRESHOLD = 20
STOP_NOW         = threading.Event()

# ─── SPEAK ────────────────────────────────────
def speak(text):
    if not text or not text.strip():
        return
    if STOP_NOW.is_set():
        return
    print("\n  [Nova]: " + text)
    try:
        eng = pyttsx3.init()
        eng.setProperty("rate", 165)
        eng.setProperty("volume", 1.0)
        for v in eng.getProperty("voices"):
            if "zira" in v.name.lower():
                eng.setProperty("voice", v.id)
                break
        if not STOP_NOW.is_set():
            eng.say(text)
            eng.runAndWait()
        eng.stop()
        del eng
    except Exception as e:
        print("  [TTS Error]: " + str(e))

# ─── STOP WATCHER ─────────────────────────────
def _stop_watcher():
    while True:
        try:
            inp = input()
            if inp.strip().lower() in ["stop", "s", "x"]:
                STOP_NOW.set()
                print("  [Stopped - ready for next command]\n")
        except:
            pass

threading.Thread(target=_stop_watcher, daemon=True).start()

# ─── LISTEN ───────────────────────────────────
def listen(timeout=3, phrase_limit=6):
    r = sr.Recognizer()
    r.energy_threshold         = ENERGY_THRESHOLD
    r.dynamic_energy_threshold = False
    r.pause_threshold          = 0.4
    r.non_speaking_duration    = 0.2
    try:
        with sr.Microphone(device_index=MIC_INDEX) as src:
            r.adjust_for_ambient_noise(src, duration=0.1)
            print("  [Listening... speak now]", end="", flush=True)
            audio = r.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
        print(" [processing...]", end="", flush=True)
        result = r.recognize_google(audio, language="en-IN")
        print("\n")
        print("  You asked: " + result)
        print("  Nova answering...")
        print("")
        return result.lower().strip()
    except sr.WaitTimeoutError:
        print(); return ""
    except sr.UnknownValueError:
        print(); return ""
    except Exception as e:
        print("\n  [Mic]: " + str(e)); return ""

# ─── GET INPUT ────────────────────────────────
def get_input(timeout=3):
    STOP_NOW.clear()
    q = listen(timeout=timeout)
    if not q:
        try:
            q = input("  >>> ").strip().lower()
            if q:
                print("  You typed: " + q)
                print("  Nova answering...")
        except:
            pass
    return q

# ─── REMINDERS ────────────────────────────────
reminders = []

def _reminder_check():
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        for r in reminders:
            if r["time"] == now and not r["fired"]:
                speak("Reminder: " + r["message"])
                r["fired"] = True
        time.sleep(30)

threading.Thread(target=_reminder_check, daemon=True).start()

def set_reminder(q):
    try:
        parts = q.split("at")
        msg   = parts[0].replace("remind me to","").replace("set a reminder to","").strip()
        t     = parts[1].strip().replace(" ",":")
        datetime.datetime.strptime(t, "%H:%M")
        reminders.append({"time": t, "message": msg, "fired": False})
        speak("Reminder set for " + t + ".")
    except:
        speak("Say: remind me to call mom at 15 30.")

# ─── EMAIL ────────────────────────────────────
def handle_email_flow():
    speak("Who to send email to?")
    to = get_input(6)
    if not to: speak("Cancelled."); return
    speak("Subject?")
    sub = get_input(6) or "No Subject"
    speak("Message?")
    body = get_input(10)
    if not body: speak("Cancelled."); return
    speak("Send to " + to + "? Say yes.")
    if "yes" in get_input(4):
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"]   = to
            msg["Subject"] = sub
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                s.sendmail(EMAIL_ADDRESS, to, msg.as_string())
            speak("Email sent successfully.")
        except:
            speak("Email failed.")
    else:
        speak("Email cancelled.")

# ─── WEATHER ──────────────────────────────────
def get_weather(city):
    try:
        import requests
        city = city.strip()
        speak("Getting weather for " + city + ".")
        r = requests.get(
            "https://wttr.in/" + city.replace(" ", "+") + "?format=j1",
            timeout=8, headers={"User-Agent": "Nova/1.0"})
        d = r.json()
        c = d["current_condition"][0]
        t = d["weather"][0]
        temp  = c["temp_C"]
        feels = c["FeelsLikeC"]
        humid = c["humidity"]
        desc  = c["weatherDesc"][0]["value"]
        wind  = c["windspeedKmph"]
        hi    = t["maxtempC"]
        lo    = t["mintempC"]
        h     = t.get("hourly", [])
        morn  = h[2]["tempC"] if len(h) > 2 else temp
        eve   = h[6]["tempC"] if len(h) > 6 else temp
        a     = t.get("astronomy", [{}])[0]
        sr2   = a.get("sunrise", "N/A")
        ss    = a.get("sunset", "N/A")

        print("")
        print("  " + "="*42)
        print("  " + city.title() + " Weather Report")
        print("  " + "="*42)
        print("  Condition : " + desc)
        print("  Temp      : " + temp + "C  (feels " + feels + "C)")
        print("  Humidity  : " + humid + "%   Wind: " + wind + " km/h")
        print("  High/Low  : " + hi + "C / " + lo + "C")
        print("  Morning   : " + morn + "C   Evening: " + eve + "C")
        print("  Sunrise   : " + sr2 + "    Sunset: " + ss)
        print("  " + "="*42)
        print("  [type stop to stop speaking]")
        print("")

        speak(city + " weather. " + desc + ".")
        speak("Temperature " + temp + " degrees, feels like " + feels + ".")
        speak("Humidity " + humid + " percent, wind " + wind + " kilometres per hour.")
        speak("High " + hi + ", low " + lo + " degrees.")
        speak("Sunrise " + sr2 + ", sunset " + ss + ".")
    except Exception as e:
        print("  [Weather error]: " + str(e))
        speak("Could not get weather. Check internet.")

# ─── WIKIPEDIA ────────────────────────────────
def wiki_search(topic):
    try:
        speak("Searching " + topic + ".")
        wikipedia.set_lang("en")
        result = wikipedia.summary(topic, sentences=3)
        print("")
        print("  " + "="*42)
        print("  Wikipedia: " + topic.title())
        print("  " + "="*42)
        print("  " + result)
        print("  " + "="*42)
        print("  [type stop to stop speaking]")
        print("")
        speak(result)
    except wikipedia.exceptions.DisambiguationError as e:
        speak("Multiple results. Try: " + ", ".join(e.options[:2]) + ".")
    except wikipedia.exceptions.PageError:
        speak("No page for " + topic + ".")
    except:
        speak("Search failed.")

# ─── JOKES ────────────────────────────────────
JOKES = [
    "Why do programmers prefer dark mode? Light attracts bugs!",
    "My computer needed a break. Now it keeps sending Kit Kat ads.",
    "Why do Java developers wear glasses? They do not C sharp.",
    "A SQL query walks into a bar, asks two tables: Can I join you?",
    "How many programmers to change a bulb? None. Hardware problem!",
    "Why was the JavaScript developer sad? He could not null his feelings.",
]
def tell_joke(): speak(random.choice(JOKES))

# ─── SMART HOME ───────────────────────────────
devices = {
    "living room light": False,
    "bedroom light": False,
    "fan": False,
    "air conditioner": False,
    "tv": False,
}

def control_device(q):
    action = "on" if " on" in q else ("off" if " off" in q else None)
    if not action: speak("Say turn on or off then device."); return
    match = next((d for d in devices if d in q), None)
    if not match: speak("Device not found. Say fan, tv, or light."); return
    devices[match] = (action == "on")
    speak(match + " turned " + action + ".")

def home_status():
    on  = [d for d, s in devices.items() if s]
    off = [d for d, s in devices.items() if not s]
    msg = ""
    if on:  msg += "On: "  + ", ".join(on)  + ". "
    if off: msg += "Off: " + ", ".join(off) + "."
    speak(msg if msg else "No devices found.")

# ─── DATE & TIME ──────────────────────────────
def tell_time():
    speak("Time is " + datetime.datetime.now().strftime("%I:%M %p") + ".")

def tell_date():
    speak("Today is " + datetime.datetime.now().strftime("%A, %B %d %Y") + ".")

# ─── COMMAND ROUTER ───────────────────────────
def process(q):
    if not q: return True
    q = q.replace(WAKE_WORD, "").strip()
    if not q: return True
    STOP_NOW.clear()

    if any(w in q for w in ["hello","hi","hey","good morning","good evening","good afternoon"]):
        h = datetime.datetime.now().hour
        g = "Good morning" if h < 12 else ("Good afternoon" if h < 18 else "Good evening")
        speak(g + "! I am Nova. How can I help?")
    elif "time" in q:
        tell_time()
    elif "date" in q or "today" in q:
        tell_date()
    elif "remind" in q:
        set_reminder(q)
    elif "email" in q or "mail" in q:
        handle_email_flow()
    elif "weather" in q:
        city = ""
        for kw in ["weather in", "weather of", "weather for"]:
            if kw in q:
                city = q.split(kw)[-1].strip()
                break
        if not city:
            speak("Which city?")
            city = get_input(5) or input("  City: ").strip()
        if city: get_weather(city)
        else: speak("City not heard.")
    elif any(k in q for k in ["search","tell me about","what is","who is","explain","describe"]):
        t = q
        for k in ["search for","search","tell me about","what is","who is","explain","describe"]:
            t = t.replace(k, "")
        t = t.strip()
        if t: wiki_search(t)
        else: speak("What to search?")
    elif "open youtube" in q:
        speak("Opening YouTube.")
        webbrowser.open("https://youtube.com")
    elif "open google" in q:
        speak("Opening Google.")
        webbrowser.open("https://google.com")
    elif "search web" in q:
        t = q.replace("search web for", "").strip()
        webbrowser.open("https://www.google.com/search?q=" + t.replace(" ", "+"))
        speak("Searching " + t + ".")
    elif "turn on" in q or "turn off" in q:
        control_device(q)
    elif "home status" in q or "device status" in q:
        home_status()
    elif "joke" in q or "funny" in q or "laugh" in q:
        tell_joke()
    elif "help" in q or "what can you do" in q:
        speak("I can tell time, date, weather, search Wikipedia, open YouTube or Google, set reminders, send email, control smart home devices, and tell jokes.")
        speak("Type stop anytime to stop me.")
    elif "your name" in q or "who are you" in q:
        speak("I am Nova, your personal voice assistant.")
    elif "how are you" in q:
        speak("Great and ready to help!")
    elif "thank" in q:
        speak("You are welcome!")
    elif any(w in q for w in ["exit","quit","goodbye","bye","close"]):
        speak("Goodbye! Have a great day!")
        return False
    else:
        speak("Not sure. Say help for options.")
    return True

# ─── MAIN ─────────────────────────────────────
def main():
    print("")
    print("  " + "="*48)
    print("  NOVA - Voice Assistant | AICTE OASIS INFOBYTE")
    print("  " + "="*48)
    print("  Speak your command OR type it below")
    print("  Type  stop  anytime to stop Nova speaking")
    print("  Type  bye   to exit")
    print("  " + "="*48)
    print("")

    speak("Hello! I am Nova. How can I help you?")

    while True:
        STOP_NOW.clear()
        print("")
        print("  " + "-"*44)
        print("  Speak now  OR  type command below:")
        print("  " + "-"*44)

        q = listen(timeout=3)
        if not q:
            try:
                q = input("  >>> ").strip().lower()
                if q:
                    print("  You typed: " + q)
                    print("  Nova answering...")
            except (EOFError, KeyboardInterrupt):
                speak("Goodbye!")
                break

        if q in ["stop", "s", "x"]:
            STOP_NOW.set()
            print("  [Stopped]\n")
            continue

        if q:
            if not process(q):
                break

if __name__ == "__main__":
    main()
