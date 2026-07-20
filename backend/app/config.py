import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///youthscores.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PythonAnywhere kills idle MySQL connections after 300s.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    JSON_AS_ASCII = False

    # Push notifications (Firebase Cloud Messaging).
    # Path to the FCM service-account JSON. Unset -> notifications run in
    # dry-run mode: the message is logged, never sent.
    FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS")
    # Optional; taken from the service-account JSON when not given.
    FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID")

    # Guards the admin write endpoints (create news/venue, etc.).
    ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")

    # Uploaded images. UPLOAD_FOLDER defaults to instance/uploads (set in the
    # app factory). Cap request bodies so a huge file can't exhaust memory.
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024  # 12 MB


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
    # A predictable key so the admin endpoints are usable locally. Override in
    # any real deployment via the ADMIN_API_KEY env var.
    ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "dev-admin-key")


CONFIGS = {
    "production": ProductionConfig,
    "development": DevelopmentConfig,
}
