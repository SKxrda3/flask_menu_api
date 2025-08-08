import re
from config import ALLOWED_CATEGORIES, STRICT_CATEGORY_HEADERS, VARIANT_KEYWORDS
from config import *
import logging


# def group_by_rows(boxes, y_thresh=15):
#     boxes.sort(key=lambda b: b["y"])
#     rows = []
#     current_row = []
#     last_y = -1000

#     for box in boxes:
#         if abs(box["y"] - last_y) > y_thresh:
#             if current_row:
#                 rows.append(sorted(current_row, key=lambda b: b["x"]))
#             current_row = [box]
#         else:
#             current_row.append(box)
#         last_y = box["y"]

#     if current_row:
#         rows.append(sorted(current_row, key=lambda b: b["x"]))
    
#     return rows

def group_by_rows(boxes, y_thresh=15):
    boxes.sort(key=lambda b: b["y"])
    logging.debug(f'Sorting {len(boxes)} boxes by y coordinate')
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
    
    logging.debug(f'Grouped into {len(rows)} rows')
    return rows


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

# def assign_categories(rows):
#     """Enhanced category assignment with better logic"""
#     categorized_rows = []
#     current_category = "Menu Items"
#     current_variants = None

#     for row in rows:
#         texts = [b["text"] for b in row]
#         full_line = " ".join(texts).strip()

#         # Skip time patterns and noise
#         if re.match(r'^[\d.:\s]+AM.*?PM.*?$', full_line, re.IGNORECASE):
#             continue
            
#         if re.search(r'They have Chinese too|BREAD$', full_line, re.IGNORECASE):
#             continue

#         # Enhanced category detection
#         if is_strict_category_header(full_line):
#             normalized = normalize_category(full_line)
#             if normalized and normalized in ALLOWED_CATEGORIES:
#                 current_category = normalized
#                 current_variants = None
#                 continue

#         # Enhanced variant detection
#         if is_variant_header(full_line) or 'VEG NON-VEG' in full_line.upper():
#             if 'VEG NON-VEG' in full_line.upper() or 'VEG' in full_line.upper() and 'NON' in full_line.upper():
#                 current_variants = ['Veg', 'Non-Veg']
#                 continue
#             else:
#                 detected = extract_variants_from_header(full_line)
#                 if detected:
#                     current_variants = detected
#                 continue

#         # Auto-assignment logic
#         if current_category == "Menu Items" and re.search(r'\d{2,3}/\d{2,3}', full_line):
#             current_category = "Uttar Mini Meals"

#         # Price detection
#         has_menu_price = bool(re.search(r'(?<!\d:)\b(\d{2,5}(?:\s*[/-]\s*\d{2,5})*)', full_line))
        
#         if has_menu_price:
#             if re.search(r'choose.*?rice|AM.*?PM', full_line, re.IGNORECASE):
#                 continue
                
#             if current_category in ALLOWED_CATEGORIES:
#                 for b in row:
#                     b["category"] = current_category
#                     if current_variants:
#                         b["variants_header"] = current_variants
#                 categorized_rows.append(row)

#     return categorized_rows


