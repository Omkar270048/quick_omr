# form_module.py
from flask import Blueprint, render_template, request, redirect, url_for
from db_utils import get_db_connection

form_bp = Blueprint('form_bp', __name__)

@form_bp.route('/new_form', methods=['GET', 'POST'])
def new_form():
    if request.method == 'POST':
        exam_id = request.form['exam_id']
        question_no = request.form['question_no']
        exam_date = request.form['exam_date']
        answer_key = request.form['answer_key']
        question_marks = request.form['question_marks']

        # Use the get_db_connection function from dbutils to get the database connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO students (Exam_Id, question_no, exam_date, answer_key, question_marks) VALUES (%s, %s, %s, %s, %s)",
            (exam_id, question_no, exam_date, answer_key, question_marks)
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('form_bp.new_form'))

    return render_template('form.html')
