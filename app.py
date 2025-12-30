from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

from interview_logic import EnhancedInterviewEngine
from models import ExperienceLevel

app = FastAPI(title="AI Interview Coach", version="1.0.0")

# Add CORS middleware - THIS IS CRITICAL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize enhanced interview engine
engine = EnhancedInterviewEngine()

class StartInterviewRequest(BaseModel):
    target_role: str
    experience_level: ExperienceLevel

class Answer(BaseModel):
    question_id: str
    question_text: str
    type: str
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    options: Optional[List[str]] = []
    correct_answer: str = ""
    user_answer: str
    time_spent: Optional[float] = 0

class SubmitRoundRequest(BaseModel):
    session_id: str
    answers: List[Answer]
    time_spent: float

@app.get("/")
async def root():
    return {
        "message": "AI Interview Preparation Coach",
        "version": "1.0.0",
        "endpoints": {
            "/start": "Start new interview",
            "/submit": "Submit round answers",
            "/status/{session_id}": "Check session status"
        }
    }

@app.post("/start")
async def start_interview(request: StartInterviewRequest):
    """Start a new interview session"""
    try:
        result = engine.start_interview(
            request.target_role,
            request.experience_level.value
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit")
async def submit_round(request: SubmitRoundRequest):
    """Submit answers for current round"""
    try:
        # Convert answers to dict
        answers_dict = [answer.dict() for answer in request.answers]
        
        result = engine.submit_round(
            request.session_id,
            answers_dict,
            request.time_spent
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{session_id}")
async def get_status(session_id: str):
    """Get interview session status"""
    try:
        status = engine.get_session_status(session_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