def assign_categories(rows):
    """Enhanced category assignment with better logic"""
    categorized_rows = []
    current_category = "Menu Items"
    current_variants = None
    logging.debug(f'Starting category assignment for {len(rows)} rows')

    for row in rows:
        texts = [b["text"] for b in row]
        full_line = " ".join(texts).strip()

        # Skip time patterns and noise
        if re.match(r'^[\d.:\s]+AM.*?PM.*?$', full_line, re.IGNORECASE):
            logging.debug(f'Skipping time pattern line: {full_line}')
            continue
            
        if re.search(r'They have Chinese too|BREAD$', full_line, re.IGNORECASE):
            logging.debug(f'Skipping noise line: {full_line}')
            continue

        # Enhanced category detection
        if is_strict_category_header(full_line):
            normalized = normalize_category(full_line)
            if normalized and normalized in ALLOWED_CATEGORIES:
                current_category = normalized
                current_variants = None
                logging.debug(f'Category changed to: {current_category}')
                continue

        # Enhanced variant detection
        if is_variant_header(full_line) or 'VEG NON-VEG' in full_line.upper():
            if 'VEG NON-VEG' in full_line.upper() or ('VEG' in full_line.upper() and 'NON' in full_line.upper()):
                current_variants = ['Veg', 'Non-Veg']
                logging.debug(f'Variants changed to: {current_variants}')
                continue
            else:
                detected = extract_variants_from_header(full_line)
                if detected:
                    current_variants = detected
                    logging.debug(f'Variants detected: {current_variants}')
                continue

        # Auto-assignment logic
        if current_category == "Menu Items" and re.search(r'\d{2,3}/\d{2,3}', full_line):
            current_category = "Uttar Mini Meals"
            logging.debug(f'Auto-assigned category to: {current_category}')

        # Price detection
        has_menu_price = bool(re.search(r'(?<!\d:)\b(\d{2,5}(?:\s*[/-]\s*\d{2,5})*)', full_line))
        
        if has_menu_price:
            if re.search(r'choose.*?rice|AM.*?PM', full_line, re.IGNORECASE):
                logging.debug(f'Skipping line due to unwanted pattern: {full_line}')
                continue
                
            if current_category in ALLOWED_CATEGORIES:
                for b in row:
                    b["category"] = current_category
                    if current_variants:
                        b["variants_header"] = current_variants
                categorized_rows.append(row)
                logging.debug(f'Added row to categorized_rows: {full_line}')

    logging.debug(f'Total categorized rows: {len(categorized_rows)}')
    return categorized_rows



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

# def parse_rows_to_menu(categorized_rows, image_name="unknown"):
#     menu = []

#     for row_idx, row in enumerate(categorized_rows):
#         row.sort(key=lambda b: b["x"])
#         full_line = " ".join(b["text"] for b in row).strip()
        
#         variants = row[0].get("variants_header", None) if row else None
#         current_category = row[0].get("category", "Uncategorized") if row else "Uncategorized"
        
#         # Enhanced noise filtering
#         if re.search(r'They have Chinese|BREAD$|choose.*?rice|AM.*?PM|M\.?R\.?P|Mineral Water|Small.*Large', full_line, re.IGNORECASE):
#             continue

#         if current_category not in ALLOWED_CATEGORIES:
#             continue

#         # Enhanced price pattern for multi-column
#         price_pattern = r'(?<!\d:)\b(\d{2,5}(?:\s*[/-]\s*\d{2,5})*)'
#         price_matches = list(re.finditer(price_pattern, full_line))

#         if price_matches:
#             price_start = price_matches[0].start()
#             item_chunk = full_line[:price_start].strip(" -–—|,Rs.")
#             cleaned_item = clean_text_content(item_chunk)
            
#             if cleaned_item and is_valid_item(cleaned_item):
#                 parsed_items = parse_multi_column_prices(cleaned_item, full_line[price_start:], variants)
                
#                 for entry in parsed_items:
#                     menu.append({
#                         "image": image_name,
#                         "category": current_category,
#                         "item": entry["item"],
#                         "price": entry["price"],
#                         "description": ""
#                     })

#     return menu

def parse_rows_to_menu(categorized_rows, image_name="unknown"):
    menu = []
    logging.debug(f'Parsing {len(categorized_rows)} categorized rows into menu items')

    for row_idx, row in enumerate(categorized_rows):
        row.sort(key=lambda b: b["x"])
        full_line = " ".join(b["text"] for b in row).strip()
        
        variants = row[0].get("variants_header", None) if row else None
        current_category = row[0].get("category", "Uncategorized") if row else "Uncategorized"
        
        # Enhanced noise filtering
        if re.search(r'They have Chinese|BREAD$|choose.*?rice|AM.*?PM|M\.?R\.?P|Mineral Water|Small.*Large', full_line, re.IGNORECASE):
            logging.debug(f'Skipping noisy line: {full_line}')
            continue

        if current_category not in ALLOWED_CATEGORIES:
            logging.debug(f'Skipping uncategorized line: {full_line}')
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
    logging.debug(f'Total menu items parsed: {len(menu)}')
    return menu


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