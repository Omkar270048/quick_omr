from flask import Blueprint, render_template, request, redirect, url_for, flash
from db_utils import get_db_connection
from flask_login import login_required
# Define the Blueprint
view_answer_key_bp = Blueprint('view_answer_key', __name__)

@view_answer_key_bp.route('/view_answer_key', methods=['GET', 'POST'])
@login_required
def view_answer_key():
    per_page = int(request.args.get('per_page', 10))  # Default to 10 items per page
    page = int(request.args.get('page', 1))

    if request.method == 'POST':
        action = request.form.get('action')
        result_id = request.form.get('result_id')

        if action == 'edit':
            examid = request.form.get('examid')
            examdate = request.form.get('examdate')
            questionno = request.form.get('questionno')
            correctoption = request.form.get('correctoption')
            marks = request.form.get('marks')

            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    UPDATE answer_key
                    SET examid = %s, examdate = %s, questionno = %s, correctoption = %s, marks = %s
                    WHERE id = %s
                """, (examid, examdate, questionno, correctoption, marks, result_id))

                conn.commit()
                flash('Result updated successfully.', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'An error occurred: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()

            return redirect(url_for('view_answer_key.view_answer_key'))

        elif action == 'delete':
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("DELETE FROM answer_key WHERE id = %s", (result_id,))
                conn.commit()
                flash('Result deleted successfully.', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'An error occurred: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()

            return redirect(url_for('view_answer_key.view_answer_key'))

    # Handle GET request
    examid = request.args.get('examid', '')
    date = request.args.get('examdate', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch exams for the dropdown
    cursor.execute("SELECT DISTINCT examid FROM answer_key")
    exams = cursor.fetchall()

    query = """
    SELECT 
        answer_key.id,
        answer_key.examid,
        answer_key.examdate,
        answer_key.questionno,
        answer_key.correctoption,
        answer_key.marks
    FROM 
        answer_key
    WHERE 
        (%s = '' OR answer_key.examid = %s)
        AND (%s = '' OR answer_key.examdate = %s)
    LIMIT %s OFFSET %s
    """

    total_query = """
    SELECT COUNT(*) AS total
    FROM answer_key
    WHERE 
        (%s = '' OR answer_key.examid = %s)
        AND (%s = '' OR answer_key.examdate = %s)
    """

    params = (examid, examid, date, date, per_page, (page - 1) * per_page)
    cursor.execute(total_query, (examid, examid, date, date))
    total = cursor.fetchone()['total']
    total_pages = (total + per_page - 1) // per_page

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    # Determine pagination range
    start_page = max(1, page - 5)
    end_page = min(total_pages, page + 5)

    return render_template('view_answer_key.html', exams=exams, examid=examid, date=date, results=results, page=page, total_pages=total_pages, per_page=per_page, start_page=start_page, end_page=end_page)
