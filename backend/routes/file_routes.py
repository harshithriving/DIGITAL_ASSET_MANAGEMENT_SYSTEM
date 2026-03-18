from flask import Blueprint, jsonify
from db.connection import get_db_connection

file_bp = Blueprint("files", __name__)

@file_bp.route("/files/<int:project_id>")
def get_files(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT f.file_id, f.file_name, f.file_type
        FROM File f
        JOIN Folder fo ON f.folder_id = fo.folder_id
        WHERE fo.project_id = %s
    """
    cursor.execute(query, (project_id,))
    files = cursor.fetchall()
    conn.close()

    return jsonify(files)