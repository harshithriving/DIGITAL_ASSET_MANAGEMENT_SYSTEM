import requests

def fetch_projects():
    res = requests.get("http://127.0.0.1:5000/projects")
    return res.json()