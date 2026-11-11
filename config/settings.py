# config/settings.py
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Database Configuration for SQL Server
DB_CONFIG = {
    'server': os.getenv('DB_SERVER', 'CASEY\\SQLEXPRESS'),
    'database': os.getenv('DB_NAME', 'byte_and_brew_pos'),
    'driver': '{ODBC Driver 17 for SQL Server}'
}

# Brevo Email API Configuration
BREVO_API_KEY = os.getenv('BREVO_API_KEY')
BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL')
BREVO_SENDER_NAME = os.getenv('BREVO_SENDER_NAME', 'Byte and Brew')

COLORS = {
    'coffee_brown': '#8B6F47',
    'dark_coffee': '#705638',
    'light_coffee': '#C8A77B',
    'cream': '#F7F3ED',
    'white': '#FFFFFF',
    'dark_brown_text': '#3E3025',
    'soft_gray': '#E5E0D8',
}

# --- UI/UX THEME ENGINE ---
LIGHT_THEME = {
    'bg_main': '#F9F8F6',       
    'bg_card': '#FFFFFF',       
    'text_main': '#1A1A1A',     
    'text_muted': '#737373',    
    'accent': '#7A5C43',        
    'accent_hover': '#634A35',  
    'accent_fg': '#FFFFFF',     
    'border': '#E5E5E5',        
    'btn_secondary': '#F5F5F5', 
    'btn_secondary_text': '#333333',
    'pill_active_bg': '#7A5C43',
    'pill_active_fg': '#FFFFFF',
    'pill_inactive_bg': '#FFFFFF',
    'pill_inactive_fg': '#555555',
    'cart_bg': '#FFFFFF',
    'img_placeholder': '#F3F4F6',
    'badge_bg': '#F3F4F6',
    'badge_fg': '#6B7280',
    'divider': '#EAEAEA',
    'sidebar_bg': '#3E3025',
    'sidebar_text': '#FFFFFF',
    'sidebar_active_bg': '#8B6F47',
    'sidebar_active_fg': '#FFFFFF',
    'banner_bg': '#F2EDE4',
    'chart_bar': '#D7C8B6',
    'chart_highlight': '#8B6F47',
    'progress_bg': '#EBE6DF',
    'progress_fg': '#8B6F47',
}

DARK_THEME = {
    'bg_main': '#121212',       
    'bg_card': '#1E1E1E',       
    'text_main': '#F5F5F5',     
    'text_muted': '#A3A3A3',    
    'accent': '#C8A77B',        
    'accent_hover': '#B59566',
    'accent_fg': '#121212',     
    'border': '#333333',
    'btn_secondary': '#2D2D2D',
    'btn_secondary_text': '#F5F5F5',
    'pill_active_bg': '#C8A77B',
    'pill_active_fg': '#121212',
    'pill_inactive_bg': '#1E1E1E',
    'pill_inactive_fg': '#A3A3A3',
    'cart_bg': '#1E1E1E',
    'img_placeholder': '#121212',
    'badge_bg': '#2D2D2D',
    'badge_fg': '#A3A3A3',
    'divider': '#333333',
    'sidebar_bg': '#0F172A',
    'sidebar_text': '#F5F5F5',
    'sidebar_active_bg': '#C8A77B',
    'sidebar_active_fg': '#121212',
    'banner_bg': '#2D2521',
    'chart_bar': '#4A3E35',
    'chart_highlight': '#C8A77B',
    'progress_bg': '#332E2A',
    'progress_fg': '#C8A77B',
}

# Application Constants
APP_NAME = "Byte and Brew"
APP_TITLE = "Byte and Brew | Restaurant POS"
RECEIPT_PREFIX = "REC"

# --- GLOBAL APP STATE & PERSISTENCE ---
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'theme_settings.json')

def load_theme_pref():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('is_dark_mode', False)
    except Exception:
        pass
    return False

def save_theme_pref(is_dark):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({'is_dark_mode': is_dark}, f)
    except Exception:
        pass

APP_SETTINGS = {
    'is_dark_mode': load_theme_pref()
}