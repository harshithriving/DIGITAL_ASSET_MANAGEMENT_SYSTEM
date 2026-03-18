from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

project_bp = Blueprint("project", __name__)

# -------------------------------
# GET ALL PROJECTS
# -------------------------------
@project_bp.route("/projects", methods=["GET"])
def get_projects():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Project")
    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(projects)


# -------------------------------
# CREATE PROJECT
# -------------------------------
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

    cursor.close()
    conn.close()

    return jsonify({"message": "Project created successfully"})