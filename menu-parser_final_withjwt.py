from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
from flask import Flask, request, jsonify
import re
from paddleocr import PaddleOCR
import pandas as pd
from tabulate import tabulate
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image
from mysql.connector import Error
import mysql.connector
import secrets

load_dotenv()

# Database configuration from .env file
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'), 
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'autocommit': True
}

def create_mysql_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def save_menu_to_database(menu_data):
    connection = create_mysql_connection()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO menu_or_services (image_path, category, item_or_service, price, description, vendor_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        records_to_insert = []
        for item in menu_data:
            records_to_insert.append((
                item['image'],
                item['category'],   
                item['item'],
                item['price'],      
                item['description'],
                item['vendor_id']   
            ))
        
        cursor.executemany(insert_query, records_to_insert)
        connection.commit()
        
        return True, f"Inserted {cursor.rowcount} records"
        
    except Error as e:
        return False, f"Database error: {str(e)}"
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)  # Generates a secure random key
jwt = JWTManager(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Enhanced CONFIGURATION
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

def get_fresh_ocr():
    """Get a fresh OCR instance to avoid state issues"""
    return PaddleOCR(use_angle_cls=True, lang='en')

def preprocess_image(image_path):
    """Process image without modifying the original file"""
    base, ext = os.path.splitext(image_path)
    processed_path = base + '_processed' + ext
    
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            img.save(processed_path)
    except Exception as e:
        return image_path
    
    return processed_path

def is_strict_category_header(text):
    """Enhanced category detection with flexible patterns"""
    text_upper = text.strip().upper()
    text_clean = text_upper.replace('.', '').replace('-', '').replace('_', '')
    
    if text_upper in STRICT_CATEGORY_HEADERS or text_clean in STRICT_CATEGORY_HEADERS:
        return True
    
    category_starters = [
        'TANDOORI', 'VEG', 'NON VEG', 'NONVEG', 'CHICKEN', 'SNACKS',
        'EXTRA', 'UTTAR MINI MEALS', 'SOUP', 'NOODLES', 
        'MOCKTAILS', 'CHAATS', 'MAGGI'
    ]
    
    for starter in category_starters:
        if text_upper.startswith(starter):
            remaining = text_upper[len(starter):].strip()
            if not remaining or any(variant in remaining for variant in ['PLAIN', 'BUTTER', 'VEG', 'NON']):
                return True
    
    if text_upper in ['EXTRA', 'EXTRAS', 'DIET MENU', 'UTTAR MINI MEALS']:
        return True
        
    words = text.split()
    if len(words) == 1 and text.isupper() and text_upper in STRICT_CATEGORY_HEADERS:
        return True
    
    return False

def normalize_category(raw):
    """Enhanced normalization with flexible matching"""
    val = str(raw).strip().upper()
    
    if 'VEG' in val and 'NON' in val and len(val.split()) == 2:
        return None
    
    if val.startswith('EXTRA'):
        return 'Extras'
    
    if val in HEADER_TO_ALLOWED_MAP:
        return HEADER_TO_ALLOWED_MAP[val]
    
    if 'EXTRA' in val:
        return 'Extras'
    if 'UTTAR' in val or 'MINI MEAL' in val:
        return 'Uttar Mini Meals'
    if any(food_word in val for food_word in ['PANEER', 'DAL', 'CHHOLE', 'ALOO']):
        return 'Uttar Mini Meals'
    
    return "Menu Items"

def detect_multi_column_variants(line):
    """Enhanced function to detect multi-column price variants"""
    line = line.strip().upper()
    
    multi_patterns = [
        (r'VEG\s+NON[\s-]*VEG', ['Veg', 'Non-Veg']),
        (r'VEG\s+EGG\s+CHICKEN', ['Veg', 'Egg', 'Chicken']),
        (r'WITHOUT\s*CHEESE\s+WITH\s*CHEESE', ['Without Cheese', 'With Cheese']),
        (r'WHITE\s+BROWN', ['White', 'Brown']),
        (r'BREAD.*WHITE.*BROWN', ['White', 'Brown']),
        (r'SWEET[/\s]*SALT', ['Sweet', 'Salt']),
        (r'PLAIN[/\s]*BUTTER', ['Plain', 'Butter']),
        (r'WHEAT[/|\s]*SEMOLINA', ['Wheat', 'Semolina']),
        (r'FULL\s+HALF', ['Full', 'Half']),
        (r'HALF\s+FULL', ['Half', 'Full'])
    ]
    
    for pattern, variants in multi_patterns:
        if re.search(pattern, line):
            return variants
    
    return None

def extract_variants_from_header(line):
    """Enhanced variant extraction supporting multiple separators"""
    multi_variants = detect_multi_column_variants(line)
    if multi_variants:
        return multi_variants
    
    separators = ['/', '|', '-']
    for sep in separators:
        if sep in line:
            parts = [p.strip().capitalize() for p in line.split(sep)]
            if len(parts) == 2 and all(p.upper() in VARIANT_KEYWORDS for p in parts):
                return parts
    
    return None

def parse_multi_column_prices(item_name, price_line, variants):
    """Enhanced parsing with better individual item handling"""
    results = []
    clean_line = re.sub(r'(₹|Rs\.?)', '', price_line)
    prices = re.findall(r'\b\d{2,5}\b', clean_line)
    
    if variants and len(prices) >= len(variants):
        for i, variant in enumerate(variants):
            if i < len(prices):
                results.append({
                    "item": f"{item_name} {variant}",
                    "price": prices[i]
                })
        return results
    
    if prices:
        results.append({
            "item": item_name,
            "price": prices[0]
        })
    
    return results

def extract_boxes(image_path, conf_threshold=0.6):
    try:
        ocr = get_fresh_ocr()
        results = ocr.predict(image_path)
        
        if not results:
            return []
        
        boxes = []
        
        if isinstance(results[0], dict):
            dt_polys = results[0]['dt_polys']
            rec_texts = results[0]['rec_texts']
            rec_scores = results[0]['rec_scores']
            
            for box_points, text, conf in zip(dt_polys, rec_texts, rec_scores):
                if conf >= conf_threshold and text and isinstance(text, str):
                    if hasattr(box_points, 'tolist'):
                        box_points = box_points.tolist()
                    x_center = sum([p[0] for p in box_points]) / len(box_points)
                    y_center = sum([p[1] for p in box_points]) / len(box_points)
                    boxes.append({
                        'text': text.strip(),
                        'conf': conf,
                        'box': box_points,
                        'x': x_center,
                        'y': y_center
                    })
        
        elif isinstance(results[0], list):
            for line in results[0]:
                if not line or len(line) < 2:
                    continue
                box_points = line[0]
                text = line[1][0]
                conf = line[1][1]
                
                if conf >= conf_threshold and text and isinstance(text, str):
                    x_center = sum([p[0] for p in box_points]) / len(box_points)
                    y_center = sum([p[1] for p in box_points]) / len(box_points)
                    boxes.append({
                        'text': text.strip(),
                        'conf': conf,
                        'box': box_points,
                        'x': x_center,
                        'y': y_center
                    })
        
        return boxes
    
    except Exception as e:
        return []

def group_by_rows(boxes, y_thresh=15):
    boxes.sort(key=lambda b: b["y"])
    rows = []
    current_row = []
    last_y = -1000

    for box in boxes:
        if abs(box["y"] - last_y) > y_thresh:
            if current_row:
                rows.append(sorted(current_row, key=lambda b: b["x"]))
            current_row = [box]
        else:
            current_row.append(box)
        last_y = box["y"]

    if current_row:
        rows.append(sorted(current_row, key=lambda b: b["x"]))
    
    return rows

def is_variant_header(line: str) -> bool:
    """Enhanced variant header detection"""
    line_upper = line.upper()
    
    multi_patterns = [
        'VEG NON-VEG', 'VEG EGG CHICKEN', 'WHITE BROWN',
        'WITHOUT CHEESE WITH CHEESE', 'SWEET/SALT', 'PLAIN/BUTTER',
        'WHEAT SEMOLINA', 'VEG NON VEG', 'FULL HALF', 'HALF FULL'
    ]
    
    for pattern in multi_patterns:
        if pattern in line_upper:
            return True
    
    separators = ['/', '|', '-']
    for sep in separators:
        if sep in line:
            parts = [p.strip().upper() for p in line.split(sep)]
            if len(parts) >= 2 and any(p in VARIANT_KEYWORDS for p in parts):
                return True
    
    return False

def assign_categories(rows):
    """Enhanced category assignment with better logic"""
    categorized_rows = []
    current_category = "Menu Items"
    current_variants = None

    for row in rows:
        texts = [b["text"] for b in row]
        full_line = " ".join(texts).strip()

        # Skip time patterns and noise
        if re.match(r'^[\d.:\s]+AM.*?PM.*?$', full_line, re.IGNORECASE):
            continue
            
        if re.search(r'They have Chinese too|BREAD$', full_line, re.IGNORECASE):
            continue

        # Enhanced category detection
        if is_strict_category_header(full_line):
            normalized = normalize_category(full_line)
            if normalized and normalized in ALLOWED_CATEGORIES:
                current_category = normalized
                current_variants = None
                continue

        # Enhanced variant detection
        if is_variant_header(full_line) or 'VEG NON-VEG' in full_line.upper():
            if 'VEG NON-VEG' in full_line.upper() or 'VEG' in full_line.upper() and 'NON' in full_line.upper():
                current_variants = ['Veg', 'Non-Veg']
                continue
            else:
                detected = extract_variants_from_header(full_line)
                if detected:
                    current_variants = detected
                continue

        # Auto-assignment logic
        if current_category == "Menu Items" and re.search(r'\d{2,3}/\d{2,3}', full_line):
            current_category = "Uttar Mini Meals"

        # Price detection
        has_menu_price = bool(re.search(r'(?<!\d:)\b(\d{2,5}(?:\s*[/-]\s*\d{2,5})*)', full_line))
        
        if has_menu_price:
            if re.search(r'choose.*?rice|AM.*?PM', full_line, re.IGNORECASE):
                continue
                
            if current_category in ALLOWED_CATEGORIES:
                for b in row:
                    b["category"] = current_category
                    if current_variants:
                        b["variants_header"] = current_variants
                categorized_rows.append(row)

    return categorized_rows

def clean_text_content(text):
    if not text:
        return ""
    
    noise_patterns = [
        r'choose with either.*?rice?\)',
        r'choose.*?rice?\)',
        r'\([^)]*\d{1,2}:\d{2}[^)]*\)',
        r'\d{1,2}:\d{2}.*?PM?\)',
        r'They have Chinese too!',
        r'BREAD$',
        r'M\.R\.P',
        r'Mineral Water.*Large.*'
    ]
    
    cleaned = text
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned.strip('.,;:-|()')
    
    return cleaned

def is_valid_item(text):
    if not text or len(text.strip()) <= 2:
        return False

    clean_text = clean_text_content(text)
    if not clean_text:
        return False

    if clean_text.isupper() and len(clean_text) <= 3:
        return False

    if re.search(r'\d{1,2}:\d{2}|AM|PM', text, re.IGNORECASE):
        return False

    if text.lower().startswith('choose'):
        return False

    if re.match(r'^\d{1,3}$', text.strip()):
        return False

    skip_patterns = ['They have Chinese too', 'BREAD', 'M.R.P', 'Mineral Water', 'Small/Large']
    if any(pattern.lower() in text.lower() for pattern in skip_patterns):
        return False

    return True

def parse_rows_to_menu(categorized_rows, image_name="unknown"):
    menu = []

    for row_idx, row in enumerate(categorized_rows):
        row.sort(key=lambda b: b["x"])
        full_line = " ".join(b["text"] for b in row).strip()
        
        variants = row[0].get("variants_header", None) if row else None
        current_category = row[0].get("category", "Uncategorized") if row else "Uncategorized"
        
        # Enhanced noise filtering
        if re.search(r'They have Chinese|BREAD$|choose.*?rice|AM.*?PM|M\.?R\.?P|Mineral Water|Small.*Large', full_line, re.IGNORECASE):
            continue

        if current_category not in ALLOWED_CATEGORIES:
            continue

        # Enhanced price pattern for multi-column
        price_pattern = r'(?<!\d:)\b(\d{2,5}(?:\s*[/-]\s*\d{2,5})*)'
        price_matches = list(re.finditer(price_pattern, full_line))

        if price_matches:
            price_start = price_matches[0].start()
            item_chunk = full_line[:price_start].strip(" -–—|,Rs.")
            cleaned_item = clean_text_content(item_chunk)
            
            if cleaned_item and is_valid_item(cleaned_item):
                parsed_items = parse_multi_column_prices(cleaned_item, full_line[price_start:], variants)
                
                for entry in parsed_items:
                    menu.append({
                        "image": image_name,
                        "category": current_category,
                        "item": entry["item"],
                        "price": entry["price"],
                        "description": ""
                    })

    return menu



@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    if username == 'vender' and password == 'password123':
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401


@app.route('/upload-menu', methods=['POST'])
@jwt_required() 

def upload_menu():
    if 'image' not in request.files:
        return jsonify({'error': 'Image file is missing.'}), 400
    if 'vendor_id' not in request.form:
        return jsonify({'error': 'vendor_id is missing.'}), 400

    file = request.files['image']
    vendor_id = request.form['vendor_id']

    if file.filename == '':
        return jsonify({"error": "Empty filename."}), 400

    # Generate unique filename
    import time
    timestamp = int(time.time())
    original_filename = secure_filename(file.filename)
    name, ext = os.path.splitext(original_filename)
    filename = f"{name}_{vendor_id}_{timestamp}{ext}"
    
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(image_path)

    # Process image and extract menu
    processed_image_path = preprocess_image(image_path)
    boxes = extract_boxes(processed_image_path)
    rows = group_by_rows(boxes)
    categorized_rows = assign_categories(rows)
    menu_data = parse_rows_to_menu(categorized_rows, image_name=filename)

    # Add vendor_id to each menu item
    for entry in menu_data:
        entry["vendor_id"] = vendor_id

    if menu_data:
        db_success, db_message = save_menu_to_database(menu_data)
        
        return jsonify({
            "message": "Menu extracted successfully",
            "data": menu_data,
            "records": len(menu_data),
            "database_saved": db_success,      
            "database_message": db_message     
        }), 200
    else:
        return jsonify({
            "message": "No valid menu items detected in allowed categories.",
            "data": [],
            "records": 0,
            "database_saved": False,
            "database_message": "No data to save"
        }), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
