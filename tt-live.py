import requests
import json
import subprocess
import sys
from piper import PiperVoice

voice = PiperVoice.load("checkpoints/en_US-lessac-low.onnx")

question = "How would you build the tallest building ever?"

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer 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",
    "Content-Type": "application/json",
}

payload = {
    "model": "tngtech/deepseek-r1t2-chimera:free",
    "messages": [{"role": "user", "content": question}],
    "stream": True,
}

player = subprocess.Popen(
    [
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-hide_banner",
        "-loglevel",
        "panic",
        "-",
    ],
    stdin=subprocess.PIPE,
)


buffer = ""
try:
    with requests.post(url, headers=headers, json=payload, stream=True) as r:
        print("Response status:", r.status_code)
        for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
            buffer += chunk
            while True:
                try:
                    # Find the next complete SSE line
                    line_end = buffer.find("\n")
                    if line_end == -1:
                        break

                    line = buffer[:line_end].strip()
                    buffer = buffer[line_end + 1 :]

                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            data_obj = json.loads(data)
                            content = data_obj["choices"][0]["delta"].get("content")
                            if content:
                                v = voice.synthesize(content)
                                for v_c in v:
                                    player.stdin.write(v_c.audio_int16_bytes)
                                print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            pass
                except Exception:
                    break
finally:
    print("\n--- Stream ended ---")
