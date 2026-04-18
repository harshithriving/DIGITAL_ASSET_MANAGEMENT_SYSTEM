from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

project_bp = Blueprint("project", __name__)


@project_bp.route("/projects", methods=["GET"])
def get_projects():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Project ORDER BY project_id DESC")
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(projects)

@project_bp.route("/projects", methods=["POST"])
def create_project():
    data = request.json
    project_name = data.get("project_name")
    description = data.get("description")
    client_user_id = data.get("client_user_id")
    pm_user_id = data.get("project_manager_user_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Project (project_name, description, client_user_id, project_manager_user_id)
        VALUES (%s, %s, %s, %s)
    """, (project_name, description, client_user_id, pm_user_id))
    conn.commit()
    project_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Project created successfully", "project_id": project_id})

@project_bp.route("/project/files/<int:project_id>", methods=["GET"])
def get_project_files(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            f.file_id, 
            f.file_name,
            f.total_versions,
            EXISTS(
                SELECT 1 FROM File_Version fv
                WHERE fv.file_id = f.file_id AND fv.status = 'Approved'
            ) AS has_approved
        FROM File f
        JOIN Folder fo ON f.folder_id = fo.folder_id
        WHERE fo.project_id = %s
    """, (project_id,))
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(files)


@project_bp.route("/project/full/<int:project_id>", methods=["GET"])
def get_project_full(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT folder_id, folder_name, parent_folder_id
        FROM Folder
        WHERE project_id = %s
    """, (project_id,))
    folders = cursor.fetchall()
    cursor.execute("""
        SELECT DISTINCT f.file_id, f.file_name, f.folder_id
        FROM File f
        JOIN Folder fo ON f.folder_id = fo.folder_id
        WHERE fo.project_id = %s
    """, (project_id,))
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"folders": folders, "files": files})

@project_bp.route("/file/versions/<int:file_id>", methods=["GET"])
def get_file_versions(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT version_id, version_number, status, uploaded_at, uploaded_by
        FROM File_Version
        WHERE file_id = %s
        ORDER BY version_number DESC
    """, (file_id,))
    versions = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(versions)

@project_bp.route("/file/comments/<int:file_id>", methods=["GET"])
def get_comments(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT comment_text, user_id, created_at
        FROM Comment
        WHERE file_id = %s
        ORDER BY created_at DESC
    """, (file_id,))
    comments = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(comments)

@project_bp.route("/file/raw/<int:file_id>", methods=["GET"])
def get_raw_file_url(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT imagekit_url
        FROM File_Version
        WHERE file_id = %s AND status = 'Raw'
        ORDER BY version_number DESC
        LIMIT 1
    """, (file_id,))
    version = cursor.fetchone()
    cursor.close()
    conn.close()
    if version and version['imagekit_url']:
        return jsonify({"download_url": version['imagekit_url']})
    return jsonify({"error": "No raw version found"}), 404


