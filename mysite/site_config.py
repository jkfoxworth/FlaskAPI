import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'mysql://estasney:password@localhost:3306/dummy'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

class FConfig(object):
    COUNTRY_DICT = os.path.join(basedir, 'app_folder/country_codes.pkl')
    ZIP_DICT = os.path.join(basedir, 'app_folder/zips_to_states.pkl')
