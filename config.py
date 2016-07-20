import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True
SESSION_COOKIE_NAME = "SessionId"
SESSION_COOKIE_HTTPONLY = True
#SESSION_COOKIE_SECURE = True TODO uncomment this in production
SESSION_SQLALCHEMY = True
SESSION_SQLALCHEMY_TABLE = "sessions"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER =  os.path.join(BASE_DIR, "uploads")