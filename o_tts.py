import time

# from playsound import playsound
import os
from threading import Thread
from piper import PiperVoice
import wave
from pydub import AudioSegment
from pydub.playback import play
import simpleaudio as sa

voice = PiperVoice.load("checkpoints/en_US-lessac-high.onnx")

sounds = {}  # Dictionary to cache sound file paths
debounce_map = {}
DEBOUNCE_INTERVAL = 5  # seconds (float)


def synthesize_speech(text: str) -> str:
    if text in sounds:
        return sounds[text]

    sound_file = f"sounds/generated/{text}.wav"

    if os.path.exists(sound_file):
        sounds[text] = sound_file
        return sound_file

    with wave.open(sound_file, "wb") as wf:
        voice.synthesize_wav(text, wf)

    sounds[text] = sound_file
    return sound_file


def _play_distance_beep(speed: float, x_dist: float = 0.0):
    if speed < 0.1:
        return

    # Load the sound file
    sound_file = "sounds/single-beep.mp3"
    beep = AudioSegment.from_file(sound_file)

    # Normalize x_dist (-320 to +320) → (-1.0 to +1.0)
    pan_value = x_dist / 320.0
    pan_value = max(-1.0, min(1.0, pan_value))  # clamp
    print(f"Pan value: {pan_value}")
    beep = beep.pan(pan_value)

    # Decide how many times to play based on speed
    if speed <= 0.5:
        repeat = 1
    elif speed < 1.0:
        repeat = 2
    elif speed < 1.5:
        repeat = 3
    else:
        repeat = 4

    # Convert to raw audio data for simpleaudio
    raw = beep.raw_data
    for _ in range(repeat):
        sa.play_buffer(
            raw,
            num_channels=beep.channels,
            bytes_per_sample=beep.sample_width,
            sample_rate=beep.frame_rate,
        )
        # no wait_done() → allows overlap


def play_distance_beep(speed: float, x_dist: float = 0.0):
    thread = Thread(target=_play_distance_beep, args=(speed, x_dist))
    thread.daemon = True  # ensures thread exits with program
    thread.start()


def _play_tts(text: str):
    start = time.time()
    sound_file = synthesize_speech(text)
    if not os.path.exists(sound_file):
        print(f"Sound file {sound_file} does not exist.")
        return

    # playsound(sound_file)
    audio_segment = AudioSegment.from_wav(sound_file)
    play(audio_segment)
    end = time.time()
    print(f"Time taken to play TTS: {end - start} seconds")


def play_tts(text: str):
    """Play text-to-speech in a separate thread."""
    now = time.time()
    prev_call = debounce_map.get((text,), float("inf"))
    if abs(prev_call - now) > DEBOUNCE_INTERVAL:
        thread = Thread(target=_play_tts, args=(text,))
        thread.start()
        debounce_map[(text,)] = now
    else:
        print(f"{text} was said {abs(prev_call - now)}s ago")
