import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'mysql://estasney:password@localhost:3306/profiles2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 299
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    EXPLAIN_TEMPLATE_LOADING = False
    PRESERVE_CONTEXT_ON_EXCEPTION = True
    PROPAGATE_EXCEPTIONS = True
    TESTING = False
    TRAP_BAD_REQUEST_ERRORS = True
    TRAP_HTTP_EXCEPTIONS = True
    USE_DEBUGGER = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    USE_RELOADER = False
    UPLOAD_FOLDER = os.path.join(basedir, 'app_folder/uploads')
    USE_DEBUGGER = False
    USE_RELOADER = False


class FConfig(object):
    COUNTRY_DICT = os.path.join(basedir, 'app_folder/country_codes.pkl')
    ZIP_DICT = os.path.join(basedir, 'app_folder/zips_to_states.pkl')
    UPLOAD_FOLDER = os.path.join(basedir, 'app_folder/uploads')
