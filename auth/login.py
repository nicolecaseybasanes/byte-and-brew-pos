# auth/login.py
from database.connection import get_db_connection
from utils.security import verify_password

def authenticate_user(email: str, password: str, expected_role: str):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed.", None

    cursor = conn.cursor()
    try:
        query = "SELECT user_id, full_name, email, password_hash, role, is_active FROM users WHERE email = ?"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if not user:
            return False, "Invalid email or password.", None

        if user[4] != expected_role:
            return False, f"This account is not authorized as {expected_role}.", None

        if not user[5]:
            return False, "This account has been disabled.", None

        # Check if the password hash in the database is actually valid
        try:
            if not verify_password(password, user[3]):
                return False, "Invalid email or password.", None
        except ValueError:
            return False, "Database error: The password hash stored for this account is invalid. Please update it in SSMS.", None

        return True, "Login successful.", {
            'user_id': user[0], 'full_name': user[1], 'email': user[2], 'role': user[4]
        }
    except Exception as e:
        print(f"Login error: {e}")
        return False, "An internal error occurred.", None
    finally:
        cursor.close()
        conn.close()