from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

pm_bp = Blueprint("pm", __name__)

@pm_bp.route("/pm/projects/<int:user_id>", methods=["GET"])
def get_pm_projects(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Project WHERE project_manager_user_id = %s", (user_id,))
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(projects)

@pm_bp.route("/pm/project/files/<int:project_id>", methods=["GET"])
def get_project_files(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT f.*
        FROM File f
        JOIN Folder fol ON f.folder_id = fol.folder_id
        WHERE fol.project_id = %s
    """, (project_id,))
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(files)

@pm_bp.route("/pm/comment", methods=["POST"])
def add_comment():
    data = request.json
    comment_text = data.get("comment")
    file_id = data.get("file_id")
    user_id = data.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Comment (comment_text, file_id, user_id)
        VALUES (%s, %s, %s)
    """, (comment_text, file_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Comment added"})

@pm_bp.route("/pm/assign_employee", methods=["POST"])
def assign_employee():
    data = request.json
    user_id = data.get("user_id")
    project_id = data.get("project_id")
    granted_by = data.get("granted_by")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT folder_id FROM Folder WHERE project_id = %s AND is_root = 1", (project_id,))
        root = cursor.fetchone()
        if not root:
            return jsonify({"error": "Project has no root folder"}), 400
        folder_id = root['folder_id']

        cursor.execute("""
            INSERT INTO Permission (user_id, folder_id, granted_by, permission_type)
            VALUES (%s, %s, %s, 'Edit')
        """, (user_id, folder_id, granted_by))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    return jsonify({"message": "Employee assigned successfully"})

@pm_bp.route("/project/employees/<int:project_id>", methods=["GET"])
def get_project_employees(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT u.user_id, u.name
        FROM User u
        JOIN Permission perm ON u.user_id = perm.user_id
        JOIN Folder f ON perm.folder_id = f.folder_id
        WHERE f.project_id = %s
    """, (project_id,))
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(employees)