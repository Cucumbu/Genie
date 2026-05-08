import warnings
import threading
import time
import numpy as np
from config import (
    AUDIO_SOURCE,
    AZURE_SPEECH_KEY,
    AZURE_SPEECH_LANGUAGE,
    AZURE_SPEECH_REGION,
    MODEL_SIZE,
    STT_PROVIDER,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
)

try:
    from soundcard.mediafoundation import SoundcardRuntimeWarning
except Exception:
    SoundcardRuntimeWarning = Warning

# soundcard installs this warning as "always" on some setups, so ignore by category.
warnings.simplefilter("ignore", SoundcardRuntimeWarning)
warnings.filterwarnings(
    "ignore",
    category=SoundcardRuntimeWarning,
    module=r"soundcard\.mediafoundation",
)
_whisper_model = None   

def _get_recorder_source():
    import soundcard as sc
    if AUDIO_SOURCE == "microphone":
        microphone= sc.default_microphone()
        print(f"Listening from microphone: {microphone.name}")
        return microphone
    speaker = sc.default_speaker()

    try:
        loopback = sc.get_microphone(str(speaker.name), include_loopback=True)
        print(f"Listening from speaker loopback: {speaker.name}")
        return loopback
    except Exception as exc:
        print(f"Loopback capture unavailable ({exc}). Falling back to default microphone.")
        microphone = sc.default_microphone()
        print(f"Listening from microphone: {microphone.name}")
        return microphone

def _float32_to_pcm16(audio: np.ndarray) -> bytes:
    audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
    audio = np.clip(audio, -1.0, 1.0)
    pcm16 = (audio * 32767).astype(np.int16)
    return pcm16.tobytes()

def _get_whisper_model():
    global _whisper_model

    if _whisper_model is None:
        print(
            f"Loading speech model ({MODEL_SIZE}) on {WHISPER_DEVICE} "
            f"with compute type {WHISPER_COMPUTE_TYPE}..."
        )
        from faster_whisper import WhisperModel

        _whisper_model = WhisperModel(
            MODEL_SIZE,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )

    return _whisper_model

def preload_model():
    if STT_PROVIDER == "azure":
        print("Using Azure Speech for STT. No local model to preload.")
        return
    
    if STT_PROVIDER == "whisper":
        try:
            _get_whisper_model()
        except Exception as exc:
            print(f"Failed to load Whisper model: {exc}")
        return
    print(f"Unknown STT_PROVIDER={STT_PROVIDER}. No model to preload.")

def _listen_with_whisper(callback):
    recorder_source = _get_recorder_source()
    speech_model = _get_whisper_model()

    with recorder_source.recorder(samplerate=16000) as mic:
        print("Listening...")
        while True:
            data = mic.record(numframes=16000)
            audio = np.asarray(data[:, 0], dtype=np.float32)

            if audio.size == 0:
                continue

            if np.max(np.abs(audio)) < 0.01:
                continue

            try:
                segments, _ = speech_model.transcribe(audio, beam_size=1)
            except Exception as exc:
                print(f"Transcription failed: {exc}")
                continue

            for segment in segments:
                text = segment.text.strip().lower()
                if text:
                    print(f"User: {text}")
                    should_continue = callback(text)
                    if should_continue is False:
                        print("Stopping listener...")
                        return
                    
def _listen_with_azure(callback):
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        raise RuntimeError("Azure Speech key and region must be set for Azure STT.")
    import azure.cognitiveservices.speech as speechsdk

    recorder_source = _get_recorder_source()
    stop_event = threading.Event()

    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION,
        )
    speech_config.speech_recognition_language = AZURE_SPEECH_LANGUAGE or "en-US"

    stream_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)

    push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    def recognized(evt):
        if evt.result.reason != speechsdk.ResultReason.RecognizedSpeech:
            return
        text = evt.result.text.strip().lower()
        if not text:
            return
        print(f"User: {text}")
        try:
            should_continue = callback(text)
        except Exception as exc:
            print(f"Error in callback: {exc}")
            should_continue = True

        if should_continue is False:
            stop_event.set()
    
    def canceled(evt):
        print(f"Speech recognition canceled: {evt.reason}")
        if evt.error_details:
            print(f"Error details: {evt.error_details}")
        stop_event.set()
    
    def session_stopped(evt):
        print("Speech recognition session stopped.")
        stop_event.set()
    
    recognizer.recognized.connect(recognized)
    recognizer.canceled.connect(canceled)
    recognizer.session_stopped.connect(session_stopped)
    recognizer.start_continuous_recognition()
    print("Listening with Azure Speech...")

    try:
        with recorder_source.recorder(samplerate=16000) as mic:
            while not stop_event.is_set():
                data = mic.record(numframes=16000)

                if data.size == 0:
                    continue
                audio = np.asarray(data[:, 0], dtype=np.float32)
                
                if np.max(np.abs(audio)) < 0.005:
                    continue

                pcm_data = _float32_to_pcm16(audio)
                push_stream.write(pcm_data)
    finally:
        push_stream.close()
        recognizer.stop_continuous_recognition()
        print("Listener stopped.")

def listen(callback):
    if STT_PROVIDER == "azure":
        _listen_with_azure(callback)
    else:
        _listen_with_whisper(callback)

    raise RuntimeError(f"Unsupported STT provider: {STT_PROVIDER}")