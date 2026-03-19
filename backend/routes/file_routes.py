from flask import Blueprint, request, jsonify
from db.connection import get_db_connection
from werkzeug.utils import secure_filename
import os

file_bp = Blueprint("file", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def update_storage_used(user_id, file_size):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE User SET storage_used = storage_used + %s WHERE user_id = %s", (file_size, user_id))
    conn.commit()
    cursor.close()
    conn.close()

@file_bp.route("/file/create", methods=["POST"])
def create_file():
    data = request.json
    file_name = data.get("file_name")
    folder_id = data.get("folder_id")
    user_id = data.get("user_id")
    file_size = data.get("file_size", 0)  # in bytes, default 0

    if not file_name or not folder_id or not user_id:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert into File
        cursor.execute("""
            INSERT INTO File (file_name, file_type, folder_id)
            VALUES (%s, %s, %s)
        """, (file_name, file_name.split('.')[-1] if '.' in file_name else 'unknown', folder_id))
        file_id = cursor.lastrowid

        # Insert first version with given size
        cursor.execute("""
            INSERT INTO File_Version (file_id, version_number, uploaded_by, status, file_path, file_size)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, 1, user_id, 'Raw', None, file_size))

        # Update user storage
        cursor.execute("UPDATE User SET storage_used = storage_used + %s WHERE user_id = %s", (file_size, user_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "File created", "file_id": file_id}), 201

@file_bp.route("/upload/file", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    folder_id = request.form.get("folder_id")
    uploaded_by = request.form.get("uploaded_by")
    if not file or not folder_id or not uploaded_by:
        return jsonify({"error": "Missing fields"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO File (file_name, file_type, folder_id)
            VALUES (%s, %s, %s)
        """, (filename, filename.split('.')[-1] if '.' in filename else 'unknown', folder_id))
        file_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO File_Version (file_id, version_number, uploaded_by, status, file_path, file_size)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, 1, uploaded_by, 'Raw', filepath, file_size))

        update_storage_used(uploaded_by, file_size)

        conn.commit()
    except Exception as e:
        conn.rollback()
        os.remove(filepath)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "File uploaded", "file_id": file_id}), 201

@file_bp.route("/upload/version", methods=["POST"])
def upload_version():
    file = request.files.get("file")
    file_id = request.form.get("file_id")
    uploaded_by = request.form.get("uploaded_by")
    if not file or not file_id or not uploaded_by:
        return jsonify({"error": "Missing fields"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT MAX(version_number) as max_version FROM File_Version WHERE file_id = %s", (file_id,))
        result = cursor.fetchone()
        next_version = (result['max_version'] or 0) + 1

        cursor.execute("""
            INSERT INTO File_Version (file_id, version_number, uploaded_by, status, file_path, file_size)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, next_version, uploaded_by, 'In-Process', filepath, file_size))

        update_storage_used(uploaded_by, file_size)

        conn.commit()
    except Exception as e:
        conn.rollback()
        os.remove(filepath)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "New version uploaded", "version_id": cursor.lastrowid}), 201

@file_bp.route("/file/review/<int:project_id>", methods=["GET"])
def files_for_review(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fv.version_id, f.file_id, f.file_name, fv.version_number
        FROM File_Version fv
        JOIN File f ON fv.file_id = f.file_id
        JOIN Folder fol ON f.folder_id = fol.folder_id
        WHERE fv.status = 'In-Process' AND fol.project_id = %s
    """, (project_id,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

@file_bp.route("/file/approve/<int:version_id>", methods=["PUT"])
def approve(version_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE File_Version SET status = 'Approved' WHERE version_id = %s", (version_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Approved"})

@file_bp.route("/file/reject/<int:version_id>", methods=["PUT"])
def reject(version_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE File_Version SET status = 'Rejected' WHERE version_id = %s", (version_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Rejected"})

@file_bp.route("/file/comments/<int:file_id>", methods=["GET"])
def get_comments(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT comment_text, user_id, created_at
        FROM Comment
        WHERE file_id = %s
        ORDER BY created_at DESC
    """, (file_id,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

@file_bp.route("/file/versions/<int:file_id>", methods=["GET"])
def get_versions(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT version_id, version_number, status, uploaded_at, uploaded_by
        FROM File_Version
        WHERE file_id = %s
        ORDER BY version_number DESC
    """, (file_id,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

@file_bp.route("/file/approved/<int:project_id>", methods=["GET"])
def approved_files(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fv.version_id, f.file_id, f.file_name, fv.version_number
        FROM File_Version fv
        JOIN File f ON fv.file_id = f.file_id
        JOIN Folder fol ON f.folder_id = fol.folder_id
        WHERE fv.status = 'Approved' AND fol.project_id = %s
    """, (project_id,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)




@file_bp.route("/simulate/upload/version", methods=["POST"])
def simulate_upload_version():
    data = request.json
    file_id = data.get("file_id")
    uploaded_by = data.get("uploaded_by")
    file_name = data.get("file_name")
    file_size = data.get("file_size", 0)

    if not file_id or not uploaded_by:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get latest version
        cursor.execute("SELECT MAX(version_number) as max_version FROM File_Version WHERE file_id = %s", (file_id,))
        result = cursor.fetchone()
        next_version = (result['max_version'] or 0) + 1

        # Insert new version – trigger will update storage_used
        cursor.execute("""
            INSERT INTO File_Version (file_id, version_number, uploaded_by, status, file_path, file_size)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, next_version, uploaded_by, 'In-Process', None, file_size))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Simulated version uploaded", "version_id": cursor.lastrowid}), 201

