# database/connection.py
import pyodbc
from config.settings import DB_CONFIG

def get_db_connection():
    try:
        # Connects using Windows Authentication (Trusted_Connection)
        conn_str = (
            f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None