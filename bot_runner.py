import os
from datetime import datetime

from ai.brain import generate_meeting_notes, generate_response
from audio.listener import listen, preload_model
from audio.speaker import speak
from config import (
    BOT_NAME,
    CHAT_REPLY_ENABLED,
    MEETING_LINK,
    TTS_ENABLED,
    VOICE_REPLY_ENABLED,
    WAKE_WORD,
)
from meeting.join import join_meeting, send_chat_message


def run_bot_session(meeting_link: str | None = None, bot_name: str | None = None):
    """
    Starts one Genie bot session.

    This function is used by:
    1. main.py for local/manual testing
    2. api.py when a remote request asks Azure to join a meeting
    """

    meeting_link = meeting_link or MEETING_LINK
    bot_name = bot_name or BOT_NAME

    if not meeting_link:
        raise ValueError("Meeting link is missing. Provide MEETING_LINK in .env or pass meeting_link.")

    print("=" * 60)
    print("Starting Genie bot session")
    print(f"Meeting link: {meeting_link}")
    print(f"Bot name: {bot_name}")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 60)

    transcript_chunks: list[str] = []

    # Store runtime values for modules that still read from env.
    os.environ["MEETING_LINK"] = meeting_link
    os.environ["BOT_NAME"] = bot_name

    # 1. Join Google Meet
    join_meeting(meeting_link=meeting_link, bot_name=bot_name)

    # 2. Preload STT system if needed
    # If STT_PROVIDER=azure, this does nothing.
    # If STT_PROVIDER=whisper, it loads the local model.
    preload_model()

    wake_word = (WAKE_WORD or bot_name).lower().strip()

    def handle_transcript(text: str):
        """
        Called every time Azure Speech / Whisper returns recognized text.
        """

        if not text:
            return True

        clean_text = text.strip()
        lower_text = clean_text.lower()

        print(f"Heard: {clean_text}")

        # Save everything heard for later notes/summary.
        transcript_chunks.append(clean_text)

        # Stop command
        if wake_word in lower_text and any(cmd in lower_text for cmd in ["stop bot", "leave meeting", "end session"]):
            goodbye = "Okay, I am stopping this session."

            if CHAT_REPLY_ENABLED:
                send_chat_message(goodbye)

            if TTS_ENABLED and VOICE_REPLY_ENABLED:
                speak(goodbye)

            _save_summary(transcript_chunks)
            return False

        # Only respond when addressed by wake word.
        if wake_word not in lower_text:
            return True

        question = _extract_question(lower_text, wake_word)

        if not question:
            question = "How can I help?"

        print(f"Question for Genie: {question}")

        context = _build_recent_context(transcript_chunks)

        try:
            answer = generate_response(question, context=context)
        except Exception as exc:
            print(f"AI response failed: {exc}")
            answer = "Sorry, I had trouble generating an answer."

        print(f"Genie answer: {answer}")

        # Chat reply is the easiest and most reliable first reply mode.
        if CHAT_REPLY_ENABLED:
            try:
                send_chat_message(answer)
            except Exception as exc:
                print(f"Failed to send Meet chat message: {exc}")

        # Voice reply needs PulseAudio routing into Meet mic.
        if TTS_ENABLED and VOICE_REPLY_ENABLED:
            speak(answer)

        return True

    try:
        # 3. Start listening loop
        listen(handle_transcript)

    except KeyboardInterrupt:
        print("Bot session interrupted manually.")

    except Exception as exc:
        print(f"Bot session failed: {exc}")
        raise

    finally:
        _save_summary(transcript_chunks)
        print("Genie bot session ended.")


def _extract_question(text: str, wake_word: str) -> str:
    """
    Removes the wake word from recognized text.

    Example:
    'genie what did we decide about pricing'
    -> 'what did we decide about pricing'
    """

    question = text.replace(wake_word, "", 1).strip()

    # Clean common punctuation/noise.
    question = question.lstrip(" ,.:;-")

    return question


def _build_recent_context(transcript_chunks: list[str], max_chunks: int = 20) -> str:
    """
    Builds recent meeting context for the LLM.

    Later, replace this with vector search / pgvector.
    For now, recent context is enough for prototype.
    """

    recent = transcript_chunks[-max_chunks:]

    if not recent:
        return "No meeting context captured yet."

    return "\n".join(recent)


def _save_summary(transcript_chunks: list[str]):
    """
    Saves transcript and meeting summary to notes/.

    This is simple file storage for prototype.
    Later, save to Postgres + Blob Storage.
    """

    if not transcript_chunks:
        print("No transcript captured. Skipping summary.")
        return

    os.makedirs("notes", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    transcript_path = f"notes/transcript_{timestamp}.txt"
    summary_path = f"notes/summary_{timestamp}.md"

    full_transcript = "\n".join(transcript_chunks)

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(full_transcript)

    print(f"Transcript saved: {transcript_path}")

    try:
        summary = generate_meeting_notes(full_transcript)
    except Exception as exc:
        print(f"Summary generation failed: {exc}")
        summary = "Summary generation failed."

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Summary saved: {summary_path}")