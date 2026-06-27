from flask import Flask, render_template_string, jsonify
import json
import os
import time

app = Flask(__name__)
LOG_FILE = "productivity_data.json"

def load_data():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {"window_time": {}, "settings": {"max_youtube_seconds": 1200, "min_code_seconds": 7200}}

# HTML Dashboard Template with the new Recent Focus Area
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YOUR_BOSS Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; margin: 40px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #ff3333; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 30px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 8px; border: 1px solid #333; }
        .card h2 { margin-top: 0; color: #00adb5; border-bottom: 1px solid #2a2a2a; padding-bottom: 8px; }
        
        /* Stylized Recent Boxes layout */
        .recent-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 10px; }
        .recent-box { background: #252525; padding: 15px; border-radius: 6px; border-left: 4px solid #ffb400; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
        .recent-box h4 { margin: 0 0 8px 0; font-size: 0.95rem; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .recent-box .time-stat { font-size: 1.4rem; font-weight: bold; color: #ffb400; }
        
        ul { list-style: none; padding: 0; }
        li { padding: 10px; background: #252525; margin-bottom: 8px; border-radius: 4px; display: flex; justify-content: space-between; }
        .time { font-weight: bold; color: #ffb400; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ YOUR_BOSS Operating Dashboard</h1>
        
        <div class="grid">
            <div class="card">
                <h2>System Rules Configuration</h2>
                <p>⚠️ Max Distraction Buffer: <strong>{{ (data.get('settings', {}).get('max_youtube_seconds', 1200) / 60)|round(1) }} mins</strong></p>
                <p>🎯 Daily Coding Goal: <strong>{{ (data.get('settings', {}).get('min_code_seconds', 7200) / 3600)|round(1) }} hours</strong></p>
            </div>
            <div class="card">
                <h2>Sync Status</h2>
                <p>Port 5500 Integration: <span style="color: #39ea49; font-weight:bold;">Active</span></p>
                <p>Logged Windows: <strong>{{ data.window_time|length }}</strong></p>
            </div>
        </div>

        <div class="card" style="margin-bottom: 30px;">
            <h2>Recent Focus Blocks (Active Windows)</h2>
            <div class="recent-grid">
                {% set count = namespace(value=0) %}
                {% for window, seconds in data.window_time.items() %}
                    {# Show the top items that have gathered tracking time #}
                    {% if count.value < 3 and seconds > 5 %}
                        <div class="recent-box">
                            <h4 title="{{ window }}">{{ window.split(' - ')[0] }}</h4>
                            <div class="time-stat">{{ (seconds / 60)|round(1) }}m</div>
                            <div style="font-size: 0.75rem; color: #888; margin-top: 4px;">Total Running Time</div>
                        </div>
                        {% set count.value = count.value + 1 %}
                    {% endif %}
                {% else %}
                    <p style="color: #888;">No recent high-impact active windows tracked yet.</p>
                {% endfor %}
            </div>
        </div>

        <div class="card">
            <h2>Tracked Application Time</h2>
            <ul>
                {% for window, seconds in data.window_time.items() %}
                <li>
                    <span>{{ window }}</span>
                    <span class="time">{{ (seconds / 60)|round(2) }} mins</span>
                </li>
                {% else %}
                <li>No active window sessions recorded yet.</li>
                {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    data = load_data()
    # Sort windows so the ones with active/recent high duration show up first in the boxes
    if "window_time" in data:
        data["window_time"] = dict(sorted(data["window_time"].items(), key=lambda item: item[1], reverse=True))
    return render_template_string(HTML_TEMPLATE, data=data)

if __name__ == '__main__':
    app.run(port=8080, debug=False)