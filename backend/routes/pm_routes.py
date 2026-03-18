from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

pm_bp = Blueprint("pm", __name__)

# -----------------------------------
# GET PROJECTS FOR PM
# -----------------------------------
@pm_bp.route("/pm/projects/<int:user_id>", methods=["GET"])
def get_pm_projects(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM Project
        WHERE project_manager_user_id = %s
    """, (user_id,))

    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(projects)


# -----------------------------------
# GET FILES OF A PROJECT
# -----------------------------------
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


# -----------------------------------
# ADD COMMENT (PM)
# -----------------------------------
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


# -----------------------------------
# ASSIGN EMPLOYEE TO PROJECT (PERMISSION)
# -----------------------------------
@pm_bp.route("/pm/assign_employee", methods=["POST"])
def assign_employee():
    data = request.json

    user_id = data.get("user_id")       # employee
    folder_id = data.get("folder_id")   # root folder
    granted_by = data.get("granted_by")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Permission (user_id, folder_id, granted_by, permission_type)
        VALUES (%s, %s, %s, 'Edit')
    """, (user_id, folder_id, granted_by))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Employee assigned successfully"})