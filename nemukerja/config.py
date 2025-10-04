import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/nemukerja_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
