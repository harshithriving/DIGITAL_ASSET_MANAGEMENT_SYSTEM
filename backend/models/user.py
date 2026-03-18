from db.connection import get_db_connection

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM User")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_storage_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT name, role, storage_used, storage_limit
        FROM User
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data