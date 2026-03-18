from flask import Blueprint, request, jsonify
from models.comment import add_comment_db

file_bp = Blueprint("file_bp", __name__)

@file_bp.route("/comments", methods=["POST"])
def add_comment():
    data = request.json
    add_comment_db(data)
    return jsonify({"message": "Comment added"})