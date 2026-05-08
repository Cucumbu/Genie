import pyttsx3

from config import (
    AZURE_SPEECH_KEY,
    AZURE_SPEECH_REGION,
    AZURE_SPEECH_VOICE,
    TTS_ENABLED,
    TTS_PROVIDER,
)

_pyttsx3_engine = None
_pyttsx3_available = True

def _speak_with_pyttsx3(text: str):
    global _pyttsx3_engine, _pyttsx3_available

    if not _pyttsx3_available:
        return

    if _pyttsx3_engine is None:
        try:
            _pyttsx3_engine = pyttsx3.init()

        except Exception as exc:
            _pyttsx3_available = False
            print(f"pyttsx3 initialization failed: {exc}")
            return

    try:
        _pyttsx3_engine.say(text)
        _pyttsx3_engine.runAndWait()
    except Exception as exc:
        print(f"pyttsx3 playback failed: {exc}")

def _speak_with_azure(text: str):
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print("Azure Speech credentials not set. Cannot speak.")
        return
    try:
        import azure.cognitiveservices.speech as speechsdk

        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION,
        )
        speech_config.speech_synthesis_voice_name = AZURE_SPEECH_VOICE
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config,audio_config=audio_config)
        result = synthesizer.speak_text_async(text).get()

        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"Azure TTS failed: {result.reason}")
    except Exception as exc:
        print(f"Azure TTS error: {exc}")

def speak(text:str):
    print(f"Genie: {text}")

    if not TTS_ENABLED or TTS_PROVIDER == "none":
        return
    
    if TTS_PROVIDER == "azure":
        _speak_with_azure(text)
    
    if TTS_PROVIDER == "pyttsx3":
        _speak_with_pyttsx3(text)
    
    print(f"Unknown TTS_PROVIDER={TTS_PROVIDER}. Use azure, pyttsx3, or none.")