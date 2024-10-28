from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import omr_processing
import omr_top
from text_extract import process_image
from results import results_bp
from uploadanswerkey import upload_bp
from new_results import new_results_bp
from auth import auth_bp
from db_utils import get_db_connection
from models import User  # Ensure you have a User model class
import os
from answer_key import answer_key_bp
from view_answer_key import view_answer_key_bp
from image_deleter import delete_all_images

app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads/'  # Folder to save uploaded images
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads/')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB limit
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Redirect to login page if not authenticated

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Register blueprints
app.register_blueprint(results_bp)
app.register_blueprint(upload_bp, url_prefix='/upload')
app.register_blueprint(new_results_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(answer_key_bp, url_prefix='/answer_key')
app.register_blueprint(view_answer_key_bp)


@login_manager.user_loader
def load_user(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, username, email, is_active, password_hash FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    connection.close()

    if user_data:
        return User(
            user_data['id'],
            user_data['username'],
            user_data['email'],
            user_data['is_active'],
            user_data['password_hash']
        )
    return None




# def record_exists(exam_id, name, admissionno, question_no):
#     connection = get_db_connection()
#     cursor = connection.cursor()
#     cursor.execute("""
#         SELECT COUNT(*) FROM student_data
#         WHERE examid = %s AND name = %s AND admissionno = %s AND question_no = %s
#     """, (exam_id, name, admissionno, question_no))
#     exists = cursor.fetchone()[0] > 0
#     cursor.close()
#     connection.close()
#     return exists

def insert_data(exam_id, name, admissionno, exam_date, omr_data):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            examid VARCHAR(255),
            name VARCHAR(255),
            admissionno VARCHAR(255),
            date DATE,
            question_no VARCHAR(255),
            answer VARCHAR(255),
            UNIQUE KEY (examid, name, admissionno, question_no)  -- Ensures no duplicate entries for the same question
        )
    """)

    # Insert records
    for question_no, answer in omr_data.items():
        # if not record_exists(exam_id, name, admissionno, question_no):
            cursor.execute("""
                INSERT INTO student_data (examid, name, admissionno, date, question_no, answer)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (exam_id, name, admissionno, exam_date, question_no, answer))

    connection.commit()
    cursor.close()
    connection.close()
    # delete_all_images()
    delete_all_images(app.config['UPLOAD_FOLDER'])  

def insert_answer_keys(exam_id, exam_date, answer_keys):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answer_key (
            id INT AUTO_INCREMENT PRIMARY KEY,
            examid VARCHAR(255),
            questionno INT,
            correctoption VARCHAR(255),
            marks INT,
            examdate DATE,
            UNIQUE KEY (examid, questionno)  -- Ensure no duplicate entries for the same question
        )
    """)

    # Insert or update each answer key
    for question_no, data in answer_keys.items():
        correct_option = data.get('correct_option')
        marks = data.get('marks')
        cursor.execute("""
            INSERT INTO answer_key (examid, questionno, correctoption, marks, examdate)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE correctoption = VALUES(correctoption), marks = VALUES(marks), examdate = VALUES(examdate)
        """, (exam_id, question_no, correct_option, marks, exam_date))

    connection.commit()
    cursor.close()
    connection.close()

@app.route('/answer_key', methods=['GET', 'POST'])
@login_required
def answer_key():
    if request.method == 'POST':
        exam_id = request.form.get('examid')
        exam_date = request.form.get('exam_date')
        answer_keys = {}

        for i in range(1, 101):  # Adjust based on the number of questions in the form
            question_no = request.form.get(f'question_no{i}')
            correct_option = request.form.get(f'answer_key{i}')
            marks = request.form.get(f'marks{i}')

            if question_no and correct_option and marks:  # Ensure all fields are filled
                answer_keys[question_no] = {
                    'correct_option': correct_option,
                    'marks': marks
                }

        if answer_keys:
            insert_answer_keys(exam_id, exam_date, answer_keys)
            return redirect(url_for('answer_key'))

    return render_template('answer_key.html')

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    existing_files = []  # Initialize with an empty list by default
    exam_ids = []  # List to store available exam IDs

    # Fetch available exam IDs from the answer_key table
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT examid FROM answer_key")
    exam_ids = [row[0] for row in cursor.fetchall()]  # Access the first element of each tuple
    cursor.close()
    connection.close()

    if request.method == 'POST':
        if 'files' not in request.files:
            return render_template('index.html', existing_files=existing_files, exam_ids=exam_ids, error="No file part")

        files = request.files.getlist('files')  # Get list of uploaded files
        if not files:
            return render_template('index.html', existing_files=existing_files, exam_ids=exam_ids, error="No selected file")

        exam_id = request.form.get('examid')  # Get exam ID from form
        exam_date = request.form.get('exam_date')  # Get exam date from form

        for file in files:
            if allowed_file(file.filename):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                file.save(filepath)

                # Process OMR image
                omr_processing.process_image(filepath)
                omr_data = omr_processing.answer
                admission_no = omr_top.process_image(filepath)

                # Process image for text extraction
                text_data = process_image(filepath)

                # Check if data already exists
                # if any(record_exists(exam_id, text_data['name'], admission_no, q_no) for q_no in omr_data.keys()):
                #     existing_files.append(file.filename)
                # else:
                    # Insert data into MySQL
                insert_data(exam_id, text_data['name'], admission_no, exam_date, omr_data)

        if existing_files:
            # Pass the existing files to the template to show the popup
            return render_template('index.html', existing_files=existing_files, exam_ids=exam_ids)

        # If no existing files, show results
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                student_data.examid,
                student_data.name,
                student_data.admissionno,
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
            WHERE student_data.examid = %s AND student_data.date = %s
            GROUP BY student_data.examid, student_data.name, student_data.admissionno, student_data.date
        """, (exam_id, exam_date))
        specific_file_results = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template('result.html', results=specific_file_results, text_data=text_data)

    return render_template('index.html', existing_files=existing_files, exam_ids=exam_ids)


def allowed_file(filename):
    return filename.lower().endswith(('.png', '.jpg', '.jpeg'))

if __name__ == "__main__":
    app.run(debug=True)
