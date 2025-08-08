import time
from werkzeug.utils import secure_filename
import os

def create_unique_filename(original_filename, vendor_id):
    """Create unique filename with timestamp"""
    timestamp = int(time.time())
    filename = secure_filename(original_filename)
    name, ext = os.path.splitext(filename)
    return f"{name}_{vendor_id}_{timestamp}{ext}"
