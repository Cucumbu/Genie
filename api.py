from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, HttpUrl

from bot_runner import run_bot_session

app = FastAPI(title="Genie Meeting Bot API")

class JoinMeetingRequest(BaseModel):
    meeting_link: HttpUrl
    bot_name: str = "Genie"

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Genie Meeting Bot API is running."}

@app.post("/start-bot")
def start_bot(request: JoinMeetingRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_bot_session, str(request.meeting_link), request.bot_name)
    return {"status": "started", "message": f"Genie is joining the meeting at {request.meeting_link} as {request.bot_name}."}