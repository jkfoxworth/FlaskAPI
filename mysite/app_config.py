class AppConfiguration(object):

    secret_key = "Offline"
    db_values = {'SQLALCHEMY_DATABASE_URI':'sqlite:///profiles.sqlite3', 'SQLALCHEMY_TRACK_MODIFICATIONS': False}
    create_all = False
    login_view = 'index'
