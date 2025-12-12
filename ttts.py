from piper import PiperVoice
import wave
from playsound import playsound

text = "Hello, this is a test of the Piper TTS system."

voice = PiperVoice.load("checkpoints/en_US-kristin-medium.onnx")
sound_file = f"sounds/generated/{text}.wav"

with wave.open(sound_file, "wb") as wf:
    voice.synthesize_wav(text, wf)

playsound(sound_file)
