from flask import Blueprint, jsonify
from db.connection import get_db_connection

admin_bp = Blueprint("admin", __name__)

# -------------------------------
# GET ALL USERS STORAGE
# -------------------------------
@admin_bp.route("/all_users_storage", methods=["GET"])
def get_storage():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT name, role, storage_used, storage_limit
        FROM User
    """)

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(users)


# -------------------------------
# ASSIGN PROJECT TO PM
# -------------------------------
@admin_bp.route("/assign_project", methods=["POST"])
def assign_project():
    from flask import request

    data = request.json
    project_id = data.get("project_id")
    pm_user_id = data.get("pm_user_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Project
        SET project_manager_user_id = %s
        WHERE project_id = %s
    """, (pm_user_id, project_id))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Project assigned successfully"})



@admin_bp.route("/audit/logs", methods=["GET"])
def get_audit_logs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT l.log_id, l.version_id, f.file_name, l.old_status, l.new_status, 
               u.name as changed_by_name, l.changed_at
        FROM File_Status_Log l
        JOIN File f ON l.file_id = f.file_id
        JOIN User u ON l.changed_by = u.user_id
        ORDER BY l.changed_at DESC
        LIMIT 50
    """)
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(logs)

@admin_bp.route("/admin/test_rollback", methods=["POST"])
def test_rollback():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.start_transaction()
        # Insert a duplicate project name (assuming project_name is unique)
        cursor.execute("INSERT INTO Project (project_name, client_user_id) VALUES ('Duplicate Project', 4)")
        cursor.execute("INSERT INTO Project (project_name, client_user_id) VALUES ('Duplicate Project', 5)")  # fails
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e), "message": "Transaction rolled back – no project was created"}), 400
    finally:
        cursor.close()
        conn.close()