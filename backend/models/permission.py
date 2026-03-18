from db.connection import get_db_connection

def assign_permission(user_id, folder_id, granted_by):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Permission (user_id, folder_id, granted_by, permission_type)
        VALUES (%s, %s, %s, 'Edit')
    """, (user_id, folder_id, granted_by))

    conn.commit()
    cursor.close()
    conn.close()