from flask import Blueprint, jsonify
from db.connection import get_db_connection

employee_bp = Blueprint("employee", __name__)

# -------------------------------
# GET PROJECTS ASSIGNED TO EMPLOYEE
# -------------------------------
@employee_bp.route("/employee/projects/<int:user_id>", methods=["GET"])
def get_employee_projects(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.*
        FROM Project p
        JOIN Permission perm ON p.project_id = perm.folder_id
        WHERE perm.user_id = %s
    """, (user_id,))

    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(projects)