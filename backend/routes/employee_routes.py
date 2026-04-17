from flask import Blueprint, jsonify
from db.connection import get_db_connection

employee_bp = Blueprint("employee", __name__)

@employee_bp.route("/employee/projects/<int:user_id>", methods=["GET"])
def get_employee_projects(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT p.*
        FROM Project p
        JOIN Folder f ON p.project_id = f.project_id
        JOIN Permission perm ON f.folder_id = perm.folder_id
        WHERE perm.user_id = %s
    """, (user_id,))
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(projects)

@employee_bp.route("/employee/project_count/<int:user_id>", methods=["GET"])
def get_employee_project_count(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT COUNT(DISTINCT p.project_id) as project_count
        FROM Project p
        JOIN Folder f ON p.project_id = f.project_id
        JOIN Permission perm ON f.folder_id = perm.folder_id
        WHERE perm.user_id = %s
    """, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"project_count": result['project_count'] if result else 0})


