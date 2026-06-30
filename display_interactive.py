import time
import json
import requests
import pygetwindow as gw
from datetime import datetime, timedelta
from plyer import notification
import tkinter as tk
from pynput import mouse, keyboard

# Import modular punishment scripts from your display.py logic
import punish1
import punish2

PORT_5500_URL = "http://localhost:5500"
LOG_FILE = "productivity_data.json"

# Asynchronous Monitoring States
last_input_time = time.time()
system_is_frozen = False
last_video_title = None
video_start_time = None
prompted_videos = set()
flash_message_expiry = None
last_alert_state = None

def update_activity(*args):
    """Fires instantly via hardware hooks to unfreeze tracking pipelines."""
    global last_input_time, system_is_frozen, flash_message_expiry
    last_input_time = time.time()
    if system_is_frozen:
        system_is_frozen = False
        print("[RESTORE]: User input tracked. Waking up logging pipelines.")
        send_casual_alert("⚡ System Restored", "Welcome back! Resuming tracking sequence.")
        try:
            with open(LOG_FILE, 'r') as f: data = json.load(f)
            data["status_metrics"]["status"] = "Active"
            data["status_metrics"]["flash_message"] = "Welcome Back! Resuming tracking sequence."
            flash_message_expiry = time.time() + 6
            with open(LOG_FILE, 'w') as f: json.dump(data, f, indent=4)
        except: pass

# Spin up asynchronous hardware capture listeners
mouse_listener = mouse.Listener(on_move=update_activity, on_click=update_activity, on_scroll=update_activity)
keyboard_listener = keyboard.Listener(on_press=update_activity)
mouse_listener.start()
keyboard_listener.start()

def send_casual_alert(title, message, urgent=False):
    try:
        notification.notify(title=title, message=message, app_name="YOUR_BOSS", timeout=7 if urgent else 4)
    except Exception as e:
        print(f"Notification Error: {e}")

def get_ist_date():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d")

def load_data():
    try:
        with open(LOG_FILE, 'r') as f:
            data = json.load(f)
            if "daily_records" not in data: data["daily_records"] = {}
            if "settings" not in data: data["settings"] = {}
            if "status_metrics" not in data:
                data["status_metrics"] = {"status": "Active", "away_count": 0, "flash_message": ""}
            data["settings"]["max_youtube_seconds"] = 1200
            data["settings"]["min_code_seconds"] = 7200
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "settings": {"max_youtube_seconds": 1200, "min_code_seconds": 7200},
            "status_metrics": {"status": "Active", "away_count": 0, "flash_message": ""},
            "daily_records": {},
            "edge_history_sync": []
        }

def ask_productivity_status(video_title):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    win = tk.Toplevel(root)
    win.title("YOUR_BOSS: Live Verification")
    win.attributes("-topmost", True)
    win.geometry("400x150+500+300")
    
    tk.Label(win, text=f"You have been watching this video for 1 minute:\n\n'{video_title[:50]}...'\n\nIs this productive?", font=("Arial", 10), pady=10).pack()
    
    res = [False]
    def select(val):
        res[0] = val
        root.destroy()
        
    tk.Button(win, text="Yes, Productive", command=lambda: select(True), bg="#28a745", fg="white", width=15).pack(side="left", padx=30, pady=10)
    tk.Button(win, text="No, Distraction", command=lambda: select(False), bg="#dc3545", fg="white", width=15).pack(side="right", padx=30, pady=10)
    
    root.mainloop()
    return "productive" if res[0] else "unproductive"

def check_inactivity_timeout():
    """Spawns custom layout. Forcefully auto-freezes and closes after 3 seconds if ignored."""
    user_responded = [False]
    root = tk.Tk()
    root.title("⚡ Inactivity Warning")
    root.attributes("-topmost", True)
    root.geometry("350x130+500+300")
    
    tk.Label(root, text="Are you there? Still working?\n(Autofreezing in 3 seconds...)", font=("Arial", 11), pady=10).pack()

    def handle_click(event=None): # Added event parameter to catch keyboard triggers
        user_responded[0] = True
        root.destroy()

    tk.Button(root, text="I'm Back!", command=handle_click, width=15, bg="#28a745", fg="white", font=("Arial", 10, "bold")).pack(pady=5)

    # --- KEYBOARD INTERCEPT UPGRADE ---
    # Binds ANY keypress while the window is focused to trigger the 'I'm Back' logic
    root.bind("<Key>", handle_click)

    def enforce_autofreeze():
        if not user_responded[0]:
            root.destroy()

    root.after(10000, enforce_autofreeze)
    
    time_before = time.time()
    root.mainloop()
    elapsed = time.time() - time_before

    if elapsed > 12:
        return "system_slept"

    return user_responded[0]   
   
