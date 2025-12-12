import requests
from threading import Thread


def play_tts(text: str):
    def _send_req():
        requests.post("http://raspberrypi.local:5000/tts", json={"text": text})

    Thread(target=_send_req).start()


def play_distance_beep(speed: float, x_dist: float = 0.0, depth: float = 0.0):
    def _send_req():
        requests.post(
            "http://raspberrypi.local:5000/beep",
            json={"speed": speed, "x_dist": x_dist, "depth": depth},
        )

    Thread(target=_send_req).start()
