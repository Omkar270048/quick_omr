from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from db_utils import get_db_connection
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, password_hash, is_active FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        connection.close()

        if user_data and (user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'], user_data['email'], user_data['is_active'])
            login_user(user)
            return redirect(url_for('index'))  # Adjusted to 'index' endpoint
        else:
            flash('Invalid email or password.', 'login_error')  # Flash with a specific category

    return render_template('login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        #hashed_password = generate_password_hash(password)
        hashed_password = (password)

        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if email already exists
        cursor.execute('SELECT email FROM users WHERE email = %s', (email,))
        email_exists = cursor.fetchone()
        
        if email_exists:
            flash('Email already exists. Please use a different email.', 'register_error')
            cursor.close()
            connection.close()
            return render_template('register.html')

        # Insert new user if email does not exist
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, %s, %s)',
                (username, email, hashed_password, True)  # Assuming new users are active by default
            )
            connection.commit()
            flash('Registration successful. You can now log in.', 'register_success')
            cursor.close()
            connection.close()
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'register_error')
            cursor.close()
            connection.close()
    
    return render_template('register.html')
