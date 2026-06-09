from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

project_bp = Blueprint("project", __name__)

# GET all projects (with client and manager names)
@project_bp.route("/projects", methods=["GET"])
def get_projects():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            p.*,
            u.name as project_manager_name,
            cl.name as client_name
        FROM Project p
        LEFT JOIN User u ON p.project_manager_user_id = u.user_id
        LEFT JOIN User cl ON p.client_user_id = cl.user_id
        ORDER BY p.project_id DESC
    """)
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(projects)

# POST create new project
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

# Get files in a project (with flags)
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
            ) AS has_approved,
            EXISTS(
                SELECT 1 FROM File_Version fv
                WHERE fv.file_id = f.file_id AND fv.status = 'In-Process'
            ) AS has_in_process,
            CASE 
                WHEN NOT EXISTS(SELECT 1 FROM File_Version fv WHERE fv.file_id = f.file_id AND fv.status IN ('Approved', 'In-Process'))
                THEN 1 ELSE 0 
            END AS is_raw
        FROM File f
        JOIN Folder fo ON f.folder_id = fo.folder_id
        WHERE fo.project_id = %s
    """, (project_id,))
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(files)

# Get full folder/file structure for a project
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

# Get all versions of a file
@project_bp.route("/file/versions/<int:file_id>", methods=["GET"])
def get_file_versions(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT version_id, version_number, status, uploaded_at, uploaded_by, file_size
        FROM File_Version
        WHERE file_id = %s
        ORDER BY version_number DESC
    """, (file_id,))
    versions = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(versions)

# Get comments for a file
# ... other imports and routes ...

@project_bp.route("/file/comments/<int:file_id>", methods=["GET"])
def get_comments(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.comment_text, u.name, c.created_at
        FROM Comment c
        JOIN User u ON c.user_id = u.user_id
        WHERE c.file_id = %s
        ORDER BY c.created_at DESC
    """, (file_id,))
    comments = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(comments)

# ... rest of the file ...

# Get raw file URL (ImageKit)
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

# Get projects with latest file status (for admin dashboard)
@project_bp.route("/projects-with-status", methods=["GET"])
def get_projects_with_status():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            p.project_id,
            p.project_name,
            p.project_manager_user_id,
            p.created_at,
            COALESCE(
                (SELECT fv.status 
                 FROM File_Version fv
                 JOIN File f ON fv.file_id = f.file_id
                 JOIN Folder fol ON f.folder_id = fol.folder_id
                 WHERE fol.project_id = p.project_id
                 ORDER BY fv.uploaded_at DESC 
                 LIMIT 1),
                'No Files'
            ) as latest_status
        FROM Project p
        ORDER BY p.created_at DESC
    """)
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(projects)

# Get download URL for approved version
@project_bp.route("/file/download/<int:file_id>", methods=["GET"])
def get_download_url(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT imagekit_url
        FROM File_Version
        WHERE file_id = %s AND status = 'Approved'
        ORDER BY version_number DESC
        LIMIT 1
    """, (file_id,))
    version = cursor.fetchone()
    cursor.close()
    conn.close()
    if version and version['imagekit_url']:
        return jsonify({"download_url": version['imagekit_url']})
    return jsonify({"error": "No approved version found"}), 404

@project_bp.route("/file/inprocess/<int:file_id>", methods=["GET"])
def get_inprocess_file_url(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT imagekit_url
        FROM File_Version
        WHERE file_id = %s AND status = 'In-Process'
        ORDER BY version_number DESC
        LIMIT 1
    """, (file_id,))
    version = cursor.fetchone()
    cursor.close()
    conn.close()
    if version and version['imagekit_url']:
        return jsonify({"download_url": version['imagekit_url']})
    return jsonify({"error": "No in-process version found"}), 404