from flask import Flask
from flask_caching import Cache
from config import Config
from app.db import db

cache = Cache()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    cache.init_app(app)
    db.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)

    with app.app_context():
        db.create_all()

    return app
