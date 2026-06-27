import time
import json
import requests
import pygetwindow as gw

# Import modular punishment scripts
import punish1
import punish2

PORT_5500_URL = "http://localhost:5500"
LOG_FILE = "productivity_data.json"

def load_data():
    try:
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # PRODUCTION READY REALISTIC THRESHOLDS (in seconds)
        return {
            "settings": {
                "max_youtube_seconds": 1200,   # 20 Minutes daily distraction allowance
                "min_code_seconds": 7200       # 2 Hours daily coding target
            },
            "window_time": {},
            "edge_history_sync": []
        }

def track_and_enforce():
    print("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =")
    print("⚡ YOUR_BOSS BACKGROUND AGENT ACTIVE & ENFORCING SYSTEM RULES ⚡")
    print("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =\n")
    
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
                pass  # Fallback gracefully if port 5500 server is down

            # --- 3. Evaluate Time Logs ---
            youtube_wasted_time = 0
            coding_time = 0
            
            for title, seconds in data["window_time"].items():
                if "YouTube" in title:
                    youtube_wasted_time += seconds
                elif "Visual Studio Code" in title:
                    coding_time += seconds

            limit = data.get("settings", {}).get("max_youtube_seconds", 1200)
            coding_goal = data.get("settings", {}).get("min_code_seconds", 7200)
            
            remaining_youtube = max(0, limit - youtube_wasted_time)
            remaining_code = max(0, coding_goal - coding_time)
            
            # --- 4. Predictive Command Line Dashboard ---
            print("=" * 65)
            print(f"[CURRENT FOCUS] : '{current_window}'")
            print(f"[METRICS]       : YouTube: {round(youtube_wasted_time/60, 1)}m/{round(limit/60, 1)}m | Code: {round(coding_time/60, 1)}m/{round(coding_goal/60, 1)}m")
            
            if "YouTube" in (current_window or ""):
                print(f"[PREDICTION]    : 🚨 Boss Warning: You are burning down your buffer time!")
                print(f"[FORECAST]      : System lockdown will execute in {round(remaining_youtube, 1)}s.")
                print(f"[ACTION PLAN]   : Minimize Edge immediately and return to coding context.")
                
            elif "Visual Studio Code" in (current_window or ""):
                if remaining_code > 0:
                    print(f"[PREDICTION]    : Good. Productive coding block detected.")
                    print(f"[FORECAST]      : Complete {round(remaining_code/60, 1)} more minutes to clear today's core milestone.")
                else:
                    print(f"[PREDICTION]    : Production target achieved! You are clear for the day.")
                    print(f"[FORECAST]      : System safe from unexpected lockdowns.")
                print(f"[ACTION PLAN]   : Keep pushing the current codebase architecture forward.")
                
            else:
                print(f"[PREDICTION]    : Neutral operational state.")
                print(f"[FORECAST]      : Remaining allowance: {round(remaining_youtube/60, 1)}m until hard action takes place.")
                print(f"[ACTION PLAN]   : Switch into an IDE to prevent passive window drift.")
            print("=" * 65 + "\n")

            # --- 5. Trigger System Punishment Array ---
            if youtube_wasted_time > limit:
                print("\n🚨🚨🚨 DISTRACTION LIMIT EXCEEDED! EXECUTING LOCKDOWN PROCEDURES 🚨🚨🚨\n")
                
                try:
                    punish1.trigger_tab_kill()
                except Exception as e:
                    print(f"[ERROR]: Failed executing punish1.py -> {e}")
                    
                try:
                    punish2.trigger_audio_alarm()
                except Exception as e:
                    print(f"[ERROR]: Failed executing punish2.py -> {e}")
                
                # Reset structural dict elements to drop out of continuous breach states smoothly
                youtube_keys = [k for k in data["window_time"].keys() if "YouTube" in k]
                for k in youtube_keys:
                    data["window_time"][k] = 0
                start_time = time.time()

            # --- 6. Save State to JSON Disk ---
            with open(LOG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            print(f"[CRITICAL SYSTEM ERROR]: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    track_and_enforce()