def track_and_enforce():
    global last_video_title, video_start_time, prompted_videos, last_input_time, system_is_frozen, flash_message_expiry, last_alert_state
    
    print("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =")
    print("== YOUR_BOSS INTERACTIVE INTERCEPTOR ACTIVE (IST MODE) ==")
    print("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =\n")
    
    current_window = None
    window_start = time.time()
    
    while True:
        try:
            data = load_data()
            ist_day = get_ist_date()
            
            # Auto-clear flash banner values after 6 seconds
            if flash_message_expiry and time.time() > flash_message_expiry:
                data["status_metrics"]["flash_message"] = ""
                flash_message_expiry = None

            # --- 1. IDLE CHECK CORNERSTONE ---
            if not system_is_frozen and (time.time() - last_input_time >= 30):
                print("[WARNING]: Device activity lost. Verification check dispatched.")
                data["status_metrics"]["status"] = "Pending Verification"
                with open(LOG_FILE, 'w') as f: json.dump(data, f, indent=4)
                
                activity_status = check_inactivity_timeout()
                
                if activity_status == "system_slept":
                    last_input_time = time.time()
                    system_is_frozen = False
                    data["status_metrics"]["status"] = "Active"
                    data["status_metrics"]["flash_message"] = "Welcome back! Recovered from sleep mode."
                    flash_message_expiry = time.time() + 6
                elif not activity_status: 
                    system_is_frozen = True
                    data["status_metrics"]["status"] = "Frozen"
                    data["status_metrics"]["away_count"] += 1
                    send_casual_alert("❄️ Logs Frozen", "All tracking engines suspended.")
                else:
                    last_input_time = time.time()
                    data["status_metrics"]["status"] = "Active"
                    data["status_metrics"]["flash_message"] = "Welcome Back! Keep grinding."
                    flash_message_expiry = time.time() + 6
                
                with open(LOG_FILE, 'w') as f: json.dump(data, f, indent=4)
                continue

            # Core escape block if engine is frozen
            if system_is_frozen:
                time.sleep(2)
                continue

            # --- 2. REGULAR TRACKING MATRIX ---
            if ist_day not in data["daily_records"]: data["daily_records"][ist_day] = {}
            if "youtube_productive" not in data["daily_records"][ist_day]: data["daily_records"][ist_day]["youtube_productive"] = 0
            if "youtube_unproductive_free_time" not in data["daily_records"][ist_day]: data["daily_records"][ist_day]["youtube_unproductive_free_time"] = 0
            if "_yt_block_count" not in data["daily_records"][ist_day]: data["daily_records"][ist_day]["_yt_block_count"] = 1

            active_window = gw.getActiveWindow()
            if active_window and "boss-override" in active_window.title.lower():
                time.sleep(5)
                continue

            if not active_window or not active_window.title:
                time.sleep(2)
                continue
                
            active_title = active_window.title

            if current_window is None:
                current_window = active_title
                window_start = time.time()
            elif active_title != current_window:
                duration = round(time.time() - window_start, 2)
                if "youtube" not in current_window.lower():
                    data["daily_records"][ist_day][current_window] = data["daily_records"][ist_day].get(current_window, 0) + duration
                current_window = active_title
                window_start = time.time()

            # --- 3. YOUTUBE SEGREGATION LOGIC ---
            learning_keywords = ["tutorial", "course", "coding", "learn", "programming", "dev", "data structure", "leetcode"]
            
            if "youtube" in active_title.lower():
                if active_title != last_video_title:
                    last_video_title = active_title
                    video_start_time = time.time()
                
                session_duration = time.time() - video_start_time
                
                if session_duration >= 60 and active_title not in prompted_videos:
                    prompted_videos.add(active_title)
                    classification = ask_productivity_status(active_title)
                    
                    if classification == "productive":
                        data["daily_records"][ist_day]["youtube_productive"] += session_duration
                    else:
                        data["daily_records"][ist_day]["youtube_unproductive_free_time"] += session_duration
                    video_start_time = time.time()
                
                elif active_title in prompted_videos:
                    tick = 2
                    if any(kw in active_title.lower() for kw in learning_keywords):
                        data["daily_records"][ist_day]["youtube_productive"] += tick
                    else:
                        data["daily_records"][ist_day]["youtube_unproductive_free_time"] += tick
                        if int(time.time()) % 8 == 0:
                            send_casual_alert("❗ Time Waste Notice", f"Burning time budget on:\n'{active_title[:40]}...'")

            # --- 4. PUNISHMENT SYSTEM BLOCK INTEGRATION ---
            unproductive_seconds = data["daily_records"][ist_day]["youtube_unproductive_free_time"]
            limit = data["settings"]["max_youtube_seconds"]
            current_block = data["daily_records"][ist_day]["_yt_block_count"]

            if unproductive_seconds > limit:
                if current_block <= 5:
                    print(f"\n🚨🚨🚨 YOUTUBE BLOCK {current_block} EXCEEDED! EXECUTING LOCKDOWN 🚨🚨🚨\n")
                    send_casual_alert(f"🚨 BLOCK {current_block} CROSSOVER LOCKDOWN 🚨", "Resetting timer block.", urgent=True)
                    
                    try: punish1.trigger_tab_kill()
                    except Exception as e: print(e)
                    try: punish2.trigger_audio_alarm()
                    except Exception as e: print(e)

                    data["daily_records"][ist_day]["youtube_unproductive_free_time"] = 0
                    data["daily_records"][ist_day]["_yt_block_count"] += 1
                else:
                    print("\n🚨🚨🚨 ALL DAILY BLOCKS EXHAUSTED! HARD SYSTEM LOCKDOWN 🚨🚨🚨\n")
                    try: punish1.trigger_tab_kill()
                    except Exception as e: print(e)

            with open(LOG_FILE, 'w') as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            print(f"System Loop Core Intercept Error: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    track_and_enforce()