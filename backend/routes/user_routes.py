from flask import Blueprint, jsonify
from db.connection import get_db_connection

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/users/<role>", methods=["GET"])
def get_users_by_role(role):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, name FROM User WHERE role = %s", (role,))
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)

@user_bp.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, name, email, role, storage_used, storage_limit FROM User WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

@user_bp.route("/employees", methods=["GET"])
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT u.user_id, u.name FROM User u JOIN Employee e ON u.user_id = e.user_id")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(employees)