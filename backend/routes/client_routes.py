from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

client_bp = Blueprint("client", __name__)

@client_bp.route("/client/projects", methods=["POST"])
def create_project():
    data = request.json
    project_name = data.get("project_name")
    description = data.get("description")
    client_user_id = data.get("client_user_id")
    if not project_name or not client_user_id:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert project
        cursor.execute("""
            INSERT INTO Project (project_name, description, client_user_id)
            VALUES (%s, %s, %s)
        """, (project_name, description, client_user_id))
        project_id = cursor.lastrowid

        # Create root folder
        cursor.execute("""
            INSERT INTO Folder (folder_name, project_id, is_root, parent_folder_id)
            VALUES (%s, %s, %s, %s)
        """, ("Root Folder", project_id, 1, None))
        root_id = cursor.lastrowid

        # Create default subfolders
        default_folders = ["Images", "Videos", "Audio", "Others"]
        for folder in default_folders:
            cursor.execute("""
                INSERT INTO Folder (folder_name, project_id, parent_folder_id, is_root)
                VALUES (%s, %s, %s, %s)
            """, (folder, project_id, root_id, 0))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Project created successfully", "project_id": project_id}), 201

@client_bp.route("/client/projects", methods=["GET"])
def get_projects():
    client_id = request.args.get("client_id")
    if not client_id:
        return jsonify({"error": "client_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT project_id, project_name, description, project_manager_user_id
            FROM Project
            WHERE client_user_id = %s
        """, (client_id,))
        projects = cursor.fetchall()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(projects), 200