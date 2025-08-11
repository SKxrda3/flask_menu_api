



# from flask import Flask, request, jsonify
# from flask_jwt_extended import JWTManager, jwt_required
# from werkzeug.utils import secure_filename
# import os
# import time
# import logging



# from config import *
# from database import save_menu_to_database
# from auth import login_user
# from ocr_processor import process_menu_image
# from utils import create_unique_filename       

# app = Flask(__name__)
# app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# jwt = JWTManager(app)
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Configure logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# @app.route('/login', methods=['POST'])
# def login():
#     return login_user()

# @app.route('/upload-menu', methods=['POST'])
# @jwt_required()
# def upload_menu():
#     try:
#         app.logger.debug('Received request to /upload-menu')
        
#         if 'image' not in request.files:
#             app.logger.error('Image file is missing.')
#             return jsonify({'error': 'Image file is missing.'}), 400
#         if 'vendor_id' not in request.form:
#             app.logger.error('vendor_id is missing.')
#             return jsonify({'error': 'vendor_id is missing.'}), 400

#         file = request.files['image']
#         vendor_id = request.form['vendor_id']

#         app.logger.debug(f'Received vendor_id: {vendor_id}')
#         app.logger.debug(f'File received: {file.filename}')

#         if not file.filename:
#             app.logger.error('Empty filename.')
#             return jsonify({'error': 'Empty filename.'}), 400

#         # Create unique filename and save file
#         filename = create_unique_filename(file.filename, vendor_id)
#         image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(image_path)
#         app.logger.debug(f'File saved at: {image_path}')

#         # Process menu image
#         menu_data = process_menu_image(image_path, filename)
#         app.logger.debug(f'Menu data processed: {menu_data}')

#         # Add vendor_id to each item
#         for entry in menu_data:
#             entry["vendor_id"] = vendor_id

#         # Save to database
#         if menu_data:
#             db_success, db_message = save_menu_to_database(menu_data)
#             app.logger.debug(f'Database save success: {db_success}, message: {db_message}')
#             return jsonify({
#                 "message": "Menu extracted successfully",
#                 "data": menu_data,
#                 "records": len(menu_data),
#                 "database_saved": db_success,
#                 "database_message": db_message
#             }), 200
#         else:
#             app.logger.warning('No valid menu items detected')
#             return jsonify({
#                 "message": "No valid menu items detected",
#                 "data": [],
#                 "records": 0,
#                 "database_saved": False,
#                 "database_message": "No data to save"
#             }), 200

#     except Exception as e:
#         app.logger.exception(f'Exception occurred in /upload-menu: {e}')
#         return jsonify({'error': 'Internal server error occurred.'}), 500

# if __name__ == "__main__":
#     app.run(debug=True, host='0.0.0.0', port=5000)




# ========= TOP: Critical env vars (Paddle stable init) =========
import os
os.environ['PADDLE_DISABLE_SIGNAL'] = '1'  # Paddle ka signal handling disable
os.environ['PADDLE_WITH_GLOO'] = '0'       # Distributed components band

# ========= Imports =========
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
import logging
import time

# Aapke local modules
from config import *
from database import save_menu_to_database
from auth import login_user
from ocr_processor import process_menu_image
from utils import create_unique_filename

# ========= Flask app setup =========
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

jwt = JWTManager(app)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ========= Logging =========
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# ========= Optional: Model preloading (startup pe) =========
# Yahan pe models ko warm-up/load kara do taaki first request slow na ho.
# Agar ocr_processor ke andar hi lazy-load ho raha hai to isme sirf ek light warm-up call bhi kar sakte ho.
@app.before_first_request
def load_models():
    try:
        app.logger.info("Preloading OCR models...")
        # Lightweight warmup: chhota dummy image path ya None ke saath safe call
        # Agar process_menu_image None handle nahi karta, to ocr_processor me ek init function banao aur yahan call karo.
        # Example:
        # from ocr_processor import init_ocr_models
        # init_ocr_models()
        pass
    except Exception as e:
        app.logger.exception(f"Model preload failed: {e}")

# ========= Routes =========
@app.route('/login', methods=['POST'])
def login():
    return login_user()

@app.route('/upload-menu', methods=['POST'])
@jwt_required()
def upload_menu():
    try:
        app.logger.debug('Received request to /upload-menu')

        if 'image' not in request.files:
            app.logger.error('Image file is missing.')
            return jsonify({'error': 'Image file is missing.'}), 400
        if 'vendor_id' not in request.form:
            app.logger.error('vendor_id is missing.')
            return jsonify({'error': 'vendor_id is missing.'}), 400

        file = request.files['image']
        vendor_id = request.form['vendor_id']

        app.logger.debug(f'Received vendor_id: {vendor_id}')
        app.logger.debug(f'File received: {file.filename}')

        if not file.filename:
            app.logger.error('Empty filename.')
            return jsonify({'error': 'Empty filename.'}), 400

        # Unique filename aur save
        filename = create_unique_filename(file.filename, vendor_id)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)
        app.logger.debug(f'File saved at: {image_path}')

        # Process menu image
        start = time.time()
        menu_data = process_menu_image(image_path, filename)
        app.logger.debug(f'Menu data processed: {menu_data} (took {time.time() - start:.2f}s)')

        # vendor_id attach
        for entry in menu_data:
            entry["vendor_id"] = vendor_id

        # DB save
        if menu_data:
            db_success, db_message = save_menu_to_database(menu_data)
            app.logger.debug(f'Database save success: {db_success}, message: {db_message}')
            return jsonify({
                "message": "Menu extracted successfully",
                "data": menu_data,
                "records": len(menu_data),
                "database_saved": db_success,
                "database_message": db_message
            }), 200
        else:
            app.logger.warning('No valid menu items detected')
            return jsonify({
                "message": "No valid menu items detected",
                "data": [],
                "records": 0,
                "database_saved": False,
                "database_message": "No data to save"
            }), 200

    except Exception as e:
        app.logger.exception(f'Exception occurred in /upload-menu: {e}')
        return jsonify({'error': 'Internal server error occurred.'}), 500

# ========= Local debug run =========
if __name__ == "__main__":
    # Local testing ke liye; Render pe gunicorn use hoga
    app.run(debug=True, host='0.0.0.0', port=5000)






