"""Comment management API built with Flask and MySQL."""

from flask import Flask, request, jsonify

from flask import send_from_directory
from datetime import datetime
import mysql.connector  # Import MySQL Connector
from mysql.connector.cursor import MySQLCursor
from mysql.connector.connection import MySQLConnection
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')


@app.route('/ui')
def serve_ui():
    """Serve the frontend user interface."""
    return app.send_static_file('index.html')

# IMPORTANT: Update with your actual MySQL credentials and database name.
# The database 'comments_db' and the user should be created in MySQL beforehand.
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',       # Replace with your MySQL username
    'password': 'H1cke$$1nk', # Replace with your MySQL password
    'database': 'stocks'    # Replace with your database name
}

# --- Database Helper Functions ---

def get_db_connection() -> MySQLConnection:
    """Create and return a connection to the configured MySQL database.

    Returns:
        MySQLConnection: Active connection object that should be closed by the
        caller.

    Raises:
        mysql.connector.Error: If the connection attempt fails.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        # In a real app, you might raise a custom exception or handle this more robustly
        raise


import os
import logging
from contextlib import closing
from typing import Optional
import mysql.connector
from mysql.connector.cursor import MySQLCursor
from mysql.connector.connection import MySQLConnection


def init_db_schema() -> bool:
    """Create database tables defined in ``schema.sql``.

    The function reads SQL statements from the ``schema.sql`` file located at
    the project root and executes them sequentially. It logs progress and
    returns a boolean indicating success.

    Returns:
        bool: ``True`` when the schema is created successfully, otherwise
        ``False``.
    """
    logging.info("Starting database schema initialization...")

    conn = None
    cursor = None

    try:
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Read schema file
        schema_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..',
            'schema.sql'
        )

        # Validate schema file exists and is readable
        if not os.path.isfile(schema_path):
            logging.error("Schema file not found at: %s", schema_path)
            return False

        # Read and execute schema
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            # Split the script into individual statements
            statements = sql_script.split(';')

            # Execute each statement separately
            for statement in statements:
                statement = statement.strip()
                if statement:  # Skip empty statements
                    cursor.execute(statement)
                    if cursor.with_rows:
                        rows = cursor.fetchall()
                        logging.debug(
                            "Query '%s' returned %d rows",
                            statement[:100],  # Truncate long statements in log
                            len(rows)
                        )
                    else:
                        logging.debug(
                            "Query '%s' affected %d rows",
                            statement[:100],  # Truncate long statements in log
                            cursor.rowcount
                        )

            # Commit changes
            conn.commit()
            logging.info("Database schema initialized successfully")
            return True

        except IOError as e:
            logging.error("Failed to read schema file: %s", e)
            return False

    except mysql.connector.Error as err:
        logging.error("Database error during schema initialization: %s", err)
        if conn:
            conn.rollback()  # Rollback any partial changes
        return False

    except Exception as e:
        logging.error("Unexpected error during schema initialization: %s", e)
        if conn:
            conn.rollback()  # Rollback any partial changes
        return False

    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logging.debug("Database connection closed")

# --- API Endpoints ---

@app.route('/comments', methods=['POST'])
def create_comment():
    """Create a new comment and store it in the database.

    The request body must contain a ``text`` field. On success the newly
    created comment, including its database assigned ``id`` and ISO formatted
    ``created_at`` timestamp, is returned with status code ``201``.
    """
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
    """Return all comments ordered by creation time in descending order."""
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
    """Retrieve a single comment by its identifier."""
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

@app.route('/comments/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    """Update the text of an existing comment."""
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({"error": "Comment text is required"}), 400

    new_text = data.get('text')
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        update_query = "UPDATE comments SET text = %s WHERE id = %s"
        cursor.execute(update_query, (new_text, comment_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Comment not found"}), 404

        cursor.close()
        cursor = conn.cursor(dictionary=True)
        select_query = ("SELECT id, text, DATE_FORMAT(created_at, '%Y-%m-%dT%H:%i:%SZ') "
                        "as created_at FROM comments WHERE id = %s")
        cursor.execute(select_query, (comment_id,))
        updated = cursor.fetchone()
        return jsonify(updated), 200

    except mysql.connector.Error as err:
        print(f"Database error in update_comment: {err}")
        return jsonify({"error": "Failed to update comment due to database error"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """Remove a comment from the database if it exists."""
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
