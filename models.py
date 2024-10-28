from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db_utils import get_db_connection

class User(UserMixin):
    def __init__(self, id, username, email, is_active, password_hash=None):
        self.id = id
        self.username = username
        self.email = email
        self._is_active = is_active  # Use a private attribute for is_active
        self.password_hash = password_hash  # Added to handle password hash

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    @staticmethod
    def get_user_by_email(email):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        connection.close()

        if user_data:
            return User(
                user_data['id'],
                user_data['username'],
                user_data['email'],
                user_data['is_active'],
                user_data['password_hash']  # Added to include password hash
            )
        return None

    @staticmethod
    def verify_password(stored_password_hash, provided_password):
        return check_password_hash(stored_password_hash, provided_password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash:
            return self.verify_password(self.password_hash, password)
        return False
