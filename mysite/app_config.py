class AppConfiguration(object):

    secret_key = "Offline"
    db_values = {'SQLALCHEMY_DATABASE_URI':'sqlite:///app.db', 'SQLALCHEMY_TRACK_MODIFICATIONS': False}
    create_all = True
    login_view = 'index'
    debug = True



