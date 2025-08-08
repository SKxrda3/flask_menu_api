import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

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
                item['image'], item['category'], item['item'],
                item['price'], item['description'], item['vendor_id']
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
