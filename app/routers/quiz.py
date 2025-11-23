from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Text, Boolean, DateTime, Float, func
from app.services.d1_service import database, metadata
from app.core.dependencies import require_admin, get_current_user

router = APIRouter(prefix="/api", tags=["Quiz"])

# Define quiz tables
quizzes = Table(
    "quizzes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("course_id", Integer, nullable=True),
    Column("section_id", Integer, nullable=True),
    Column("title", String, nullable=False),
    Column("description", Text, nullable=True),
    Column("duration_minutes", Integer, nullable=True),
    Column("passing_score", Integer, nullable=False, server_default="70"),
    Column("max_attempts", Integer, nullable=True),
    Column("show_correct_answers", Boolean, nullable=False, server_default="true"),
    Column("randomize_questions", Boolean, nullable=False, server_default="false"),
    Column("randomize_options", Boolean, nullable=False, server_default="false"),
    Column("published", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
)

quiz_questions = Table(
    "quiz_questions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("quiz_id", Integer, nullable=False),
    Column("question_text", Text, nullable=False),
    Column("question_type", String, nullable=False, server_default="multiple_choice"),
    Column("points", Integer, nullable=False, server_default="1"),
    Column("order", Integer, nullable=False, server_default="0"),
    Column("explanation", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)

quiz_options = Table(
    "quiz_options",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("question_id", Integer, nullable=False),
    Column("option_text", Text, nullable=False),
    Column("is_correct", Boolean, nullable=False, server_default="false"),
    Column("order", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime, server_default=func.now()),
)

quiz_attempts = Table(
    "quiz_attempts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("quiz_id", Integer, nullable=False),
    Column("user_id", Integer, nullable=False),
    Column("score", Float, nullable=True),
    Column("total_points", Integer, nullable=False),
    Column("earned_points", Integer, nullable=False, server_default="0"),
    Column("passed", Boolean, nullable=True),
    Column("started_at", DateTime, server_default=func.now()),
    Column("completed_at", DateTime, nullable=True),
    Column("time_taken_seconds", Integer, nullable=True),
)

quiz_answers = Table(
    "quiz_answers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("attempt_id", Integer, nullable=False),
    Column("question_id", Integer, nullable=False),
    Column("selected_option_id", Integer, nullable=True),
    Column("answer_text", Text, nullable=True),
    Column("is_correct", Boolean, nullable=True),
    Column("points_earned", Integer, nullable=False, server_default="0"),
    Column("answered_at", DateTime, server_default=func.now()),
)

# Pydantic Models
class QuizOptionCreate(BaseModel):
    option_text: str
    is_correct: bool
    order: int = 0

class QuizQuestionCreate(BaseModel):
    question_text: str
    question_type: str = "multiple_choice"
    points: int = 1
    order: int = 0
    explanation: Optional[str] = None
    options: List[QuizOptionCreate] = []

class QuizCreate(BaseModel):
    course_id: Optional[int] = None
    section_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    passing_score: int = 70
    max_attempts: Optional[int] = None
    show_correct_answers: bool = True
    randomize_questions: bool = False
    randomize_options: bool = False
    published: bool = True
    questions: List[QuizQuestionCreate] = []

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    passing_score: Optional[int] = None
    max_attempts: Optional[int] = None
    show_correct_answers: Optional[bool] = None
    randomize_questions: Optional[bool] = None
    randomize_options: Optional[bool] = None
    published: Optional[bool] = None

class AnswerSubmit(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None
    answer_text: Optional[str] = None

class QuizSubmit(BaseModel):
    answers: List[AnswerSubmit]

# Admin Endpoints
@router.get('/admin/quizzes', dependencies=[Depends(require_admin)])
def list_quizzes(course_id: Optional[int] = None):
    """List all quizzes, optionally filtered by course"""
    query = quizzes.select()
    if course_id:
        query = query.where(quizzes.c.course_id == course_id)
    query = query.order_by(quizzes.c.created_at.desc())
    
    result = database.fetch_all(query)
    return {"quizzes": [dict(q) for q in result]}

@router.post('/admin/quizzes', dependencies=[Depends(require_admin)])
def create_quiz(quiz_data: QuizCreate):
    """Create a new quiz with questions and options"""
    # Insert quiz
    quiz_values = quiz_data.dict(exclude={'questions'})
    query = quizzes.insert().values(**quiz_values)
    quiz_id = database.execute(query)
    
    # Insert questions and options
    for question_data in quiz_data.questions:
        options_list = question_data.options
        question_values = question_data.dict(exclude={'options'})
        question_values['quiz_id'] = quiz_id
        
        question_query = quiz_questions.insert().values(**question_values)
        question_id = database.execute(question_query)
        
        # Insert options
        for option_data in options_list:
            option_values = option_data.dict()
            option_values['question_id'] = question_id
            option_query = quiz_options.insert().values(**option_values)
            database.execute(option_query)
    
    return {"id": quiz_id, "message": "Quiz created successfully"}

@router.get('/admin/quizzes/{quiz_id}', dependencies=[Depends(require_admin)])
def get_quiz_with_questions(quiz_id: int):
    """Get quiz details with all questions and options"""
    # Get quiz
    quiz_query = quizzes.select().where(quizzes.c.id == quiz_id)
    quiz = database.fetch_one(quiz_query)
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Get questions
    questions_query = quiz_questions.select().where(
        quiz_questions.c.quiz_id == quiz_id
    ).order_by(quiz_questions.c.order)
    questions_result = database.fetch_all(questions_query)
    
    # Get options for each question
    questions_with_options = []
    for question in questions_result:
        options_query = quiz_options.select().where(
            quiz_options.c.question_id == question['id']
        ).order_by(quiz_options.c.order)
        options_result = database.fetch_all(options_query)
        
        questions_with_options.append({
            **dict(question),
            'options': [dict(opt) for opt in options_result]
        })
    
    return {
        **dict(quiz),
        'questions': questions_with_options
    }

@router.put('/admin/quizzes/{quiz_id}', dependencies=[Depends(require_admin)])
def update_quiz(quiz_id: int, quiz_data: QuizUpdate):
    """Update quiz details"""
    update_values = {k: v for k, v in quiz_data.dict().items() if v is not None}
    if not update_values:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    query = quizzes.update().where(quizzes.c.id == quiz_id).values(**update_values)
    database.execute(query)
    return {"message": "Quiz updated successfully"}

@router.delete('/admin/quizzes/{quiz_id}', dependencies=[Depends(require_admin)])
def delete_quiz(quiz_id: int):
    """Delete a quiz and all related data"""
    # Get all questions for this quiz
    questions_query = quiz_questions.select().where(quiz_questions.c.quiz_id == quiz_id)
    questions_result = database.fetch_all(questions_query)
    
    # Delete options for each question
    for question in questions_result:
        database.execute(quiz_options.delete().where(quiz_options.c.question_id == question['id']))
    
    # Delete questions
    database.execute(quiz_questions.delete().where(quiz_questions.c.quiz_id == quiz_id))
    
    # Delete quiz attempts and answers
    attempts_query = quiz_attempts.select().where(quiz_attempts.c.quiz_id == quiz_id)
    attempts_result = database.fetch_all(attempts_query)
    for attempt in attempts_result:
        database.execute(quiz_answers.delete().where(quiz_answers.c.attempt_id == attempt['id']))
    database.execute(quiz_attempts.delete().where(quiz_attempts.c.quiz_id == quiz_id))
    
    # Delete quiz
    database.execute(quizzes.delete().where(quizzes.c.id == quiz_id))
    return {"message": "Quiz deleted successfully"}

# Student Endpoints
@router.get('/quizzes/{quiz_id}')
def get_quiz_for_student(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Get quiz for student (without correct answers)"""
    # Get quiz
    quiz_query = quizzes.select().where(
        quizzes.c.id == quiz_id,
        quizzes.c.published == True
    )
    quiz = database.fetch_one(quiz_query)
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check attempts limit
    if quiz['max_attempts']:
        attempts_query = quiz_attempts.select().where(
            quiz_attempts.c.quiz_id == quiz_id,
            quiz_attempts.c.user_id == current_user['id']
        )
        attempts_count = len(database.fetch_all(attempts_query))
        if attempts_count >= quiz['max_attempts']:
            raise HTTPException(status_code=403, detail="Maximum attempts reached")
    
    # Get questions
    questions_query = quiz_questions.select().where(
        quiz_questions.c.quiz_id == quiz_id
    ).order_by(quiz_questions.c.order)
    questions_result = database.fetch_all(questions_query)
    
    # Get options (without is_correct field)
    questions_with_options = []
    for question in questions_result:
        options_query = quiz_options.select().where(
            quiz_options.c.question_id == question['id']
        ).order_by(quiz_options.c.order)
        options_result = database.fetch_all(options_query)
        
        # Remove is_correct from options
        options_clean = [{k: v for k, v in dict(opt).items() if k != 'is_correct'} for opt in options_result]
        
        questions_with_options.append({
            **{k: v for k, v in dict(question).items() if k != 'explanation'},
            'options': options_clean
        })
    
    return {
        **{k: v for k, v in dict(quiz).items()},
        'questions': questions_with_options
    }

@router.post('/quizzes/{quiz_id}/start')
def start_quiz_attempt(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Start a new quiz attempt"""
    # Calculate total points
    questions_query = quiz_questions.select().where(quiz_questions.c.quiz_id == quiz_id)
    questions = database.fetch_all(questions_query)
    total_points = sum(q['points'] for q in questions)
    
    # Create attempt
    attempt_values = {
        'quiz_id': quiz_id,
        'user_id': current_user['id'],
        'total_points': total_points,
        'earned_points': 0
    }
    query = quiz_attempts.insert().values(**attempt_values)
    attempt_id = database.execute(query)
    
    return {"attempt_id": attempt_id, "message": "Quiz attempt started"}

@router.post('/quizzes/{quiz_id}/submit')
def submit_quiz(quiz_id: int, submission: QuizSubmit, current_user: dict = Depends(get_current_user)):
    """Submit quiz answers and calculate score"""
    # Get the latest attempt
    attempt_query = quiz_attempts.select().where(
        quiz_attempts.c.quiz_id == quiz_id,
        quiz_attempts.c.user_id == current_user['id'],
        quiz_attempts.c.completed_at == None
    ).order_by(quiz_attempts.c.started_at.desc()).limit(1)
    attempt = database.fetch_one(attempt_query)
    
    if not attempt:
        raise HTTPException(status_code=404, detail="No active quiz attempt found")
    
    # Get quiz details
    quiz_query = quizzes.select().where(quizzes.c.id == quiz_id)
    quiz = database.fetch_one(quiz_query)
    
    # Process answers and calculate score
    earned_points = 0
    
    for answer in submission.answers:
        # Get question
        question_query = quiz_questions.select().where(quiz_questions.c.id == answer.question_id)
        question = database.fetch_one(question_query)
        
        if not question:
            continue
        
        # Check if answer is correct
        is_correct = False
        points_earned = 0
        
        if answer.selected_option_id:
            option_query = quiz_options.select().where(quiz_options.c.id == answer.selected_option_id)
            option = database.fetch_one(option_query)
            
            if option and option['is_correct']:
                is_correct = True
                points_earned = question['points']
                earned_points += points_earned
        
        # Save answer
        answer_values = {
            'attempt_id': attempt['id'],
            'question_id': answer.question_id,
            'selected_option_id': answer.selected_option_id,
            'answer_text': answer.answer_text,
            'is_correct': is_correct,
            'points_earned': points_earned
        }
        database.execute(quiz_answers.insert().values(**answer_values))
    
    # Calculate score percentage
    score = (earned_points / attempt['total_points'] * 100) if attempt['total_points'] > 0 else 0
    passed = score >= quiz['passing_score']
    
    # Calculate time taken
    time_taken = (datetime.now() - attempt['started_at']).total_seconds()
    
    # Update attempt
    update_values = {
        'earned_points': earned_points,
        'score': score,
        'passed': passed,
        'completed_at': datetime.now(),
        'time_taken_seconds': int(time_taken)
    }
    database.execute(
        quiz_attempts.update().where(quiz_attempts.c.id == attempt['id']).values(**update_values)
    )
    
    return {
        "score": score,
        "earned_points": earned_points,
        "total_points": attempt['total_points'],
        "passed": passed,
        "time_taken_seconds": int(time_taken)
    }

@router.get('/quizzes/{quiz_id}/attempts')
def get_quiz_attempts(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Get user's quiz attempts"""
    query = quiz_attempts.select().where(
        quiz_attempts.c.quiz_id == quiz_id,
        quiz_attempts.c.user_id == current_user['id']
    ).order_by(quiz_attempts.c.started_at.desc())
    
    attempts = database.fetch_all(query)
    return {"attempts": [dict(a) for a in attempts]}

@router.get('/quizzes/attempts/{attempt_id}/results')
def get_attempt_results(attempt_id: int, current_user: dict = Depends(get_current_user)):
    """Get detailed results for a quiz attempt"""
    # Get attempt
    attempt_query = quiz_attempts.select().where(quiz_attempts.c.id == attempt_id)
    attempt = database.fetch_one(attempt_query)
    
    if not attempt or attempt['user_id'] != current_user['id']:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    # Get quiz
    quiz_query = quizzes.select().where(quizzes.c.id == attempt['quiz_id'])
    quiz = database.fetch_one(quiz_query)
    
    # Get all answers
    answers_query = quiz_answers.select().where(quiz_answers.c.attempt_id == attempt_id)
    answers = database.fetch_all(answers_query)
    
    # Get questions with correct answers if show_correct_answers is enabled
    results = []
    for answer in answers:
        question_query = quiz_questions.select().where(quiz_questions.c.id == answer['question_id'])
        question = database.fetch_one(question_query)
        
        # Get options
        options_query = quiz_options.select().where(quiz_options.c.question_id == answer['question_id'])
        options = database.fetch_all(options_query)
        
        result_item = {
            **dict(answer),
            'question': dict(question) if quiz['show_correct_answers'] else {k: v for k, v in dict(question).items() if k not in ['explanation']},
            'options': [dict(opt) for opt in options] if quiz['show_correct_answers'] else [{k: v for k, v in dict(opt).items() if k != 'is_correct'} for opt in options]
        }
        results.append(result_item)
    
    return {
        'attempt': dict(attempt),
        'quiz': dict(quiz),
        'results': results
    }
