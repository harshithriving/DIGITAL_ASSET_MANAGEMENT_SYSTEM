from flask import Blueprint, request, jsonify
from db.connection import get_db_connection
import os
import hashlib
import time
import requests
from dotenv import load_dotenv

load_dotenv()

file_bp = Blueprint("file", __name__)

# Ensure upload directory exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ImageKit credentials from .env
IMAGEKIT_PRIVATE_KEY = os.getenv('IMAGEKIT_PRIVATE_KEY')
IMAGEKIT_PUBLIC_KEY = os.getenv('IMAGEKIT_PUBLIC_KEY')
IMAGEKIT_URL_ENDPOINT = os.getenv('IMAGEKIT_URL_ENDPOINT')

# Validate credentials
if not IMAGEKIT_PRIVATE_KEY or not IMAGEKIT_PUBLIC_KEY or not IMAGEKIT_URL_ENDPOINT:
    raise ValueError("Missing ImageKit credentials in .env file")

# Helper to get next version number
def get_next_version(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT MAX(version_number) as max_version FROM File_Version WHERE file_id = %s", (file_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return (result['max_version'] or 0) + 1


def upload_to_imagekit_rest(file_path, file_name):
    """Upload using Basic Authentication with private key."""
    with open(file_path, "rb") as f:
        files = {'file': (file_name, f)}
        data = {
            'fileName': file_name,
            'useUniqueFileName': 'true',   # must be string 'true' or 'false'
            'folder': 'dam_system'
        }
        response = requests.post(
            'https://upload.imagekit.io/api/v1/files/upload',
            files=files,
            data=data,
            auth=(IMAGEKIT_PRIVATE_KEY, '')
        )
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"ImageKit upload failed: {response.text}")

# -------------------- EXISTING ENDPOINTS (unchanged) --------------------
@file_bp.route("/file/create", methods=["POST"])
def create_file():
    data = request.json
    file_name = data.get("file_name")
    folder_id = data.get("folder_id")
    user_id = data.get("user_id")
    file_size = data.get("file_size", 0)

    if not file_name or not folder_id or not user_id:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO File (file_name, file_type, folder_id)
            VALUES (%s, %s, %s)
        """, (file_name, file_name.split('.')[-1] if '.' in file_name else 'unknown', folder_id))
        file_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO File_Version (file_id, version_number, uploaded_by, status, file_path, file_size)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, 1, user_id, 'Raw', None, file_size))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "File created", "file_id": file_id}), 201

@file_bp.route("/simulate/upload/version", methods=["POST"])
def simulate_upload_version():
    data = request.json
    file_id = data.get("file_id")
    uploaded_by = data.get("uploaded_by")
    file_size = data.get("file_size", 0)

    if not file_id or not uploaded_by:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        next_version = get_next_version(file_id)
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

@file_bp.route("/file/version/<int:version_id>", methods=["DELETE"])
def delete_version(version_id):
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT version_id, file_id, uploaded_by, status, file_size
            FROM File_Version
            WHERE version_id = %s
        """, (version_id,))
        version = cursor.fetchone()
        if not version:
            return jsonify({"error": "Version not found"}), 404
        if version['uploaded_by'] != user_id:
            return jsonify({"error": "You can only delete your own versions"}), 403
        if version['status'] == 'Approved':
            return jsonify({"error": "Cannot delete an approved version"}), 403

        cursor.execute("DELETE FROM File_Version WHERE version_id = %s", (version_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Version deleted successfully"}), 200

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

@file_bp.route("/test-imagekit", methods=["GET"])
def test_imagekit():
    """Test ImageKit credentials without uploading a file."""
    return jsonify({
        "private_key_exists": bool(IMAGEKIT_PRIVATE_KEY),
        "public_key_exists": bool(IMAGEKIT_PUBLIC_KEY),
        "url_endpoint": IMAGEKIT_URL_ENDPOINT,
        "private_key_preview": IMAGEKIT_PRIVATE_KEY[:10] + "..." if IMAGEKIT_PRIVATE_KEY else None,
        "public_key_preview": IMAGEKIT_PUBLIC_KEY[:10] + "..." if IMAGEKIT_PUBLIC_KEY else None
    })

# -------------------- IMAGEKIT UPLOAD ENDPOINTS (using direct REST API) --------------------
@file_bp.route("/upload-to-imagekit", methods=["POST"])
def upload_to_imagekit_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    folder_id = request.form.get("folder_id")
    uploaded_by = request.form.get("uploaded_by")
    if not folder_id or not uploaded_by:
        return jsonify({"error": "Missing folder_id or uploaded_by"}), 400

    # Save file temporarily
    temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(temp_path)

    try:
        upload_data = upload_to_imagekit_rest(temp_path, file.filename)

        # Store in local database
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO File (file_name, file_type, folder_id)
                VALUES (%s, %s, %s)
            """, (file.filename, file.filename.split('.')[-1], folder_id))
            file_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO File_Version (file_id, version_number, uploaded_by, status, file_size, imagekit_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (file_id, 1, uploaded_by, 'Raw', upload_data['size'], upload_data['url']))

            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            cursor.close()
            conn.close()

        return jsonify({
            "message": "File uploaded successfully to ImageKit",
            "file_id": file_id,
            "url": upload_data['url']
        }), 201

    except Exception as e:
        return jsonify({"error": f"Upload error: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@file_bp.route("/upload-version-to-imagekit", methods=["POST"])
def upload_version_to_imagekit_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_id = request.form.get("file_id")
    uploaded_by = request.form.get("uploaded_by")
    if not file_id or not uploaded_by:
        return jsonify({"error": "Missing file_id or uploaded_by"}), 400

    temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(temp_path)

    try:
        upload_data = upload_to_imagekit_rest(temp_path, file.filename)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            next_version = get_next_version(file_id)
            cursor.execute("""
                INSERT INTO File_Version (file_id, version_number, uploaded_by, status, file_size, imagekit_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (file_id, next_version, uploaded_by, 'In-Process', upload_data['size'], upload_data['url']))

            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            cursor.close()
            conn.close()

        return jsonify({
            "message": "New version uploaded",
            "version_id": cursor.lastrowid
        }), 201

    except Exception as e:
        return jsonify({"error": f"Upload error: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)