from paddleocr import PaddleOCR
from PIL import Image
import os
import logging
from menu_parser import assign_categories, group_by_rows, parse_rows_to_menu

# def get_fresh_ocr():
#     """Get a fresh OCR instance to avoid state issues"""
#     return PaddleOCR(use_angle_cls=True, lang='en')


# def get_fresh_ocr():
#     return PaddleOCR(
#         use_angle_cls=False,
#         lang='en',
#         det_model_dir='./models/PP-OCRv5_server_det/',
#         rec_model_dir='./models/PP-OCRv5_server_rec/',
#         cls_model_dir='./models/PP-LCNet_x1_0_textline_ori/'  
#     )

# def get_fresh_ocr():
#     return PaddleOCR(
#         use_angle_cls=False,
#         lang='en',
#         det_model_dir='./models/PP-OCRv3_det/',
#         rec_model_dir='./models/PP-OCRv3_rec/',
#         cls_model_dir='./models/PP-LCNet_x1_0_textline_ori/'  
#     )


def get_fresh_ocr():
    return PaddleOCR(
        use_angle_cls=False,
        lang='en',
        
       
    )
# det_model_dir='models/PP-OCRv5_mobile_det/',
# rec_model_dir='models/PP-OCRv5_mobile_rec/',



def preprocess_image(image_path):
    """Process image without modifying the original file"""
    base, ext = os.path.splitext(image_path)
    processed_path = base + '_processed' + ext
    
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            img.save(processed_path)
    except Exception:
        return image_path
    return processed_path

# def extract_boxes(image_path, conf_threshold=0.6):
#     try:
#         ocr = get_fresh_ocr()
#         results = ocr.predict(image_path)
        
#         if not results:
#             return []
        
#         boxes = []
        
#         if isinstance(results[0], dict):
#             dt_polys = results[0]['dt_polys']
#             rec_texts = results[0]['rec_texts']
#             rec_scores = results[0]['rec_scores']
            
#             for box_points, text, conf in zip(dt_polys, rec_texts, rec_scores):
#                 if conf >= conf_threshold and text and isinstance(text, str):
#                     if hasattr(box_points, 'tolist'):
#                         box_points = box_points.tolist()
#                     x_center = sum([p[0] for p in box_points]) / len(box_points)
#                     y_center = sum([p[1] for p in box_points]) / len(box_points)
#                     boxes.append({
#                         'text': text.strip(),
#                         'conf': conf,
#                         'box': box_points,
#                         'x': x_center,
#                         'y': y_center
#                     })
        
#         elif isinstance(results[0], list):
#             for line in results[0]:
#                 if not line or len(line) < 2:
#                     continue
#                 box_points = line[0]
#                 text = line[1][0]
#                 conf = line[1][1]
                
#                 if conf >= conf_threshold and text and isinstance(text, str):
#                     x_center = sum([p[0] for p in box_points]) / len(box_points)
#                     y_center = sum([p[1] for p in box_points]) / len(box_points)
#                     boxes.append({
#                         'text': text.strip(),
#                         'conf': conf,
#                         'box': box_points,
#                         'x': x_center,
#                         'y': y_center
#                     })
        
#         return boxes
    
#     except Exception as e:
#         return []

def extract_boxes(image_path, conf_threshold=0.6):
    try:
        ocr = get_fresh_ocr()
        logging.debug(f'Running OCR on {image_path}')
        results = ocr.predict(image_path)
        
        if not results:
            logging.debug('No OCR results found')
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
        logging.debug(f'Boxes extracted: {len(boxes)}')
        return boxes
    
    except Exception as e:
        logging.error(f'Exception in extract_boxes: {e}', exc_info=True)
        return []
    


# def process_menu_image(image_path, filename):
#     """Main function to process menu image and return extracted data"""
#     processed_image_path = preprocess_image(image_path)
#     boxes = extract_boxes(processed_image_path)
#     rows = group_by_rows(boxes)
#     categorized_rows = assign_categories(rows)
#     menu_data = parse_rows_to_menu(categorized_rows, image_name=filename)
#     return menu_data


def process_menu_image(image_path, filename):

    logging.debug(f'Starting process_menu_image for {filename}')
    processed_image_path = preprocess_image(image_path)
    logging.debug(f'Image preprocessed: {processed_image_path}')
    boxes = extract_boxes(processed_image_path)
    logging.debug(f'Extracted {len(boxes)} boxes')
    rows = group_by_rows(boxes)
    logging.debug(f'Grouped into {len(rows)} rows')
    categorized_rows = assign_categories(rows)
    logging.debug(f'{len(categorized_rows)} rows categorized')
    menu_data = parse_rows_to_menu(categorized_rows, image_name=filename)
    logging.debug(f'Parsed {len(menu_data)} menu items')
    return menu_data


# import easyocr
# from PIL import Image
# import os
# import logging
# from menu_parser import assign_categories, group_by_rows, parse_rows_to_menu

# # EasyOCR reader globally initialize karen, CPU mode
# reader = easyocr.Reader(['en'], gpu=False)

# def preprocess_image(image_path):
#     """Image ko resize karke processed file banaye bina original file modify kiye."""
#     base, ext = os.path.splitext(image_path)
#     processed_path = base + '_processed' + ext
    
#     try:
#         with Image.open(image_path) as img:
#             img = img.convert('RGB')
#             img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
#             img.save(processed_path)
#     except Exception:
#         return image_path
#     return processed_path

# def extract_boxes(image_path, conf_threshold=0.6):
#     try:
#         logging.debug(f'Running EasyOCR on {image_path}')
#         results = reader.readtext(image_path)

#         if not results:
#             logging.debug('No OCR results found')
#             return []

#         boxes = []
#         for (bbox, text, conf) in results:
#             if conf >= conf_threshold and text and isinstance(text, str):
#                 x_center = sum([point[0] for point in bbox]) / len(bbox)
#                 y_center = sum([point[1] for point in bbox]) / len(bbox)
#                 boxes.append({
#                     'text': text.strip(),
#                     'conf': conf,
#                     'box': bbox,
#                     'x': x_center,
#                     'y': y_center
#                 })

#         logging.debug(f'Boxes extracted: {len(boxes)}')
#         return boxes
    
#     except Exception as e:
#         logging.error(f'Exception in extract_boxes: {e}', exc_info=True)
#         return []

# def process_menu_image(image_path, filename):
#     logging.debug(f'Starting process_menu_image for {filename}')
#     processed_image_path = preprocess_image(image_path)
#     logging.debug(f'Image preprocessed: {processed_image_path}')
#     boxes = extract_boxes(processed_image_path)
#     logging.debug(f'Extracted {len(boxes)} boxes')
#     rows = group_by_rows(boxes)
#     logging.debug(f'Grouped into {len(rows)} rows')
#     categorized_rows = assign_categories(rows)
#     logging.debug(f'{len(categorized_rows)} rows categorized')
#     menu_data = parse_rows_to_menu(categorized_rows, image_name=filename)
#     logging.debug(f'Parsed {len(menu_data)} menu items')
#     return menu_data
