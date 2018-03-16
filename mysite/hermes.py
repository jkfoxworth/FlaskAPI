from app_folder import app_run, db
from app_folder.models import User, UserCache, User_Records, UserActivity, CompanyName, Company, LinkedInRecord, Skill,\
    Job
from werkzeug.security import generate_password_hash


@app_run.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'UserCache': UserCache, 'User_Records': User_Records, 'UserActivity': UserActivity,
            'CompanyName': CompanyName, 'Company': Company, 'LinkedInRecord': LinkedInRecord, 'Skill': Skill,
            'Job': Job, 'generate_password_hash': generate_password_hash}
