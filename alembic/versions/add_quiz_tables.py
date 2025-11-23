"""add quiz tables

Revision ID: add_quiz_tables
Revises: add_api_analytics
Create Date: 2025-11-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_quiz_tables'
down_revision = 'add_api_analytics'
branch_labels = None
depends_on = None


def upgrade():
    # Create quizzes table
    op.create_table(
        'quizzes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('passing_score', sa.Integer(), nullable=False, server_default='70'),
        sa.Column('max_attempts', sa.Integer(), nullable=True),
        sa.Column('show_correct_answers', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('randomize_questions', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('randomize_options', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('published', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quizzes_course_id', 'quizzes', ['course_id'])
    op.create_index('ix_quizzes_section_id', 'quizzes', ['section_id'])
    
    # Create quiz_questions table
    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(), nullable=False, server_default='multiple_choice'),
        sa.Column('points', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quiz_questions_quiz_id', 'quiz_questions', ['quiz_id'])
    
    # Create quiz_options table
    op.create_table(
        'quiz_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quiz_options_question_id', 'quiz_options', ['question_id'])
    
    # Create quiz_attempts table
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('total_points', sa.Integer(), nullable=False),
        sa.Column('earned_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('time_taken_seconds', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'])
    op.create_index('ix_quiz_attempts_user_id', 'quiz_attempts', ['user_id'])
    op.create_index('ix_quiz_attempts_quiz_user', 'quiz_attempts', ['quiz_id', 'user_id'])
    
    # Create quiz_answers table
    op.create_table(
        'quiz_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attempt_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('selected_option_id', sa.Integer(), nullable=True),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('points_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('answered_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quiz_answers_attempt_id', 'quiz_answers', ['attempt_id'])
    op.create_index('ix_quiz_answers_question_id', 'quiz_answers', ['question_id'])


def downgrade():
    op.drop_index('ix_quiz_answers_question_id', table_name='quiz_answers')
    op.drop_index('ix_quiz_answers_attempt_id', table_name='quiz_answers')
    op.drop_table('quiz_answers')
    
    op.drop_index('ix_quiz_attempts_quiz_user', table_name='quiz_attempts')
    op.drop_index('ix_quiz_attempts_user_id', table_name='quiz_attempts')
    op.drop_index('ix_quiz_attempts_quiz_id', table_name='quiz_attempts')
    op.drop_table('quiz_attempts')
    
    op.drop_index('ix_quiz_options_question_id', table_name='quiz_options')
    op.drop_table('quiz_options')
    
    op.drop_index('ix_quiz_questions_quiz_id', table_name='quiz_questions')
    op.drop_table('quiz_questions')
    
    op.drop_index('ix_quizzes_section_id', table_name='quizzes')
    op.drop_index('ix_quizzes_course_id', table_name='quizzes')
    op.drop_table('quizzes')
