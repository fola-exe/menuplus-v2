import os

from flask import Flask, redirect, send_from_directory, url_for

from .extensions import db


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        static_url_path="",
    )

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(app.instance_path, "menuplus.db"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    with app.app_context():
        # Import models inside context to ensure they are registered with SQLAlchemy
        from . import models
        db.create_all()

    @app.route("/assets/<path:filename>")
    def asset_file(filename):
        return send_from_directory(app.static_folder + "/assets", filename)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    from .blueprints.admin import bp as admin_bp
    from .blueprints.admin_auth import bp as admin_auth_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.customer import bp as customer_bp
    from .blueprints.menu import bp as menu_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(menu_bp)

    return app
