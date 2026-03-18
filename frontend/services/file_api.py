import requests

def fetch_files(project_id):
    res = requests.get(f"http://127.0.0.1:5000/files/{project_id}")
    return res.json()