import os
import secrets
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))

# Upload Configuration
UPLOAD_FOLDER = 'uploads'

# Auth Credentials
AUTH_USER = 'vender'
AUTH_PASSWORD = 'password123'

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'autocommit': True
}

# Menu Categories
ALLOWED_CATEGORIES = [
    "Snacks", "Starters", "Chinese Starters", "Chinese Main Course",
    "Dosas", "Uttapams", "Sweets", "Beverages", "Extras", 
    "Licksters", "Uttar Mini Meals", "Chaats", "Tikki", "Maggi", 
    "Sandwiches", "Diet Menu", "VEG", "NON VEG", "Noodles", 
    "Mocktails", "Soup", "Menu Items", "Tandoori Snacks", 
    "Veg Snacks", "Non-Veg Snacks"
]

STRICT_CATEGORY_HEADERS = {
    'MOCKTAILS', 'SOUP', 'NOODLES', 'SNACKS', 'TIKKI', 
    'MAGGI', 'SANDWICHES', 'DIET MENU', 'CHAATS', 'EXTRAS', 
    'BEVERAGES', 'SWEETS', 'DOSAS', 'UTTAPAMS', 'STARTERS',
    'EXTRA', 'CHINESE STARTERS', 'CHINESE MAIN COURSE', 
    'LICKSTERS', 'UTTAR MINI MEALS', 'VEG', 'NON VEG',
    'TANDOORISNACKS', 'VEGSNACKS', 'NONVEGSNACKS', 
    'TANDOORI SNACKS', 'VEG SNACKS', 'NON-VEG SNACKS'
}

HEADER_TO_ALLOWED_MAP = {
    'SNACKS': 'Snacks', 'STARTERS': 'Starters',
    'CHINESE STARTERS': 'Chinese Starters', 
    'CHINESE MAIN COURSE': 'Chinese Main Course',
    'SWEETS': 'Sweets', 'BEVERAGES': 'Beverages',
    'DOSAS': 'Dosas', 'DOSA': 'Dosas',
    'UTTAPAMS': 'Uttapams', 'UTTAPAM': 'Uttapams',
    'EXTRAS': 'Extras', 'EXTRA': 'Extras', 
    'LICKSTERS': 'Licksters',
    'UTTAR MINI MEALS': 'Uttar Mini Meals',
    'UTTAR MINI MEAL': 'Uttar Mini Meals',
    'CHAATS': 'Chaats', 'CHAAT': 'Chaats',
    'TIKKI': 'Tikki', 'MAGGI': 'Maggi',
    'SANDWICHES': 'Sandwiches', 'SANDWICH': 'Sandwiches',
    'DIET MENU': 'Diet Menu', 'VEG': 'VEG', 'NON VEG': 'NON VEG',
    'NOODLES': 'Noodles', 'NOODLE': 'Noodles',
    'MOCKTAILS': 'Mocktails', 'MOCKTAIL': 'Mocktails',
    'SOUP': 'Soup', 'SOUPS': 'Soup',
    'TANDOORISNACKS': 'Tandoori Snacks',
    'VEGSNACKS': 'Veg Snacks',
    'NONVEGSNACKS': 'Non-Veg Snacks',
    'TANDOORI SNACKS': 'Tandoori Snacks',
    'VEG SNACKS': 'Veg Snacks',
    'NON-VEG SNACKS': 'Non-Veg Snacks'
}

VARIANT_KEYWORDS = {
    "PLAIN", "BUTTER", "VEG", "CHEESE", "SMALL", "LARGE", 
    "WHEAT", "SEMOLINA", "WITHOUT CHEESE", "WITH CHEESE", 
    "BREAD", "WHITE", "BROWN", "EGG", "CHICKEN", 
    "NON-VEG", "NON VEG", "SWEET", "SALT", "HALF", "FULL"
}
