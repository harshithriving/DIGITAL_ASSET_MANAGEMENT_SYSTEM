from flask import Blueprint, request, jsonify
from db.connection import get_db_connection
from werkzeug.utils import secure_filename
import os

file_bp = Blueprint("file", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def check_permission(cursor, user_id, folder_id):
    cursor.execute("""
        SELECT 1
        FROM Permission
        WHERE user_id = %s AND folder_id = %s
    """, (user_id, folder_id))
    
    return cursor.fetchone() is not None

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
    cursor = conn.cursor(dictionary = True)

    try:
        cursor.execute("""
            SELECT storage_used, storage_limit
            FROM User
            WHERE user_id = %s
        """, (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error" : "User not found"}), 404
        
        # PERMISSION CHECK
        if not check_permission(cursor, user_id, folder_id):
            return jsonify({"error": "Permission denied"}), 403
        
        # DUPLICATE FILE CHECK
        cursor.execute("""
            SELECT 1 FROM File
            WHERE file_name = %s AND folder_id = %s
        """, (file_name, folder_id))

        if cursor.fetchone():
            return jsonify({"error": "File with same name already exists in this folder"}), 400
                
        if user['storage_used'] + file_size > user['storage_limit']:
            return jsonify({"error" : "Storage limit exceeded"}), 400
    
        cursor.execute("""
            INSERT INTO File (file_name, file_type, folder_id)
            VALUES (%s, %s, %s)
        """, (file_name, file_name.split('.')[-1] if '.' in file_name else 'unknown', folder_id))
        file_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO File_Version (file_id, version_number, uploaded_by, status, file_path, file_size)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, 1, user_id, 'Raw', None, file_size))

        cursor.execute("""
            UPDATE User
            SET storage_used = storage_used + %s
            WHERE user_id = %s
        """, (file_size, user_id))

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

        cursor.execute("""
            SELECT storage_used, storage_limit
            FROM User
            WHERE user_id = %s
        """, (uploaded_by,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # GET FOLDER ID FROM FILE
        cursor.execute("""
            SELECT folder_id FROM File WHERE file_id = %s
        """, (file_id,))
        file_data = cursor.fetchone()

        if not file_data:
            return jsonify({"error": "File not found"}), 404

        folder_id = file_data['folder_id']

        # PERMISSION CHECK
        if not check_permission(cursor, uploaded_by, folder_id):
            return jsonify({"error": "Permission denied"}), 403

        if user['storage_used'] + file_size > user['storage_limit']:
            return jsonify({"error": "Storage limit exceeded"}), 400

        cursor.execute("SELECT MAX(version_number) as max_version FROM File_Version WHERE file_id = %s" , (file_id,))
        result = cursor.fetchone()
        next_version = (result['max_version'] or 0) + 1

        cursor.execute("""
            INSERT INTO File_Version (file_id, version_number, uploaded_by, status, file_path, file_size)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, next_version, uploaded_by, 'In-Process', None, file_size))

        cursor.execute("""
            UPDATE User
            SET storage_used = storage_used + %s
            WHERE user_id = %s
        """, (file_size, uploaded_by))

        version_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO File_Status_Log (file_id, version_id, old_status, new_status, changed_by)
            VALUES (%s, %s, NULL, 'In-Process', %s)
        """, (file_id, version_id, uploaded_by))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Simulated version uploaded", "version_id": version_id}), 201

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
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # GET FILE → FOLDER
        cursor.execute("""
            SELECT f.folder_id
            FROM File_Version fv
            JOIN File f ON fv.file_id = f.file_id
            WHERE fv.version_id = %s
        """, (version_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Version not found"}), 404

        folder_id = result['folder_id']

        # PERMISSION CHECK
        if not check_permission(cursor, user_id, folder_id):
            return jsonify({"error": "Permission denied"}), 403

        # STEP 1: Unapprove other versions
        cursor.execute("""
            UPDATE File_Version
            SET status = 'Rejected'
            WHERE file_id = (
                SELECT file_id FROM File_Version WHERE version_id = %s
            )
        """, (version_id,))

        # STEP 2: Approve selected version
        cursor.execute("""
            UPDATE File_Version
            SET status = 'Approved'
            WHERE version_id = %s
        """, (version_id,))

        cursor.execute("""
            INSERT INTO File_Status_Log (file_id, version_id, old_status, new_status, changed_by)
            VALUES (
                (SELECT file_id FROM File_Version WHERE version_id = %s),
                %s,
                'In-Process',
                'Approved',
                %s
            )
        """, (version_id, version_id, user_id))

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Approved"})


@file_bp.route("/file/reject/<int:version_id>", methods=["PUT"])
def reject(version_id):
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # GET FILE → FOLDER
    cursor.execute("""
        SELECT f.folder_id
        FROM File_Version fv
        JOIN File f ON fv.file_id = f.file_id
        WHERE fv.version_id = %s
    """, (version_id,))
    
    result = cursor.fetchone()
    if not result:
        return jsonify({"error": "Version not found"}), 404

    folder_id = result['folder_id']

    # PERMISSION CHECK
    if not check_permission(cursor, user_id, folder_id):
        return jsonify({"error": "Permission denied"}), 403
    cursor.execute("UPDATE File_Version SET status = 'Rejected' WHERE version_id = %s", (version_id,))

    cursor.execute("""
        INSERT INTO File_Status_Log (file_id, version_id, old_status, new_status, changed_by)
        VALUES (
            (SELECT file_id FROM File_Version WHERE version_id = %s),
            %s,
            'In-Process',
            'Rejected',
            %s
        )
    """, (version_id, version_id, user_id))

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

@file_bp.route("/file/delete/<int:file_id>", methods=["DELETE"])
def delete_file(file_id):
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # CHECK FILE EXISTS
        cursor.execute("""
            SELECT f.file_id, fv.uploaded_by, fv.file_size
            FROM File f
            JOIN File_Version fv ON f.file_id = fv.file_id
            WHERE f.file_id = %s
        """, (file_id,))
        versions = cursor.fetchall()

        if not versions:
            return jsonify({"error": "File not found"}), 404
        
        # GET FOLDER ID
        cursor.execute("""
            SELECT folder_id FROM File WHERE file_id = %s
        """, (file_id,))
        file_data = cursor.fetchone()

        if not file_data:
            return jsonify({"error": "File not found"}), 404

        folder_id = file_data['folder_id']

        # PERMISSION CHECK
        if not check_permission(cursor, user_id, folder_id):
            return jsonify({"error": "Permission denied"}), 403

        # CALCULATE TOTAL SIZE (to reduce storage)
        total_size = sum(v['file_size'] or 0 for v in versions)

        # DELETE COMMENTS
        cursor.execute("DELETE FROM Comment WHERE file_id = %s", (file_id,))

        # DELETE VERSIONS
        cursor.execute("DELETE FROM File_Version WHERE file_id = %s", (file_id,))

        # DELETE FILE
        cursor.execute("DELETE FROM File WHERE file_id = %s", (file_id,))

        # UPDATE STORAGE (reduce usage)
        cursor.execute("""
            UPDATE User
            SET storage_used = GREATEST(storage_used - %s, 0)
            WHERE user_id = %s
        """, (total_size, user_id))

        cursor.execute("""
            INSERT INTO File_Status_Log (file_id, version_id, old_status, new_status, changed_by)
            VALUES (%s, NULL, 'Existing', 'Deleted', %s)
        """, (file_id, user_id))

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "File deleted successfully"}), 200