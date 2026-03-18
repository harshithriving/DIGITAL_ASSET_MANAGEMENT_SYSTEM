from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

client_bp = Blueprint("client", __name__)

# -------------------------------
# CREATE PROJECT
# -------------------------------
@client_bp.route("/client/projects", methods=["POST"])
def create_project():
    data = request.json

    project_name = data.get("project_name")
    description = data.get("description")
    client_user_id = data.get("client_user_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Project (project_name, description, client_user_id)
        VALUES (%s, %s, %s)
    """, (project_name, description, client_user_id))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Project created successfully"})


# -------------------------------
# GET CLIENT PROJECTS
# -------------------------------
@client_bp.route("/client/projects/<int:user_id>", methods=["GET"])
def get_client_projects(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM Project
        WHERE client_user_id = %s
    """, (user_id,))

    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(projects)