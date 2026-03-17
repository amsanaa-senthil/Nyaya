from pydantic import BaseModel
from typing import List, Optional

class OptionCreate(BaseModel):
    option_text: str
    is_correct: bool

class QuestionCreate(BaseModel):
    question_text: str
    options: List[OptionCreate]

class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class OptionResponse(BaseModel):
    id: str
    option_text: str
    is_correct: bool

class QuestionResponse(BaseModel):
    id: str
    question_text: str
    options: List[OptionResponse]

class QuizResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    question_count: int