import time
import json
import requests
import pygetwindow as gw

# 1. Import your modular punishment scripts
import punish1
import punish2

PORT_5500_URL = "http://localhost:5500"
LOG_FILE = "productivity_data.json"

def load_data():
    try:
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default fallback structure with settings thresholds (in seconds)
        return {
            "settings": {
                "max_youtube_seconds": 20,  # 15 minutes
                "min_code_seconds": 10    # 1 hour
            },
            "window_time": {},
            "edge_history_sync": []
        }

def track_and_enforce():
    print("YOUR_BOSS agent active. Monitoring and enforcing rules...\n")
    current_window = None
    start_time = time.time()
    
    data = load_data()

    while True:
        try:
            # --- 1. Track Active Window Time ---
            active_window = gw.getActiveWindow()
            if active_window and active_window.title:
                active_title = active_window.title
                
                if current_window is None:
                    current_window = active_title
                    start_time = time.time()
                elif active_title != current_window:
                    duration = round(time.time() - start_time, 2)
                    data["window_time"][current_window] = data["window_time"].get(current_window, 0) + duration
                    
                    current_window = active_title
                    start_time = time.time()

            # --- 2. Poll External Progress Tracker Data ---
            try:
                res = requests.get(PORT_5500_URL, timeout=2)
                if res.status_code == 200:
                    data["edge_history_sync"] = res.json()
            except requests.exceptions.RequestException:
                pass

            # --- 3. Evaluate Rule Thresholds (The Boss Check) ---
            youtube_wasted_time = 0
            coding_time = 0
            
            for title, seconds in data["window_time"].items():
                if "YouTube" in title:
                    youtube_wasted_time += seconds
                elif "Visual Studio Code" in title:
                    coding_time += seconds

            # Threshold configurations
            limit = data.get("settings", {}).get("max_youtube_seconds", 20)
            coding_goal = data.get("settings", {}).get("min_code_seconds", 10)
            
            remaining_youtube = max(0, limit - youtube_wasted_time)
            remaining_code = max(0, coding_goal - coding_time)
            
            # --- LIVE COMMAND LOGS ---
            print("=" * 60)
            print(f"[CURRENT STATUS]: Active Window: '{current_window}'")
            print(f"[STATS]         : YouTube: {round(youtube_wasted_time, 1)}s/{limit}s | Code: {round(coding_time, 1)}s/{coding_goal}s")
            
            if "YouTube" in (current_window or ""):
                print(f"[PREDICTION]    : Warning! Distraction detected.")
                print(f"[FORECAST]      : 🚨 LOCKDOWN IMMINENT in {round(remaining_youtube, 1)}s!")
                print(f"[ACTION PLAN]   : Shift focus to VS Code now.")
                
            elif "Visual Studio Code" in (current_window or ""):
                if remaining_code > 0:
                    print(f"[PREDICTION]    : Good. You are building up consistency.")
                    print(f"[FORECAST]      : Spend {round(remaining_code, 1)}s more to satisfy your coding goal.")
                else:
                    print(f"[PREDICTION]    : Daily target achieved!")
                    print(f"[FORECAST]      : Boss is fully appeased. System safe.")
                print(f"[ACTION PLAN]   : Maintain this momentum.")
                
            else:
                print(f"[PREDICTION]    : Idle / Neutral behavior.")
                print(f"[FORECAST]      : YouTube safety buffer: {round(remaining_youtube, 1)}s.")
                print(f"[ACTION PLAN]   : Launch an IDE to avoid drifting.")
            print("=" * 60 + "\n")

            # --- Trigger Punishment ---
            # --- Trigger Punishment ---
            if youtube_wasted_time > limit:
                print("🚨🚨🚨 DISTRACTION THRESHOLD BREACHED! ENFORCING LOCKDOWN... 🚨🚨🚨")
                
                try:
                    punish1.trigger_tab_kill()
                    punish2.trigger_audio_alarm()
                except Exception as ex:
                    print(f"Punishment execution error: {ex}")
                
                # FIX: Clear all past entries containing 'YouTube' completely out of the dataset
                youtube_keys = [k for k in data["window_time"].keys() if "YouTube" in k]
                for k in youtube_keys:
                    data["window_time"][k] = 0
                
                # Force update start time so the clock resets cleanly for the next window
                start_time = time.time()
            # --- 4. Commit to Database File ---
            with open(LOG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            print(f"System Error: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    track_and_enforce()