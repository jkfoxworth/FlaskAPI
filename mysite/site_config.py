import os
basedir = os.path.abspath(os.path.dirname(__file__))
print(basedir)

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

class FConfig(object):
    COUNTRY_DICT = r"C:\Users\estasney\PycharmProjects\FlaskAPIWeb\mysite\app_folder\country_codes.pkl"
    ZIP_DICT = r"C:\Users\estasney\PycharmProjects\FlaskAPIWeb\mysite\app_folder\zips_to_states.pkl"
