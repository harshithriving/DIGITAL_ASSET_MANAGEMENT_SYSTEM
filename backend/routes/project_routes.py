from flask import Blueprint, jsonify
from db.connection import get_db_connection

project_bp = Blueprint("projects", __name__)

@project_bp.route("/projects")
def get_projects():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Project")
    projects = cursor.fetchall()
    conn.close()
    return jsonify(projects)