import threading
from datetime import datetime
from pathlib import Path

from meeting.join import join_meeting
from audio.listener import listen, preload_model
from audio.speaker import speak
from ai.wakeword import is_called, extract_query
from ai.brain import generate_response, generate_meeting_notes

conversation_context = []
END_COMMANDS = ["genie stop", "genie end meeting", "genie finish"]


def save_notes(conversation_lines):
    notes_dir = Path("notes")
    notes_dir.mkdir(parents=True, exist_ok=True)

    transcript = "\n".join(conversation_lines)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    notes_path = notes_dir / f"meeting_notes_{timestamp}.md"

    try:
        notes = generate_meeting_notes(transcript)
    except Exception as exc:
        notes = f"Could not generate AI notes: {exc}\n\nTranscript:\n{transcript}"

    with notes_path.open("w", encoding="utf-8") as file:
        file.write(notes)

    print(f"Saved notes to {notes_path}")

def handle_text(text):
    global conversation_context

    conversation_context.append(text)
    conversation_context[:] = conversation_context[-200:]

    if any(command in text for command in END_COMMANDS):
        print("End command heard. Finishing meeting workflow...")
        return False

    if is_called(text):
        query = extract_query(text)

        if not query:
            return True
        
        print("Query:", query)

        context = "\n".join(conversation_context)

        response = generate_response(query, context)

        speak(response)

    return True

def main():
    print("Starting Genie...")
    threading.Thread(target=preload_model, daemon=True).start()
    joined = join_meeting()
    if not joined:
        print("Genie did not join the meeting. Stopping to avoid running without a call.")
        return

    try:
        listen(handle_text)
    except KeyboardInterrupt:
        print("Interrupted by user. Finishing up...")
    finally:
        save_notes(conversation_context)

if __name__ == "__main__":
    main()
