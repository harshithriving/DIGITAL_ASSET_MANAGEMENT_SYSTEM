from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from routes.project_routes import project_bp
from routes.file_routes import file_bp

app.register_blueprint(project_bp)
app.register_blueprint(file_bp)

if __name__ == "__main__":
    app.run(debug=True)