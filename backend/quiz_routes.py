from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import SessionLocal
from backend.admin_routes import get_current_admin
from backend.models import Admin
from backend.quiz_schemas import QuizCreate, QuizUpdate, QuizResponse
import uuid

router = APIRouter(prefix="/api/admin/quizzes", tags=["admin-quizzes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def list_quizzes(admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """List all quizzes with question count"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT 
            q.id, 
            q.title, 
            q.description, 
            COUNT(qs.id) as question_count,
            q.created_at
        FROM quizzes2 q
        LEFT JOIN questions qs ON q.id = qs.quiz_id
        GROUP BY q.id, q.title, q.description, q.created_at
        ORDER BY q.created_at DESC
    """))
    
    quizzes = [dict(row) for row in result]
    return quizzes

@router.post("/")
def create_quiz(quiz_data: QuizCreate, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Create a new quiz"""
    from sqlalchemy import text
    
    quiz_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO quizzes2 (id, title, description)
        VALUES (:id, :title, :description)
    """), {"id": quiz_id, "title": quiz_data.title, "description": quiz_data.description})
    
    db.commit()
    return {"id": quiz_id, "title": quiz_data.title, "description": quiz_data.description}

@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: str, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Delete a quiz"""
    from sqlalchemy import text
    
    db.execute(text("DELETE FROM quizzes2 WHERE id = :id"), {"id": quiz_id})
    db.commit()
    return {"message": "Quiz deleted"}