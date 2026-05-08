from openai import AzureOpenAI
from config import API_KEY, AZURE_API_VERSION, BASE_URL, MODEL_NAME

client = AzureOpenAI(
    api_key=API_KEY,
    azure_endpoint=BASE_URL,
    api_version=AZURE_API_VERSION
)

def generate_response(query, context=""):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Genie, a concise helpful AI meeting assistant. "
                "Answer only from the meeting context when possible. "
                "If the meeting context does not contain the answer, say that clearly."
            ),
        },
        {
            "role": "user",
            "content": f"Meeting context:\n{context}\n\nQuestion: {query}",
        },
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
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