import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'mysql://estasney:password@localhost:3306/profiles2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 299
    DEBUG = True
    USE_DEBUGGER = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    USE_RELOADER = False
    UPLOAD_FOLDER = os.path.join(basedir, 'app_folder/uploads')

class FConfig(object):
    COUNTRY_DICT = os.path.join(basedir, 'app_folder/country_codes.pkl')
    ZIP_DICT = os.path.join(basedir, 'app_folder/zips_to_states.pkl')
    UPLOAD_FOLDER = os.path.join(basedir, 'app_folder/uploads')
