from db.connection import get_db

def get_projects():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Project")
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


def create_project(data):
    conn = get_db()
    cursor = conn.cursor()

    query = """
    INSERT INTO Project (project_name, description, client_user_id)
    VALUES (%s, %s, %s)
    """

    cursor.execute(query, (
        data["project_name"],
        data["description"],
        data["client_user_id"]
    ))

    conn.commit()
    cursor.close()
    conn.close()