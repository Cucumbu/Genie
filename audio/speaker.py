import pyttsx3

engine = None
tts_available = True


def _get_engine():
    global engine, tts_available

    if not tts_available:
        return None

    if engine is None:
        try:
            engine = pyttsx3.init()
        except Exception as exc:
            tts_available = False
            print(f"TTS disabled: {exc}")
            return None

    return engine

def speak(text):
    print(f"Genie: {text}")

    current_engine = _get_engine()
    if current_engine is None:
        return

    try:
        current_engine.say(text)
        current_engine.runAndWait()
    except Exception as exc:
        print(f"TTS playback failed: {exc}")