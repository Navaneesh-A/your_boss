from flask import Flask, render_template_string, request
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
LOG_FILE = "productivity_data.json"

def get_ist_date():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d")

def load_data():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                data = json.load(f)
                if "settings" not in data:
                    data["settings"] = {}
                data["settings"]["max_youtube_seconds"] = 1200 # 20 mins production target
                data["settings"]["min_code_seconds"] = 7200    # 2 hours production target
                return data
        except json.JSONDecodeError:
            pass
    return {"daily_records": {}, "settings": {"max_youtube_seconds": 1200, "min_code_seconds": 7200}}

def get_group_details(window_title):
    title_lower = window_title.lower()
    if "visual studio code" in title_lower:
        return "Visual Studio Code", "https://code.visualstudio.com/apple-touch-icon.png"
    if "task switching" in title_lower or "lock screen" in title_lower or "windows" in title_lower:
        return "System (Windows)", "https://upload.wikimedia.org/wikipedia/commons/8/87/Windows_logo_-_2021.svg"
        
    domain_map = {
        "gemini": ("Google Gemini", "gemini.google.com"),
        "github": ("GitHub", "github.com"),
        "youtube": ("YouTube", "youtube.com"),
        "google search": ("Google Search", "google.com"),
        "google": ("Google Search", "google.com"),
        "stackoverflow": ("Stack Overflow", "stackoverflow.com")
    }
    for key, (name, domain) in domain_map.items():
        if key in title_lower:
            return name, f"https://icons.duckduckgo.com/ip3/{domain}.ico"

    return "Web Browsing", "https://cdn-icons-png.flaticon.com/512/6821/6821262.png"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YOUR_BOSS Dashboard</title>
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        if (!urlParams.get('date') || urlParams.get('date') === "{{ today }}") {
            setInterval(function() { window.location.reload(); }, 5000);
        }
        
        function toggleTerminalLogs() {
            const hiddenLogs = document.getElementById("hidden-terminal-logs");
            const btn = document.getElementById("read-more-btn");
            if (hiddenLogs.style.display === "none") {
                hiddenLogs.style.display = "block";
                btn.innerText = "Read Less";
            } else {
                hiddenLogs.style.display = "none";
                btn.innerText = "Read More...";
            }
        }
    </script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; margin: 40px; }
        .container { max-width: 900px; margin: 0 auto; }
        .header-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 30px; }
        h1 { color: #ff3333; margin: 0; }
        .date-picker { background: #1e1e1e; color: #fff; border: 1px solid #444; padding: 8px 12px; border-radius: 4px; font-size: 1rem; cursor: pointer; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 8px; border: 1px solid #333; margin-bottom: 30px; }
        .card h2 { margin-top: 0; color: #00adb5; border-bottom: 1px solid #2a2a2a; padding-bottom: 8px; }
        
        .terminal-box { background: #0c0c0c; border: 1px solid #222; border-radius: 6px; padding: 15px; font-family: 'Courier New', Courier, monospace; color: #39ea49; font-size: 0.9rem; line-height: 1.5; }
        .terminal-line { border-bottom: 1px solid #151515; padding: 6px 0; display: flex; justify-content: space-between; }
        .terminal-text { color: #a5a5a5; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 75%; }
        .terminal-time { color: #ffb400; font-weight: bold; }
        .read-more-link { display: inline-block; margin-top: 12px; color: #00adb5; cursor: pointer; font-weight: bold; text-decoration: underline; }
        
        .recent-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 10px; }
        .recent-box { background: #252525; padding: 15px; border-radius: 6px; border-left: 4px solid #ffb400; }
        .recent-box h4 { margin: 0 0 8px 0; font-size: 0.95rem; color: #ffffff; display: flex; align-items: center; gap: 8px; }
        .recent-box .time-stat { font-size: 1.4rem; font-weight: bold; color: #ffb400; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-row">
            <h1>⚡ YOUR_BOSS Operating Dashboard</h1>
            <form method="GET" action="/">
                <select name="date" class="date-picker" onchange="this.form.submit()">
                    {% for d in available_dates %}
                        <option value="{{ d }}" {% if d == selected_date %}selected{% endif %}>
                            {{ d }} {% if d == today %}(Today - IST){% endif %}
                        </option>
                    {% endfor %}
                </select>
            </form>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>System Rules Configuration</h2>
                <p>⚠️ Distraction Buffer: <strong style="color:#ff3333;">{{ yt_spent|round(1) }}m spent out of {{ (data.get('settings', {}).get('max_youtube_seconds', 1200) / 60)|round(1) }}m</strong></p>
                <p>🎯 Coding Goal: <strong style="color:#39ea49;">{{ code_spent|round(1) }}m completed out of {{ (data.get('settings', {}).get('min_code_seconds', 7200) / 60)|round(1) }}m</strong></p>
            </div>
            <div class="card">
                <h2>Sync Status [{{ selected_date }}]</h2>
                <p>Logged Windows: <strong>{{ raw_windows|length }}</strong></p>
            </div>
        </div>

        <div class="card">
            <h2>🖥️ Live Terminal Activity Stream</h2>
            <div class="terminal-box">
                {% for window, seconds in raw_windows[:5] %}
                <div class="terminal-line">
                    <span class="terminal-text">> tracking: {{ window }}</span>
                    <span class="terminal-time">{{ (seconds / 60)|round(2) }}m</span>
                </div>
                {% endfor %}
                
                <div id="hidden-terminal-logs" style="display: none;">
                    {% for window, seconds in raw_windows[5:] %}
                    <div class="terminal-line">
                        <span class="terminal-text">> tracking: {{ window }}</span>
                        <span class="terminal-time">{{ (seconds / 60)|round(2) }}m</span>
                    </div>
                    {% endfor %}
                </div>
                
                {% if raw_windows|length > 5 %}
                    <div id="read-more-btn" class="read-more-link" onclick="toggleTerminalLogs()">Read More...</div>
                {% endif %}
            </div>
        </div>

        <div class="card">
            <h2>Tracked Application Groups</h2>
            <div class="recent-grid">
                {% for group in groups %}
                <div class="recent-box">
                    <h4><img src="{{ group.icon }}" style="width:16px;height:16px;" alt=""> <span>{{ group.name }}</span></h4>
                    <div class="time-stat">{{ (group.seconds / 60)|round(1) }}m</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    raw_data = load_data()
    today_ist = get_ist_date()
    daily_records = raw_data.get("daily_records", {})
    
    available_dates = sorted(list(daily_records.keys()), reverse=True)
    if today_ist not in available_dates:
        available_dates.insert(0, today_ist)
        
    selected_date = request.args.get('date', today_ist)
    target_day_windows = daily_records.get(selected_date, {})
    
    sorted_raw_windows = sorted(target_day_windows.items(), key=lambda item: item[1], reverse=True)
    
    # Calculate live progress bars for the selected day metrics
    yt_spent = 0
    code_spent = 0
    learning_keywords = ["tutorial", "course", "coding", "learn", "programming", "dev", "data structure", "leetcode"]
    
    grouped_dict = {}
    for window_title, seconds in target_day_windows.items():
        title_lower = window_title.lower()
        
        # Accumulate metrics variables for out-of displays
        if "youtube" in title_lower:
            if any(kw in title_lower for kw in learning_keywords):
                code_spent += seconds
            else:
                yt_spent += seconds
        elif "visual studio code" in title_lower or any(d in title_lower for d in ["github", "gemini", "google search", "stackoverflow"]):
            code_spent += seconds

        group_name, icon_url = get_group_details(window_title)
        if group_name not in grouped_dict:
            grouped_dict[group_name] = {"name": group_name, "icon": icon_url, "seconds": 0}
        grouped_dict[group_name]["seconds"] += seconds
        
    sorted_groups = sorted(grouped_dict.values(), key=lambda x: x["seconds"], reverse=True)
    
    return render_template_string(
        HTML_TEMPLATE, 
        data=raw_data, 
        groups=sorted_groups, 
        raw_windows=sorted_raw_windows, 
        available_dates=available_dates, 
        selected_date=selected_date, 
        today=today_ist,
        yt_spent=(yt_spent / 60),
        code_spent=(code_spent / 60)
    )

if __name__ == '__main__':
    app.run(port=8080, debug=False)