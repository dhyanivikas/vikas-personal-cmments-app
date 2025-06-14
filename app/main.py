from flask import Flask, request, jsonify
from datetime import datetime
import mysql.connector # Import MySQL Connector
import os

app = Flask(__name__)

# IMPORTANT: Update with your actual MySQL credentials and database name.
# The database 'comments_db' and the user should be created in MySQL beforehand.
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',       # Replace with your MySQL username
    'password': 'your_password', # Replace with your MySQL password
    'database': 'comments_db'    # Replace with your database name
}

# --- Database Helper Functions ---

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        # In a real app, you might raise a custom exception or handle this more robustly
        raise

def init_db_schema():
    """Initializes the database schema by executing commands from schema.sql."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(base_dir, '..', 'schema.sql')
        with open(schema_path, 'r') as f:
            sql_script = f.read()
        
        # Split script into individual statements if necessary,
        # though mysql.connector's cursor.execute() can often handle multi-statement scripts
        # if the connection is configured for it (e.g., multi=True on cursor or using execute_stream).
        # For simplicity, assuming single statements or that the driver handles it.
        # A more robust way for multiple statements:
        for result in cursor.execute(sql_script, multi=True):
            if result.with_rows:
                print("Rows produced by statement '{}':".format(result.statement))
                print(result.fetchall())
            else:
                print("Number of rows affected by statement '{}': {}".format(
                    result.statement, result.rowcount))

        conn.commit()
        print("Database schema initialized successfully.")
    except mysql.connector.Error as err:
        print(f"Error initializing database schema: {err}")
    except FileNotFoundError:
        print("Error: schema.sql not found. Make sure it's in the root directory.")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# --- API Endpoints ---

@app.route('/comments', methods=['POST'])
def create_comment():
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({"error": "Comment text is required"}), 400

    comment_text = data.get('text')
    created_at_dt = datetime.utcnow()
    # Format for MySQL DATETIME column
    created_at_sql_format = created_at_dt.strftime('%Y-%m-%d %H:%M:%S')

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = "INSERT INTO comments (text, created_at) VALUES (%s, %s)"
        cursor.execute(insert_query, (comment_text, created_at_sql_format))
        new_comment_id = cursor.lastrowid # Get the ID of the newly inserted row
        conn.commit()
        
        new_comment = {
            "id": new_comment_id,
            "text": comment_text,
            "created_at": created_at_dt.isoformat() + 'Z' # ISO 8601 format for response
        }
        return jsonify(new_comment), 201
        
    except mysql.connector.Error as err:
        print(f"Database error in create_comment: {err}")
        return jsonify({"error": "Failed to create comment due to database error"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/comments', methods=['GET'])
def get_all_comments():
    conn = None
    try:
        conn = get_db_connection()
        # Use dictionary=True for cursor to get results as dictionaries
        cursor = conn.cursor(dictionary=True)
        
        # Format created_at to ISO 8601 like string in SQL
        query = "SELECT id, text, DATE_FORMAT(created_at, '%Y-%m-%dT%H:%i:%SZ') as created_at FROM comments ORDER BY created_at DESC"
        cursor.execute(query)
        comments = cursor.fetchall()
        
        return jsonify(comments), 200
        
    except mysql.connector.Error as err:
        print(f"Database error in get_all_comments: {err}")
        return jsonify({"error": "Failed to fetch comments due to database error"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/comments/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, text, DATE_FORMAT(created_at, '%Y-%m-%dT%H:%i:%SZ') as created_at FROM comments WHERE id = %s"
        cursor.execute(query, (comment_id,))
        comment = cursor.fetchone()
        
        if comment:
            return jsonify(comment), 200
        else:
            return jsonify({"error": "Comment not found"}), 404
            
    except mysql.connector.Error as err:
        print(f"Database error in get_comment: {err}")
        return jsonify({"error": "Failed to fetch comment due to database error"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "DELETE FROM comments WHERE id = %s"
        cursor.execute(query, (comment_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({"message": "Comment deleted successfully"}), 200
        else:
            return jsonify({"error": "Comment not found or already deleted"}), 404
            
    except mysql.connector.Error as err:
        print(f"Database error in delete_comment: {err}")
        return jsonify({"error": "Failed to delete comment due to database error"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    # Initialize the database schema when the app starts (for development)
    # In production, you'd typically run schema migrations separately.
    init_db_schema() 
    app.run(debug=True)
