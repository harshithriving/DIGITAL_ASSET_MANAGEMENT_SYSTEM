from db.connection import get_db_connection

def get_files_by_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT f.*
        FROM File f
        JOIN Folder fol ON f.folder_id = fol.folder_id
        WHERE fol.project_id = %s
    """, (project_id,))

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data