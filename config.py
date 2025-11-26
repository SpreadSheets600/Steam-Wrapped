import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key-please-change"

    STEAM_API_KEY = os.environ.get("STEAM_API_KEY")

    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///steam_wrapped.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CACHE_TYPE = "FileSystemCache"
    CACHE_DIR = os.path.join(os.path.dirname(__file__), "app/cache")
    CACHE_DEFAULT_TIMEOUT = 3600

    SESSION_TYPE = "filesystem"
