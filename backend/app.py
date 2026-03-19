from flask import Flask
from routes.project_routes import project_bp
from routes.client_routes import client_bp
from routes.employee_routes import employee_bp
from routes.pm_routes import pm_bp
from routes.admin_routes import admin_bp
from routes.file_routes import file_bp
from routes.pm_routes import pm_bp
from routes.comment_routes import comment_bp
from routes.user_routes import user_bp



app = Flask(__name__)

# Register Blueprints
app.register_blueprint(user_bp)
app.register_blueprint(client_bp)
app.register_blueprint(pm_bp)
app.register_blueprint(project_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(file_bp)
app.register_blueprint(comment_bp)

if __name__ == "__main__":
    app.run(debug=True)