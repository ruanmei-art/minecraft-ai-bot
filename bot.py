

import os
import json
import requests
import random
import time
from datetime import datetime
from flask import Flask, render_template_string
from threading import Thread

# ========== CONFIG ==========
# Lấy từ GitHub Secrets hoặc môi trường
API_KEY = os.environ.get("OPENAI_API_KEY", "")
PIKAMC_SERVER = os.environ.get("PIKAMC_SERVER", "play.pikamc.net")
BOT_NAME = os.environ.get("BOT_NAME", "GitHub_AI_Bot")

# ========== FLASK APP ==========
app = Flask(__name__)

# ========== GLOBAL STATE ==========
activity_logs = []
is_running = False
ai_memory = []
current_goal = "Explore and survive"

# ========== AI CORE ==========
class MinecraftAI:
    def __init__(self):
        self.session = requests.Session()
    
    def ask_openai(self, situation):
        """Gọi OpenAI API để lấy hành động"""
        if not API_KEY:
            return self._fallback_action()
        
        prompt = f"""Bạn là {BOT_NAME}, một AI đang chơi Minecraft trên server {PIKAMC_SERVER}.
        
Tình huống hiện tại: {situation}
Mục tiêu: {current_goal}

Hãy trả về JSON với format:
{{
    "action": "tên_hành_động",
    "reason": "lý_do",
    "chat_message": "tin_nhắn_gửi_chat" (có thể rỗng)
}}

Danh sách hành động có thể:
- explore: Di chuyển khám phá
- mine: Đào khoáng sản
- build: Xây dựng
- craft: Chế tạo
- hunt: Săn bắn
- trade: Giao dịch
- chat: Nói chuyện
"""
        
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "Bạn là một AI chơi Minecraft. Luôn trả về JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 300
            }
            
            response = self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Tìm JSON trong response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
        except Exception as e:
            log_message(f"AI Error: {str(e)[:50]}", "error")
        
        return self._fallback_action()
    
    def _fallback_action(self):
        """Hành động mặc định khi AI không hoạt động"""
        actions = [
            {"action": "explore", "reason": "Khám phá thế giới", "chat_message": ""},
            {"action": "mine", "reason": "Đào tài nguyên", "chat_message": ""},
            {"action": "build", "reason": "Xây nơi trú ẩn", "chat_message": ""},
            {"action": "chat", "reason": "Giao tiếp", "chat_message": "Xin chào từ GitHub AI Bot!"}
        ]
        return random.choice(actions)

