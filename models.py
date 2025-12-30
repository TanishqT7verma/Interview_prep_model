from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"

class QuestionType(str, Enum):
    MCQ = "mcq"
    ONE_WORD = "one_word"
    THEORY = "theory"
    CODE_SNIPPET = "code_snippet"
    OUTPUT_PREDICTION = "output_prediction"
    FILL_BLANK = "fill_blank"
    CODING_PROBLEM = "coding_problem"

class Question(BaseModel):
    id: str
    round_number: int
    type: QuestionType
    text: str
    topic: str
    difficulty: str
    options: Optional[List[str]] = None
    correct_answer: str
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    time_spent: Optional[float] = 0

class RoundResult(BaseModel):
    round_number: int
    score: float
    total_questions: int
    correct_answers: int
    time_spent: float
    questions: List[Question]
    passed: bool

class InterviewSession(BaseModel):
    session_id: str
    target_role: str
    experience_level: ExperienceLevel
    start_time: datetime
    current_round: int = 1
    completed_rounds: List[RoundResult] = []
    is_complete: bool = False

class Feedback(BaseModel):
    score: float
    strongest_topics: List[str]
    weakest_topics: List[str]
    recommendations: List[str]
    time_spent: Dict[str, float]
    detailed_analysis: Optional[str] = ""
