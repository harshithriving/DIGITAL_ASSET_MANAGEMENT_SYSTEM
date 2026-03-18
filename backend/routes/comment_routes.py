from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

comment_bp = Blueprint("comment", __name__)

# -------------------------------
# ADD COMMENT
# -------------------------------
@comment_bp.route("/comments", methods=["POST"])
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


# -------------------------------
# GET COMMENTS BY FILE
# -------------------------------
@comment_bp.route("/comments/<int:file_id>", methods=["GET"])
def get_comments(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT c.comment_text, u.name
        FROM Comment c
        JOIN User u ON c.user_id = u.user_id
        WHERE c.file_id = %s
    """, (file_id,))

    comments = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(comments)