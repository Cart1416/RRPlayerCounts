import json
import os
from flask import Flask, request, jsonify, send_from_directory # type: ignore
import threading
import time
import datetime
import requests # type: ignore

with open("config.json", "r") as config:
    configData = json.load(config)

app = Flask(__name__)

def getPlayerCounts():
    os.makedirs("data", exist_ok=True)
    servers = configData.get("servers", {})

    timestamp = int(time.time())

    for name, serverData in servers.items():
        url = serverData.get("url")
        print(name, url)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            payload = response.content

            try:
                data = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                data = payload.decode("utf-8", errors="replace")

            file_path = os.path.join("data", f"{name}.json")

            history = []

            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        history = json.load(file)

                    if not isinstance(history, list):
                        history = []

                except (json.JSONDecodeError, OSError):
                    history = []

            if serverData.get("format") == "simple":
                history.append({
                    "timestamp": timestamp,
                    "data": {"value": data}
                })

                with open(file_path, "w", encoding="utf-8") as output:
                    json.dump(history, output, ensure_ascii=False, indent=2)

            elif serverData.get("format") == "meownet":
                history.append({
                    "timestamp": timestamp,
                    "data": {"value": data.get("count", -1)}
                })

                with open(file_path, "w", encoding="utf-8") as output:
                    json.dump(history, output, ensure_ascii=False, indent=2)

            elif serverData.get("format") == "kittyrec":
                history.append({
                    "timestamp": timestamp,
                    "data": {"value": data.get("online", -1)}
                })

                with open(file_path, "w", encoding="utf-8") as output:
                    json.dump(history, output, ensure_ascii=False, indent=2)

        except Exception as e:
            print(e)
            continue

def getPlayerCountTask():
    oldTime = None

    while True:
        now = datetime.datetime.now()
        if now.minute % 5 == 0:
            currentTime = now.strftime("%Y-%m-%d %H:%M")
            if oldTime != currentTime:
                oldTime = currentTime
                getPlayerCounts()

        time.sleep(1)

@app.route("/", methods=["GET"])
def index():
    return send_from_directory("public", "index.html")

@app.route("/data/<path:filename>", methods=["GET"])
def getData(filename):
    return send_from_directory("data", filename)

@app.route("/config", methods=["GET"])
def getConfig():
    return jsonify(configData)

if __name__ == "__main__":
    thread = threading.Thread(target=getPlayerCountTask, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=4200)