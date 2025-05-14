from flask import Flask, render_template
from .config import Config
from .extensions import db, login_manager
from .models import User
from .blueprints.web import web_bp
from .blueprints.auth import auth_bp
from .blueprints.chatbot import chatbot_bp
from .blueprints.api import api_bp


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True, template_folder="templates")

    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.errorhandler(404)
    def not_found_error(error):
        """Handles 404 Not Found errors."""
        return (
            render_template(
                "error.html.jinja2",
                error_code=404,
                error_message="Page Not Found",
                error_description="Sorry, the page you are looking for does not exist, might have been moved, or is temporarily unavailable.",
            ),
            404,
        )

    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handles 401 Unauthorized errors."""
        return (
            render_template(
                "error.html.jinja2",
                error_code=401,
                error_message="Unauthorized Access",
                error_description="You need to be logged in or have the correct permissions to view this page.",
            ),
            401,
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handles 500 Internal Server Error."""
        db.session.rollback()
        return (
            render_template(
                "error.html.jinja2",
                error_code=500,
                error_message="Internal Server Error",
                error_description="We encountered an unexpected issue while processing your request. Please try again later.",
            ),
            500,
        )

    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
