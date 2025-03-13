from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here'  # Thay bằng key ngẫu nhiên an toàn

    # Import và đăng ký các blueprint
    from app.routes import auth, project, settings
    app.register_blueprint(auth.bp)
    app.register_blueprint(project.bp)
    app.register_blueprint(settings.bp)

    return app