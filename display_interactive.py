import time
import json
import requests
import pygetwindow as gw
from datetime import datetime, timedelta
from plyer import notification
import tkinter as tk
from tkinter import messagebox
from pynput import mouse, keyboard
import threading

PORT_5500_URL = "http://localhost:5500"
LOG_FILE = "productivity_data.json"

# Asynchronous Monitoring States
last_input_time = time.time()
system_is_frozen = False
last_video_title = None
video_start_time = None
prompted_videos = set()

# Asynchronous pynput Event Listeners for Activity Captures
def update_activity(*args):
    global last_input_time, system_is_frozen
    last_input_time = time.time()
    if system_is_frozen:
        system_is_frozen = False
        send_casual_alert("⚡ System Restored", "Welcome back! Resuming tracking sequence.")

mouse_listener = mouse.Listener(on_move=update_activity, on_click=update_activity, on_scroll=update_activity)
keyboard_listener = keyboard.Listener(on_press=update_activity)

mouse_listener.start()
keyboard_listener.start()

def send_casual_alert(title, message):
    try:
        notification.notify(title=title, message=message, app_name="YOUR_BOSS", timeout=4)
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
            data["settings"]["max_youtube_seconds"] = 1200
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "settings": {"max_youtube_seconds": 1200, "min_code_seconds": 7200},
            "daily_records": {},
            "edge_history_sync": []
        }

def ask_productivity_status(video_title):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    answer = messagebox.askyesno("YOUR_BOSS: Live Verification", f"You have been watching this video for 1 minute:\n\n'{video_title}'\n\nIs this productive?")
    root.destroy()
    return "productive" if answer else "unproductive"

def check_inactivity_timeout():
    """
    Spawns an interactive 10-second countdown alert box on top of the OS window stack.
    Returns True if user explicitly registers a click within 10 seconds.
    """
    global system_is_frozen
    box_result = [False]

    def close_box_automatically(tk_root):
        if not box_result[0]:
            tk_root.destroy()

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    # Force a 10-second automatic kill thread execution
    timer = threading.Timer(10.0, lambda: close_box_automatically(root))
    timer.start()

    res = messagebox.askyesno("⚡ Inactivity Warning", "Are you there? Still working? (Autofreezing in 10s)")
    box_result[0] = True
    timer.cancel()
    root.destroy()
    return res

def track_and_enforce():
    global last_video_title, video_start_time, prompted_videos, last_input_time, system_is_frozen
    
    print("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =")
    print("== YOUR_BOSS INTERACTIVE INTERCEPTOR ACTIVE (IST MODE) ==")
    print("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =\n")
    
    current_window = None
    window_start = time.time()
    data = load_data()
    
    while True:
        try:
            # --- 1. IDLE CHECK CORNERSTONE ---
            if not system_is_frozen and (time.time() - last_input_time >= 180): # 3 mins of total device silence
                print("[WARNING]: Device activity lost. Verification check dispatched.")
                is_active = check_inactivity_timeout()
                
                if not is_active:
                    system_is_frozen = True
                    print("[FREEZE]: Core processing frozen. Tracking suspended until user interaction.")
                    send_casual_alert("❄️ Logs Frozen", "All tracking engines suspended due to inactivity.")
                    continue
                else:
                    last_input_time = time.time() # Reset clock pool bounds

            if system_is_frozen:
                time.sleep(2)
                continue

            # --- 2. REGULAR TRACKING MATRIX ---
            ist_day = get_ist_date()
            if ist_day not in data["daily_records"]: data["daily_records"][ist_day] = {}
            if "youtube_productive" not in data["daily_records"][ist_day]: data["daily_records"][ist_day]["youtube_productive"] = 0
            if "youtube_unproductive_free_time" not in data["daily_records"][ist_day]: data["daily_records"][ist_day]["youtube_unproductive_free_time"] = 0
            if "_yt_block_count" not in data["daily_records"][ist_day]: data["daily_records"][ist_day]["_yt_block_count"] = 1

            active_window = gw.getActiveWindow()
            if not active_window or not active_window.title:
                time.sleep(5)
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
                    tick = 5
                    if "tutorial" in active_title.lower() or "coding" in active_title.lower():
                        data["daily_records"][ist_day]["youtube_productive"] += tick
                    else:
                        data["daily_records"][ist_day]["youtube_unproductive_free_time"] += tick
                        if time.time() % 7 == 0:
                            send_casual_alert("❗ Time Waste Notice", f"Burning time budget on:\n'{active_title[:40]}...'")

            # --- 4. ENGINE SAVE BLOCKS ---
            unproductive_seconds = data["daily_records"][ist_day]["youtube_unproductive_free_time"]
            limit = data["settings"]["max_youtube_seconds"]
            current_block = data["daily_records"][ist_day]["_yt_block_count"]

            if unproductive_seconds > limit:
                data["daily_records"][ist_day]["youtube_unproductive_free_time"] = 0
                data["daily_records"][ist_day]["_yt_block_count"] += 1
                time.sleep(5)

            with open(LOG_FILE, 'w') as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            print(f"System Loop Core Intercept Error: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    track_and_enforce()