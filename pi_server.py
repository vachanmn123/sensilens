# pi_sound_server.py
from flask import Flask, request
from tts import play_tts, play_distance_beep

app = Flask(__name__)


@app.route("/tts", methods=["POST"])
def tts():
    text = request.json["text"]
    play_tts(text)
    return "OK"


@app.route("/beep", methods=["POST"])
def beep():
    data = request.json
    play_distance_beep(
        data.get("speed", 1.0), data.get("x_dist", 0.0), data.get("depth", 0.0)
    )
    return "OK"


app.run(host="0.0.0.0", port=5000)
