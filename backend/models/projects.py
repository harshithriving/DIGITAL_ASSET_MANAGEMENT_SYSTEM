from db.connection import get_db_connection

def get_all_projects():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Project")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def create_project(project_name, description, client_id, pm_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Project (project_name, description, client_user_id, project_manager_user_id)
        VALUES (%s, %s, %s, %s)
    """, (project_name, description, client_id, pm_id))

    conn.commit()
    cursor.close()
    conn.close()


def get_projects_by_client(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Project WHERE client_user_id=%s", (user_id,))
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_projects_by_pm(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Project WHERE project_manager_user_id=%s", (user_id,))
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data