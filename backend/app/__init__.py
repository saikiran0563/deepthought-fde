import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    database_url = os.getenv("DATABASE_URL") or "sqlite:///deepthought.db"

    # Normalize PostgreSQL URLs for the psycopg 3 driver.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://", "postgresql+psycopg://", 1
        )
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

    if test_config:
        app.config.update(test_config)

    origins = os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )
    allowed_origins = [
        origin.strip() for origin in origins.split(",") if origin.strip()
    ]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    db.init_app(app)

    from app import models
    from app.routes import register_routes
    from app.coach import register_coach_routes

    register_routes(app)
    register_coach_routes(app)

    with app.app_context():
        db.create_all()

    return app
