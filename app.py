# from flask import Flask, request, jsonify
# from flask_jwt_extended import JWTManager, jwt_required
# from werkzeug.utils import secure_filename
# import os
# import time

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

# @app.route('/login', methods=['POST'])
# def login():
#     return login_user()

# @app.route('/upload-menu', methods=['POST'])
# @jwt_required()
# def upload_menu():
#     if 'image' not in request.files:
#         return jsonify({'error': 'Image file is missing.'}), 400
#     if 'vendor_id' not in request.form:
#         return jsonify({'error': 'vendor_id is missing.'}), 400

#     file = request.files['image']
#     vendor_id = request.form['vendor_id']

#     if file.filename == '':
#         return jsonify({'error': 'Empty filename.'}), 400

#     # Create unique filename
#     filename = create_unique_filename(file.filename, vendor_id)
#     image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     file.save(image_path)

#     # Process menu image
#     menu_data = process_menu_image(image_path, filename)

#     # Add vendor_id to each item
#     for entry in menu_data:
#         entry["vendor_id"] = vendor_id

#     # Save to database
#     if menu_data:
#         db_success, db_message = save_menu_to_database(menu_data)
#         return jsonify({
#             "message": "Menu extracted successfully",
#             "data": menu_data,
#             "records": len(menu_data),
#             "database_saved": db_success,
#             "database_message": db_message
#         }), 200
#     else:
#         return jsonify({
#             "message": "No valid menu items detected",
#             "data": [],
#             "records": 0,
#             "database_saved": False,
#             "database_message": "No data to save"
#         }), 200

# if __name__ == "__main__":
#     app.run(debug=True, host='0.0.0.0', port=5000)




import logging
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from werkzeug.utils import secure_filename
import os
import time

from config import *
from database import save_menu_to_database
from auth import login_user
from ocr_processor import process_menu_image
from utils import create_unique_filename       

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

jwt = JWTManager(app)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

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

        # Create unique filename and save file
        filename = create_unique_filename(file.filename, vendor_id)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)
        app.logger.debug(f'File saved at: {image_path}')

        # Process menu image
        menu_data = process_menu_image(image_path, filename)
        app.logger.debug(f'Menu data processed: {menu_data}')

        # Add vendor_id to each item
        for entry in menu_data:
            entry["vendor_id"] = vendor_id

        # Save to database
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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)