# ========== UTILITIES ==========
def log_message(message, msg_type="info"):
    """Ghi log vào bộ nhớ"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {
        "time": timestamp,
        "message": message,
        "type": msg_type
    }
    activity_logs.append(entry)
    
    # Giới hạn log size
    if len(activity_logs) > 100:
        activity_logs.pop(0)
    
    # In ra console
    print(f"[{timestamp}] {message}")

# ========== WEB ROUTES ==========
@app.route('/')
def dashboard():
    """Trang dashboard điều khiển bot"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ bot_name }} - Minecraft AI Bot</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid rgba(255, 255, 255, 0.2);
            }
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.15);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                transition: transform 0.3s;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
            .stat-card h3 {
                font-size: 1.2rem;
                margin-bottom: 10px;
                opacity: 0.9;
            }
            .stat-value {
                font-size: 2rem;
                font-weight: bold;
            }
            .controls {
                display: flex;
                gap: 15px;
                justify-content: center;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }
            .btn {
                padding: 15px 30px;
                border: none;
                border-radius: 50px;
                font-size: 1.1rem;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .btn-start {
                background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
                color: white;
            }
            .btn-stop {
                background: linear-gradient(135deg, #f44336 0%, #c62828 100%);
                color: white;
            }
            .btn-goal {
                background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
                color: white;
            }
            .btn:hover {
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
            .logs-container {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 15px;
                padding: 20px;
                margin-top: 30px;
            }
            .logs-title {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            .log-box {
                background: rgba(0, 0, 0, 0.5);
                border-radius: 10px;
                padding: 20px;
                height: 400px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
            }
            .log-entry {
                padding: 8px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .log-time {
                color: #4CAF50;
                font-weight: bold;
                margin-right: 10px;
            }
            .log-info { color: #90CAF9; }
            .log-success { color: #4CAF50; }
            .log-warning { color: #FF9800; }
            .log-error { color: #f44336; }
            .goal-input {
                padding: 12px 20px;
                border-radius: 50px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 1rem;
                width: 300px;
                margin-right: 10px;
            }
            .goal-input::placeholder {
                color: rgba(255, 255, 255, 0.7);
            }
            @media (max-width: 768px) {
                .container { padding: 15px; }
                .controls { flex-direction: column; }
                .btn { width: 100%; justify-content: center; }
                .goal-input { width: 100%; margin-bottom: 10px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 {{ bot_name }}</h1>
                <p>OpenAI playing Minecraft on {{ server }}</p>
                <p>Powered by GitHub Codespaces</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>🕒 Status</h3>
                    <div class="stat-value" id="status-indicator">
                        {{ "🟢 ONLINE" if running else "🔴 OFFLINE" }}
                    </div>
                </div>
                <div class="stat-card">
                    <h3>📊 Log Entries</h3>
                    <div class="stat-value" id="log-count">{{ logs|length }}</div>
                </div>
                <div class="stat-card">
                    <h3>🎯 Current Goal</h3>
                    <div class="stat-value" id="current-goal">{{ goal }}</div>
                </div>
                <div class="stat-card">
                    <h3>🌐 Server</h3>
                    <div class="stat-value">{{ server }}</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-start" onclick="controlBot('start')">
                    <span>▶</span> Start AI Bot
                </button>
                <button class="btn btn-stop" onclick="controlBot('stop')">
                    <span>⏹</span> Stop AI
                </button>
                <input type="text" class="goal-input" id="goalInput" 
                       placeholder="Enter new goal...">
                <button class="btn btn-goal" onclick="setGoal()">
                    <span>🎯</span> Set Goal
                </button>
            </div>
            
            <div class="logs-container">
                <div class="logs-title">
                    <h2>📝 Activity Logs</h2>
                    <button class="btn" onclick="clearLogs()" 
                            style="padding: 8px 15px; font-size: 0.9rem;">
                        Clear Logs
                    </button>
                </div>
                <div class="log-box" id="log-box">
                    {% for log in logs %}
                    <div class="log-entry">
                        <span class="log-time">[{{ log.time }}]</span>
                        <span class="log-{{ log.type }}">{{ log.message }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <script>
            function controlBot(action) {
                fetch('/' + action)
                    .then(response => response.text())
                    .then(data => {
                        updateStatus();
                        addLog(`Bot ${action}ed`, 'info');
                    })
                    .catch(error => {
                        addLog(`Error: ${error}`, 'error');
                    });
            }
            
            function setGoal() {
                const goalInput = document.getElementById('goalInput');
                const newGoal = goalInput.value.trim();
                if (newGoal) {
                    fetch('/goal', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({goal: newGoal})
                    })
                    .then(response => response.text())
                    .then(data => {
                        document.getElementById('current-goal').textContent = newGoal;
                        goalInput.value = '';
                        addLog(`New goal: ${newGoal}`, 'success');
                    });
                }
            }
            
            function addLog(message, type) {
                const logBox = document.getElementById('log-box');
                const time = new Date().toLocaleTimeString();
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.innerHTML = `
                    <span class="log-time">[${time}]</span>
                    <span class="log-${type}">${message}</span>
                `;
                logBox.appendChild(logEntry);
                logBox.scrollTop = logBox.scrollHeight;
            }
            
            function clearLogs() {
                fetch('/clear_logs')
                    .then(() => {
                        document.getElementById('log-box').innerHTML = '';
                        addLog('Logs cleared', 'info');
                    });
            }
            
            function updateStatus() {
                fetch('/status')
                    .then(response => response.text())
                    .then(data => {
                        document.getElementById('status-indicator').innerHTML = data;
                    });
            }
            
            // Auto-update logs every 3 seconds
            setInterval(() => {
                fetch('/get_logs')
                    .then(response => response.text())
                    .then(data => {
                        document.getElementById('log-box').innerHTML = data;
                    });
                updateStatus();
            }, 3000);
            
            // Initial load
            updateStatus();
        </script>
    </body>
    </html>
    ''',
    bot_name=BOT_NAME,
    server=PIKAMC_SERVER,
    running=is_running,
    logs=activity_logs[-20:],
    goal=current_goal
)

@app.route('/start')
def start_bot():
    global is_running
    if not is_running:
        is_running = True
        log_message(f"AI bot started on {PIKAMC_SERVER}", "success")
        # Start AI loop in background
        Thread(target=ai_loop, daemon=True).start()
        return "🟢 Bot started"
    return "⚪ Bot already running"

@app.route('/stop')
def stop_bot():
    global is_running
    is_running = False
    log_message("AI bot stopped", "warning")
    return "🔴 Bot stopped"

@app.route('/status')
def get_status():
    return "🟢 ONLINE" if is_running else "🔴 OFFLINE"

@app.route('/goal', methods=['POST'])
def set_goal():
    global current_goal
    try:
        import flask
        data = flask.request.json
        new_goal = data.get('goal', 'Explore')
        current_goal = new_goal
        log_message(f"New goal set: {new_goal}", "success")
        return "Goal updated"
    except:
        return "Error updating goal"

@app.route('/get_logs')
def get_logs_html():
    """Trả về HTML của logs (cho auto-update)"""
    html = ""
    for log in activity_logs[-20:]:
        html += f'''
        <div class="log-entry">
            <span class="log-time">[{log['time']}]</span>
            <span class="log-{log['type']}">{log['message']}</span>
        </div>
        '''
    return html if html else "<div class='log-entry'>No logs yet</div>"

@app.route('/clear_logs')
def clear_logs():
    activity_logs.clear()
    return "Logs cleared"

@app.route('/health')
def health_check():
    """Endpoint cho uptime monitoring"""
    return json.dumps({
        "status": "healthy" if is_running else "stopped",
        "timestamp": datetime.now().isoformat(),
        "logs_count": len(activity_logs),
        "memory_entries": len(ai_memory)
    })

# ========== AI GAMEPLAY LOOP ==========
def ai_loop():
    """Vòng lặp chính của AI bot"""
    ai = MinecraftAI()
    cycle = 0
    
    log_message(f"AI gameplay loop started for {PIKAMC_SERVER}", "success")
    
    while is_running:
        try:
            cycle += 1
            
            # Tạo tình huống ngẫu nhiên
            situations = [
                "Inventory is empty, need resources",
                "Found a village nearby",
                "Night is approaching, need shelter",
                "Health is low, need food",
                "Exploring new terrain",
                "Found cave entrance, should explore",
                "Has enough wood, should craft tools",
                "Encountered mobs, need to fight or flee"
            ]
            
            situation = random.choice(situations)
            
            # Hỏi AI hành động tiếp theo
            log_message(f"Cycle {cycle}: {situation}", "info")
            action_data = ai.ask_openai(situation)
            
            # Ghi log hành động
            log_entry = f"AI chose: {action_data['action']} - {action_data['reason']}"
            log_message(log_entry, "success")
            
            # Nếu có chat message, log riêng
            if action_data.get('chat_message'):
                log_message(f"Chat: {action_data['chat_message']}", "info")
            
            # Lưu vào memory
            ai_memory.append({
                "cycle": cycle,
                "timestamp": datetime.now().isoformat(),
                "situation": situation,
                "action": action_data,
                "goal": current_goal
            })
            
            # Giới hạn memory size
            if len(ai_memory) > 100:
                ai_memory = ai_memory[-50:]
            
            # Chờ giữa các cycle
            time.sleep(30)  # 30 giây mỗi cycle
            
        except Exception as e:
            log_message(f"Error in AI loop: {str(e)[:100]}", "error")
            time.sleep(10)

# ========== MAIN ==========
if __name__ == "__main__":
    # Hiển thị thông tin khởi động
    print("=" * 60)
    print("🤖 MINECRAFT AI BOT - GitHub Codespaces Edition")
    print("=" * 60)
    print(f"Bot Name: {BOT_NAME}")
    print(f"Server: {PIKAMC_SERVER}")
    print(f"OpenAI API: {'✅ Configured' if API_KEY else '❌ Not configured'}")
    print("=" * 60)
    print("🌐 Web Dashboard: http://localhost:8080")
    print("📱 Public URL sẽ hiện ở Ports tab")
    print("=" * 60)
    
    # Kiểm tra API key
    if not API_KEY:
        log_message("WARNING: OPENAI_API_KEY not set!", "error")
        log_message("Add it in GitHub Secrets or .env file", "warning")
    
    # Chạy Flask app
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
