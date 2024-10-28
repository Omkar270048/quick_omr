from flask import Blueprint, request, redirect, render_template, send_from_directory
import pandas as pd
from db_utils import get_db_connection
import os
from flask_login import login_required
upload_bp = Blueprint('upload', __name__)

# Path to the directory containing the CSV template
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'static')

@upload_bp.route('/')
@login_required
def index():
    return redirect('/upload_answer_key')  # Redirect to the upload page

@upload_bp.route('/upload_answer_key', methods=['GET', 'POST'])
@login_required
def upload_answer_key():
    message = None  # Initialize message

    if request.method == 'POST':
        if 'file' not in request.files:
            message = 'No file part'
        else:
            file = request.files['file']

            if file.filename == '':
                message = 'No selected file'
            elif file and file.filename.endswith('.csv'):
                try:
                    # Read the CSV file into a DataFrame
                    df = pd.read_csv(file)

                    # Strip any leading or trailing spaces from column names
                    df.columns = df.columns.str.strip()

                    # Print the column names for debugging
                    print(df.columns)

                    # Parse the 'Exam Date' column and convert to YYYY-MM-DD format
                    df['Exam Date'] = pd.to_datetime(df['Exam Date'], errors='coerce').dt.strftime('%Y-%m-%d')

                    # Connect to the database
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    for _, row in df.iterrows():
                        # Check if the data already exists
                        cursor.execute("""
                            SELECT COUNT(*) FROM answer_key 
                            WHERE examid = %s AND questionno = %s AND examdate = %s
                        """, (
                            row['Exam ID'],
                            row['Question No'],
                            row['Exam Date']
                        ))
                        exists = cursor.fetchone()[0]

                        if exists:
                            message = f'Data for exam ID {row["Exam ID"]}, question {row["Question No"]} already exists.'
                        else:
                            # Insert data into the database
                            cursor.execute("""
                                INSERT INTO answer_key (examid, questionno, correctoption, marks, examdate)
                                VALUES (%s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                correctoption = VALUES(correctoption),
                                marks = VALUES(marks),
                                examdate = VALUES(examdate)
                            """, (
                                row['Exam ID'],
                                row['Question No'],
                                row['Answer Key'],
                                row['Marks'],
                                row['Exam Date']
                            ))

                    conn.commit()
                    cursor.close()
                    conn.close()

                    if message is None:
                        message = 'File successfully uploaded and data saved!'

                except Exception as e:
                    message = f'Error: {e}'
            else:
                message = 'Invalid file format. Please upload a CSV file.'

    return render_template('uploadanswerkey.html', message=message)

@upload_bp.route('/download_template')
@login_required
def download_template():
    return send_from_directory(TEMPLATE_DIR, 'template.csv', as_attachment=True)
