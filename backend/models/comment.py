from db.connection import get_db

def add_comment_db(data):
    conn = get_db()
    cursor = conn.cursor()

    query = """
    INSERT INTO Comment (comment_text, file_id, user_id)
    VALUES (%s, %s, %s)
    """

    cursor.execute(query, (
        data["comment"],
        data["file_id"],
        data["user_id"]
    ))

    conn.commit()
    cursor.close()
    conn.close()