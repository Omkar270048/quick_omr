from flask import Blueprint, render_template, request, send_file
import pandas as pd
import tempfile
from db_utils import get_db_connection
from math import ceil
from flask_login import login_required

# Define the Blueprint
new_results_bp = Blueprint('new_results', __name__)
@new_results_bp.route('/new_results', methods=['GET'])
@login_required
def new_results():
    examid = request.args.get('examid', '')
    date = request.args.get('date', '')
    name = request.args.get('name', '')
    admissionno = request.args.get('admissionno', '')
    page = int(request.args.get('page', 1))  # Default to page 1
    per_page = int(request.args.get('per_page', 10))  # Default to 10 items per page

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Query to get distinct exam IDs for the dropdown
    exam_ids_query = "SELECT DISTINCT examid FROM student_data ORDER BY examid"
    cursor.execute(exam_ids_query)
    exam_ids = cursor.fetchall()
    exam_ids = [row['examid'] for row in exam_ids]

    # Main query with new join
    query = """
    SELECT 
        student_data.examid,
         student_registration.name,
        student_data.admissionno,
        student_registration.class,
        student_registration.section,
        student_data.date,
        COUNT(student_data.question_no) AS total_questions,
        SUM(answer_key.marks) AS total_marks,
        SUM(CASE WHEN student_data.answer = answer_key.correctoption THEN answer_key.marks ELSE 0 END) AS total_obtained_marks
    FROM 
        student_data
    JOIN 
        answer_key 
    ON 
        student_data.question_no = answer_key.questionno 
        AND student_data.examid = answer_key.examid
    JOIN 
        student_registration
    ON 
        student_data.admissionno = student_registration.admission_no
    WHERE 
        (%s = '' OR student_data.examid = %s)
        AND (%s = '' OR student_data.date = %s)
        AND (%s = '' OR student_data.admissionno LIKE %s)
        AND (%s = '' OR student_data.name LIKE %s)
    GROUP BY 
        student_data.examid,  student_registration.name, student_data.admissionno, student_registration.class, student_registration.section, student_data.date
    LIMIT %s OFFSET %s
    """

    # Parameters for the query
    params = (
        examid, examid,  # Exam ID filter
        date, date,      # Date filter
        f'%{admissionno}%', f'%{admissionno}%', # Admission No filter (LIKE clause)
        f'%{name}%', f'%{name}%', # Name filter (LIKE clause)
        per_page, (page - 1) * per_page
    )

    # Count total records for pagination
    total_query = """
    SELECT COUNT(*) AS total
    FROM (
        SELECT DISTINCT student_data.examid,  student_registration.name, student_data.admissionno, student_registration.class, student_registration.section, student_data.date
        FROM student_data
        JOIN answer_key
        ON student_data.question_no = answer_key.questionno
        AND student_data.examid = answer_key.examid
        JOIN student_registration
        ON student_data.admissionno = student_registration.admission_no
        WHERE
            (%s = '' OR student_data.examid = %s)
            AND (%s = '' OR student_data.date = %s)
            AND (%s = '' OR student_data.admissionno LIKE %s)
            AND (%s = '' OR student_data.name LIKE %s)
    ) AS subquery
    """

    cursor.execute(total_query, (examid, examid, date, date, f'%{admissionno}%', f'%{admissionno}%', f'%{name}%', f'%{name}%'))
    total = cursor.fetchone()['total']
    total_pages = (total + per_page - 1) // per_page

    # Calculate pagination range
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)

    if page - 2 < 1:
        end_page = min(total_pages, end_page + (2 - (page - 1)))
        start_page = 1

    if page + 2 > total_pages:
        start_page = max(1, start_page - ((page + 2) - total_pages))
        end_page = total_pages

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('new_results_view.html', results=results, examid=examid, date=date, name=name, admissionno=admissionno, exam_ids=exam_ids, page=page, total_pages=total_pages, start_page=start_page, end_page=end_page, per_page=per_page)

@new_results_bp.route('/export_new_results', methods=['GET'])
@login_required
def export_new_results():
    examid = request.args.get('examid', '')
    date = request.args.get('date', '')
    name = request.args.get('name', '')
    admissionno = request.args.get('admissionno', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch results with the new join
        query = """
        SELECT 
            student_data.examid,
             student_registration.name,
            student_data.admissionno,
            student_registration.class,
            student_registration.section,
            student_data.date,
            COUNT(student_data.question_no) AS total_questions,
            SUM(answer_key.marks) AS total_marks,
            SUM(CASE WHEN student_data.answer = answer_key.correctoption THEN answer_key.marks ELSE 0 END) AS total_obtained_marks
        FROM 
            student_data
        JOIN 
            answer_key 
        ON 
            student_data.question_no = answer_key.questionno 
            AND student_data.examid = answer_key.examid
        JOIN 
            student_registration
        ON 
            student_data.admissionno = student_registration.admission_no
        WHERE 
            (%s = '' OR student_data.examid = %s)
            AND (%s = '' OR student_data.date = %s)
            AND (%s = '' OR student_data.admissionno LIKE %s)
            AND (%s = '' OR student_data.name LIKE %s)
        GROUP BY 
            student_data.examid,  student_registration.name, student_data.admissionno, student_registration.class, student_registration.section, student_data.date
        """

        # Parameters for the query
        params = (
            examid, examid,  # Exam ID filter
            date, date,      # Date filter
            f'%{admissionno}%', f'%{admissionno}%', # Admission No filter (LIKE clause)
            f'%{name}%', f'%{name}%' # Name filter (LIKE clause)
        )

        cursor.execute(query, params)
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert results to DataFrame
        df = pd.DataFrame(results)

        # Save DataFrame to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            with pd.ExcelWriter(tmp_file, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Results')
            tmp_file.flush()
            tmp_file.seek(0)
            return send_file(tmp_file.name, as_attachment=True, download_name='new_omr_results.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        # Log the error
        print(f"An error occurred: {e}")
        return "An error occurred while generating the Excel file.", 500
