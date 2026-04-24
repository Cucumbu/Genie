from openai import OpenAI
from config import HACK_AI_API_KEY, BASE_URL, MODEL_NAME

client = OpenAI(
    api_key=HACK_AI_API_KEY,
    base_url=BASE_URL,
)

def generate_response(query, context=""):
    messages = [
        {"role": "system", "content": "You are a helpful AI meeting assistant."},
        {"role": "user", "content": f"{context}\n\nQuestion: {query}"}
    ]
     
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages
    )
    
    return response.choices[0].message.content.strip()


def generate_meeting_notes(transcript):
    transcript = transcript.strip()
    if not transcript:
        return "No transcript captured for this meeting."

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert meeting assistant. Create concise notes with these sections: "
                "Summary, Key Decisions, Action Items (with owner if possible), and Open Questions."
            ),
        },
        {
            "role": "user",
            "content": f"Meeting transcript:\n\n{transcript}",
        },
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )

    return response.choices[0].message.content.strip()