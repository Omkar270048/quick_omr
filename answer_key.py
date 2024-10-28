from flask import Blueprint, request, render_template, redirect, url_for, flash
from db_utils import get_db_connection
from flask_login import login_required
answer_key_bp = Blueprint('answer_key_bp', __name__)

@answer_key_bp.route('/answer_key', methods=['GET', 'POST'])
@login_required
def answer_key():
    if request.method == 'POST':
        exam_id = request.form.get('examid')
        exam_date = request.form.get('exam_date')
        num_questions = int(request.form.get('question_count', 100))  # Default to 10 if not provided
        answer_keys = {}

        # Collect answer keys
        for i in range(1, num_questions + 1):
            question_no = request.form.get(f'question_no{i}')
            correct_option = request.form.get(f'answer_key{i}')
            marks = request.form.get(f'marks{i}')

            if question_no and correct_option and marks:
                answer_keys[question_no] = {
                    'correct_option': correct_option,
                    'marks': marks
                }

        if answer_keys:
            if not exam_id_exists(exam_id):
                insert_answer_keys(exam_id, exam_date, answer_keys)
                flash('Answer key successfully added.', 'success')
            else:
                flash('Exam ID already exists. Please choose a different Exam ID.', 'error')
                
            return redirect(url_for('answer_key_bp.answer_key'))

    return render_template('answer_key.html')

def insert_answer_keys(exam_id, exam_date, answer_keys):
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL query to insert data
    query = """
    INSERT INTO answer_key (examid, questionno, correctoption, marks, examdate)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE correctoption = VALUES(correctoption), marks = VALUES(marks), examdate = VALUES(examdate)
    """

    # Insert or update each answer key
    for question_no, data in answer_keys.items():
        correct_option = data.get('correct_option')
        marks = data.get('marks')
        cursor.execute(query, (exam_id, question_no, correct_option, marks, exam_date))

    conn.commit()
    cursor.close()
    conn.close()

def exam_id_exists(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM answer_key WHERE examid = %s"
    cursor.execute(query, (exam_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count > 0
