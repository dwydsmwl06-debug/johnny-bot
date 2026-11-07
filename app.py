import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

CONFIG = {
    "bot_name": "ג'וני",
    "system_prompt": "אתה ג'וני, עוזר קולי חכם, דובר עברית צחה וטבעית, עונה בקצרה ובנעימות.",
    "groq_api_key": os.environ.get("GROQ_API_KEY", "")
}

users_db = {}

@app.route("/", methods=["GET", "POST"])
def yemot_webhook():
    phone = request.values.get("Phone", "unknown")
    if phone not in users_db:
        users_db[phone] = {"quota_seconds": 900, "used_seconds": 0}
        
    user_text = request.values.get("text", "") or request.values.get("response", "")
    
    if not user_text:
        return "read=stt=he-IL=שלום, מה תרצה לשאול את ג'וני?&hangup=no"

    if users_db[phone]["used_seconds"] >= users_db[phone]["quota_seconds"]:
        return "api_text=הסתיימה המכסה שלך לשיחה זו.&hangup=yes"

    bot_reply = "שלום, אני ג'וני."
    if CONFIG["groq_api_key"]:
        try:
            headers = {
                "Authorization": f"Bearer {CONFIG['groq_api_key']}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": f"{CONFIG['system_prompt']} שמך הוא {CONFIG['bot_name']}."},
                    {"role": "user", "content": user_text}
                ]
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            if res.status_code == 200:
                bot_reply = res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            bot_reply = "שגיאה בפנייה למנוע הדיבור."

    return f"api_text={bot_reply}&goto=stt_loop"

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if request.method == "POST":
        CONFIG["bot_name"] = request.form.get("bot_name", CONFIG["bot_name"])
        CONFIG["system_prompt"] = request.form.get("system_prompt", CONFIG["system_prompt"])
        CONFIG["groq_api_key"] = request.form.get("groq_api_key", CONFIG["groq_api_key"])
        
        reset_phone = request.form.get("reset_phone")
        if reset_phone and reset_phone in users_db:
            users_db[reset_phone]["used_seconds"] = 0

    html = """
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>ניהול בוט טלפוני - ג'וני</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f4f9; padding: 20px; direction: rtl; }
            .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            input, textarea { width: 100%; padding: 8px; margin: 8px 0; box-sizing: border-box; }
            button { background: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>ניהול הבוט הטלפוני - ג'וני</h1>
        <div class="card">
            <form method="POST">
                <label>שם הבוט:</label>
                <input type="text" name="bot_name" value="{{ config.bot_name }}">
                
                <label>System Prompt (התנהגות הבוט):</label>
                <textarea name="system_prompt" rows="4">{{ config.system_prompt }}</textarea>
                
                <label>Groq API Key:</label>
                <input type="text" name="groq_api_key" value="{{ config.groq_api_key }}">
                
                <button type="submit">שמור שינויים</button>
            </form>
        </div>
        
        <div class="card">
            <h2>ניהול משתמשים ומכסות (15 דקות ברירת מחדל)</h2>
            <ul>
            {% for phone, data in users.items() %}
                <li>מספר: {{ phone }} | ניצל: {{ data.used_seconds }} שניות 
                    <form method="POST" style="display:inline;">
                        <input type="hidden" name="reset_phone" value="{{ phone }}">
                        <button type="submit" style="background:#f44336; padding:5px 10px; font-size:12px;">איפוס מכסה</button>
                    </form>
                </li>
            {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, config=CONFIG, users=users_db)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
  
