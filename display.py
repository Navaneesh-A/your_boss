import time
import json
import requests
import pygetwindow as gw
from datetime import datetime, timedelta

# Import modular punishment scripts
import punish1
import punish2

# Notifications setup
from plyer import notification

PORT_5500_URL = "http://localhost:5500"
LOG_FILE = "productivity_data.json"

# Initialize global tracking variable to prevent crashing
last_alert_state = None

def send_boss_alert(title, message, urgent=False):
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="YOUR_BOSS",
            ticker="YOUR_BOSS Alert",
            timeout=7 if urgent else 4
        )
    except Exception as e:
        print(f"Failed to send notification: {e}")

def get_ist_date():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d")

def load_data():
    try:
        with open(LOG_FILE, 'r') as f:
            data = json.load(f)
            # PRODUCTION THRESHOLDS: Ensure fallback updates to real mode
            if "settings" not in data:
                data["settings"] = {}
            data["settings"]["max_youtube_seconds"] = 1200   # 20 Minutes allowance
            data["settings"]["min_code_seconds"] = 7200       # 2 Hours coding goal
            if "daily_records" not in data:
                data["daily_records"] = {}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "settings": {
                "max_youtube_seconds": 1200,   # 20 Minutes allowance
                "min_code_seconds": 7200       # 2 Hours coding goal
            },
            "daily_records": {},
            "edge_history_sync": []
        }

def track_and_enforce():
    global last_alert_state
    print("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =")
    print(" YOUR_BOSS BACKGROUND AGENT ACTIVE & ENFORCING SYSTEM RULES ")
    print("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =\n")
    
    current_window = None
    start_time = time.time()
    data = load_data()
    
    while True:
        try:
            
            ist_day = get_ist_date()
            if "daily_records" not in data:
                data["daily_records"] = {}
            if ist_day not in data["daily_records"]:
                data["daily_records"][ist_day] = {}

            # blocks of 5times daily
            # Initialize YouTube block counter for the day if not present (Max 5 blocks)
            if "_yt_block_count" not in data["daily_records"][ist_day]:
                data["daily_records"][ist_day]["_yt_block_count"] = 1

            # --- EMERGENCY BYPASS SHORTCUT ---
            active_window = gw.getActiveWindow()
            if active_window and "boss-override" in active_window.title.lower():
                print("[BYPASS] : Secret override window detected. Freezing Boss enforcement.")
                time.sleep(5)
                continue


            # --- 1. Track Active Window Time ---
            active_window = gw.getActiveWindow()
            if active_window and active_window.title:
                active_title = active_window.title
                
                if current_window is None:
                    current_window = active_title
                    start_time = time.time()
                elif active_title != current_window:
                    duration = round(time.time() - start_time, 2)
                    
                    # Log directly to daily records
                    data["daily_records"][ist_day][current_window] = data["daily_records"][ist_day].get(current_window, 0) + duration
                    
                    current_window = active_title
                    start_time = time.time()

            # --- 2. Poll External Progress Tracker Data ---
            try:
                res = requests.get(PORT_5500_URL, timeout=2)
                if res.status_code == 200:
                    data["edge_history_sync"] = res.json()
            except requests.exceptions.RequestException:
                pass

            # --- 3. Evaluate Time Logs (Smart Context Classification) ---
            youtube_wasted_time = 0
            coding_time = 0
            learning_keywords = ["tutorial", "course", "coding", "learn", "programming", "dev", "data structure", "leetcode"]

            for title, seconds in data["daily_records"][ist_day].items():
                # ADDED THIS 
                if title.startswith("_"): # Skip system keys
                    continue
                title_lower = title.lower()
                if "youtube" in title_lower:
                    is_learning = any(kw in title_lower for kw in learning_keywords)
                    if is_learning:
                        coding_time += seconds  
                    else:
                        youtube_wasted_time += seconds  
                elif "visual studio code" in title_lower:
                    coding_time += seconds
                elif any(domain in title_lower for domain in ["github", "gemini", "google search", "stackoverflow"]):
                    coding_time += seconds

            limit = data["settings"]["max_youtube_seconds"]
            coding_goal = data["settings"]["min_code_seconds"]
            current_block = data["daily_records"][ist_day]["_yt_block_count"]
            remaining_youtube = max(0, limit - youtube_wasted_time)
           #remaining_code = max(0, coding_goal - coding_time)
            
            # --- 4. Predictive Notifications ---
            if "YouTube" in (current_window or "") and "tutorial" not in (current_window or "").lower():
                if last_alert_state != "warning" and remaining_youtube < 60:
                    send_boss_alert(
                        title=f"⚠️ YOUTUBE BLOCK {current_block} WARNING",
                        message=f"Block lockdown executing in {round(remaining_youtube)} seconds!"
                    )
                    last_alert_state = "warning"

            # --- 5. Trigger System Punishment Array ---
            if youtube_wasted_time > limit:
                if current_block <= 5:
                    print(f"\n🚨🚨🚨 YOUTUBE BLOCK {current_block} EXCEEDED! EXECUTING LOCKDOWN 🚨🚨🚨\n")
                    send_boss_alert(
                        title=f"🚨 BLOCK {current_block} CROSSOVER LOCKDOWN 🚨",
                        message="Threshold crossed. Resetting your timer block.",
                        urgent=True
                    )
                    
                    try:punish1.trigger_tab_kill()
                    except Exception as e: print(e)
                    try:punish2.trigger_audio_alarm()
                    except Exception as e: print(e)

                    # Reset ONLY YouTube logs for this current block day pool
                    youtube_keys = [k for k in data["daily_records"][ist_day].keys() if "youtube" in k.lower() and not any(lk in k.lower() for lk in learning_keywords)]
                    for k in youtube_keys:
                        data["daily_records"][ist_day][k] = 0
                    
                    # Advance to the next allocation block
                    data["daily_records"][ist_day]["_yt_block_count"] += 1
                else:
                    # Absolute total burnout (All 5 blocks used up)
                    print("\n🚨🚨🚨 ALL 5 DAILY BLOCKS USED UP! HARD SYSTEM LOCKDOWN 🚨🚨🚨\n")
                    try:punish1.trigger_tab_kill()
                    except Exception as e: print(e)
                
                start_time = time.time()
                last_alert_state = "breached"

            # --- 6. Save State ---
            with open(LOG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            print(f"[CRITICAL SYSTEM ERROR]: {e}")
            
        # Hard 5-second interval to allow emergency typing in terminal if needed!
        time.sleep(5)

if __name__ == "__main__":
    track_and_enforce()