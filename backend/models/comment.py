from db.connection import get_db_connection

def add_comment(comment, file_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Comment (comment_text, file_id, user_id)
        VALUES (%s, %s, %s)
    """, (comment, file_id, user_id))

    conn.commit()
    cursor.close()
    conn.close()
    


def get_comments(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT c.comment_text, u.name
        FROM Comment c
        JOIN User u ON c.user_id = u.user_id
        WHERE file_id=%s
    """, (file_id,))

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data