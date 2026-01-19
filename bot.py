
import os
import json
import time
import random
import requests
from datetime import datetime
from flask import Flask, render_template_string
from threading import Thread

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
PIKAMC_SERVER = os.environ.get("PIKAMC_SERVER", "play.pikamc.net")
BOT_NAME = os.environ.get("BOT_NAME", "AI_Minecraft_Bot")

app = Flask(__name__)
bot_logs = []
bot_active = False
bot_memory = []
current_goal = "Khám phá và sinh tồn"

def ask_openai(situation):
    if not OPENAI_API_KEY:
        return get_fallback_action()
    
    prompt = f"""Bạn là {BOT_NAME} chơi Minecraft trên {PIKAMC_SERVER}.
Tình huống: {situation}
Mục tiêu: {current_goal}
Trả về JSON: {{"action": "...", "reason": "...", "chat": "..."}}"""
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
    
    except:
        pass
    
    return get_fallback_action()

def get_fallback_action():
    actions = [
        {"action": "explore", "reason": "Khám phá", "chat": ""},
        {"action": "mine", "reason": "Đào tài nguyên", "chat": ""},
        {"action": "build", "reason": "Xây nhà", "chat": ""},
        {"action": "chat", "reason": "Giao tiếp", "chat": "Xin chào!"}
    ]
    return random.choice(actions)

def add_log(message, log_type="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {"time": timestamp, "message": message, "type": log_type}
    bot_logs.append(log_entry)
    if len(bot_logs) > 100:
        bot_logs.pop(0)
    print(f"[{timestamp}] {message}")
    return log_entry

@app.route('/')
def dashboard():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ bot_name }}</title>
        <style>
            body { font-family: Arial; background: #1a1a2e; color: white; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; 
                   border-radius: 5px; margin: 5px; cursor: pointer; }
            .btn-stop { background: #f44336; }
            .logs { background: black; color: #0f0; padding: 15px; border-radius: 5px; 
                    font-family: monospace; height: 300px; overflow-y: scroll; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 {{ bot_name }}</h1>
            <p>Server: {{ server }}</p>
            <button class="btn" onclick="control('start')">▶ Start</button>
            <button class="btn btn-stop" onclick="control('stop')">⏹ Stop</button>
            <input type="text" id="goal" placeholder="New goal..." style="padding: 10px; width: 300px;">
            <button class="btn" onclick="setGoal()">🎯 Set Goal</button>
            <h3>📝 Logs:</h3>
            <div class="logs" id="logBox">
                {% for log in logs %}
                <div>[{{ log.time }}] {{ log.message }}</div>
                {% endfor %}
            </div>
        </div>
        <script>
            function control(action) {
                fetch('/' + action).then(r => r.text()).then(t => {
                    updateLogs();
                });
            }
            function setGoal() {
                const goal = document.getElementById('goal').value;
                if(goal) {
                    fetch('/goal', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({goal: goal})
                    }).then(() => {
                        document.getElementById('goal').value = '';
                        updateLogs();
                    });
                }
            }
            function updateLogs() {
                fetch('/get_logs').then(r => r.text()).then(t => {
                    document.getElementById('logBox').innerHTML = t;
                });
            }
            setInterval(updateLogs, 3000);
        </script>
    </body>
    </html>
    ''',
    bot_name=BOT_NAME,
    server=PIKAMC_SERVER,
    logs=bot_logs[-20:]
    )

@app.route('/start')
def start():
    global bot_active
    if not bot_active:
        bot_active = True
        Thread(target=bot_loop, daemon=True).start()
        add_log("Bot started", "success")
    return "Bot started"

@app.route('/stop')
def stop():
    global bot_active
    bot_active = False
    add_log("Bot stopped", "warning")
    return "Bot stopped"

@app.route('/goal', methods=['POST'])
def set_goal():
    global current_goal
    try:
        import flask
        data = flask.request.json
        current_goal = data.get('goal', 'Explore')
        add_log(f"New goal: {current_goal}", "success")
        return "Goal updated"
    except:
        return "Error"

@app.route('/get_logs')
def get_logs():
    html = ""
    for log in bot_logs[-20:]:
        html += f'<div>[{log["time"]}] {log["message"]}</div>'
    return html

def bot_loop():
    cycle = 0
    while bot_active:
        try:
            cycle += 1
            situations = [
                "Inventory empty",
                "Found village",
                "Night coming",
                "Low health",
                "Exploring"
            ]
            situation = random.choice(situations)
            action = ask_openai(situation)
            add_log(f"Cycle {cycle}: {action['action']} - {action['reason']}", "info")
            bot_memory.append({
                "cycle": cycle,
                "time": datetime.now().isoformat(),
                "situation": situation,
                "action": action
            })
            if len(bot_memory) > 50:
                bot_memory = bot_memory[-30:]
            time.sleep(30)
        except Exception as e:
            add_log(f"Error: {e}", "error")
            time.sleep(10)

if __name__ == "__main__":
    print(f"🤖 {BOT_NAME} for {PIKAMC_SERVER}")
    if not OPENAI_API_KEY:
        print("⚠️ No OpenAI API Key")
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)                           
                     
