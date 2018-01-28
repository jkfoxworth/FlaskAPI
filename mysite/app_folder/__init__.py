from flask import Flask
from site_config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app_run = Flask(__name__)
app_run.config.from_object(Config)
db = SQLAlchemy(app_run)
migrate = Migrate(app_run, db)
login = LoginManager(app_run)
login.login_view = 'login'

from app_folder import routes, models

# Does this re