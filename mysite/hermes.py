from app_folder import app_run, db
from app_folder.models import User
from werkzeug.security import generate_password_hash


@app_run.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'generate_password_hash': generate_password_hash}