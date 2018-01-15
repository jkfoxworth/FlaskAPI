from app_config import AppConfiguration
from flask import Flask, render_template, session, redirect, url_for, request, abort, jsonify
from profile_parser import LinkedInProfile
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text
from flask_migrate import Migrate
from flask_login import login_user, LoginManager, UserMixin, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, date
from random import randrange
from string import ascii_letters
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from functools import wraps
import base64

app = Flask(__name__)
app.config['DEBUG'] = True
for k, v in AppConfiguration.db_values.items():
    app.config[k] = v

db = SQLAlchemy(app)

if AppConfiguration.create_all is True:
    db.create_all()

migrate = Migrate(app, db)

app.secret_key = AppConfiguration.secret_key
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = AppConfiguration.login_view


class LinkedInRecord(db.Model):
    __tablename__ = 'Profiles'
    member_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    created = db.Column(db.Date, default=date.today())
    updated = db.Column(db.Date)
    metro = db.Column(db.Text)
    postal_code = db.Column(db.Text)
    language = db.Column(db.Text)
    industry = db.Column(db.Text)
    skills = db.Column(db.Text)
    summary = db.Column(db.Text)
    company_0 = db.Column(db.Text)
    company_url_0 = db.Column(db.Text)
    title_0 = db.Column(db.Text)
    start_date_0 = db.Column(db.Date)
    end_date_0 = db.Column(db.Date)
    description_0 = db.Column(db.Text)
    company_1 = db.Column(db.Text)
    company_url_1 = db.Column(db.Text)
    title_1 = db.Column(db.Text)
    start_date_1 = db.Column(db.Date)
    end_date_1 = db.Column(db.Date)
    description_1 = db.Column(db.Text)
    company_2 = db.Column(db.Text)
    company_url_2 = db.Column(db.Text)
    title_2 = db.Column(db.Text)
    start_date_2 = db.Column(db.Date)
    end_date_2 = db.Column(db.Date)
    description_2 = db.Column(db.Text)
    education_school = db.Column(db.Text)
    education_start = db.Column(db.Date)
    education_end = db.Column(db.Date)
    education_degree = db.Column(db.Text)
    education_study_field = db.Column(db.Text)
    public_url = db.Column(db.Text, unique=True)
    recruiter_url = db.Column(db.Text, unique=True)

    def __init__(self, LinkedInProfile):

        self.member_id = LinkedInProfile.member_id
        self.name = LinkedInProfile.name
        self.metro = LinkedInProfile.metro
        self.postal_code = LinkedInProfile.postal_code
        self.country_code = LinkedInProfile.country_code
        self.language = LinkedInProfile.language
        self.industry = LinkedInProfile.industry
        self.skills = LinkedInProfile.skills
        self.summary = LinkedInProfile.summary
        self.company_name_0 = LinkedInProfile.companyName_0
        self.company_url_0 = LinkedInProfile.companyUrl_0
        self.title_0 = LinkedInProfile.title_0
        self.start_date_0 = LinkedInProfile.start_date_0
        self.end_date_0 = LinkedInProfile.end_date_0
        self.summary_0 = LinkedInProfile.summary_0
        self.company_name_1 = LinkedInProfile.companyName_1
        self.company_url_1 = LinkedInProfile.companyUrl_1
        self.title_1 = LinkedInProfile.title_1
        self.start_date_1 = LinkedInProfile.start_date_1
        self.end_date_1 = LinkedInProfile.end_date_1
        self.summary_1 = LinkedInProfile.summary_1
        self.company_name_2 = LinkedInProfile.companyName_2
        self.company_url_2 = LinkedInProfile.companyUrl_2
        self.title_2 = LinkedInProfile.title_2
        self.start_date_2 = LinkedInProfile.start_date_2
        self.end_date_2 = LinkedInProfile.end_date_2
        self.summary_2 = LinkedInProfile.summary_2
        self.education_school = LinkedInProfile.education_school
        self.education_start = LinkedInProfile.education_start
        self.education_end = LinkedInProfile.education_end
        self.education_degree = LinkedInProfile.education_degree
        self.education_study_field = LinkedInProfile.education_study_field
        self.public_url = LinkedInProfile.public_url
        self.recruiter_url = LinkedInProfile.recruiter_url

def requires_key(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        api_key = request.args.get('api_key', False)
        if api_key is False:
            abort(400)
        if User.verify_auth_token(api_key) is False:
            abort(400)
        elif User.verify_auth_token(api_key) is None:
            abort(400)
        else:
            return func(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapped



class User(UserMixin, db.Model):

    __tablename__ = "Users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    api_key = db.Column(db.Text)
    current_session_user = db.Column(db.Integer, default=0)
    last_session_user = db.Column(db.Integer)

    # Generating a random key to return to Extension after login success
    def generate_auth_token(self, expiration=86400):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        session_number = self.new_user_session()
        print("Token session number issued is : {}".format(session_number))
        return s.dumps({'id': self.id, 'session': session_number})



    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        if user:
            token_session = data['session']
            if token_session == user.current_session_user:
                return user
            else:
                print("Session does not match, generate new token")
                return None
        else:
            return None

    def new_user_session(self):
        current_session = self.current_session_user
        new_session = current_session + 1
        self.current_session_user = new_session
        self.last_session_user = current_session
        db.session.commit()
        return new_session

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

# TODO Add table mapping User to associated sessions
# TODO Add table mapping sessions to records


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()


@login_manager.request_loader
def load_user_from_request(request):

    # first, try to login using the api_key url arg
    api_key = request.headers.get('api_key')
    if api_key:
        user = User.verify_auth_token(api_key)
        if user:
            return user

    # next, try to login using Basic Auth
    api_key = request.headers.get('Authorization')
    print("Auth header {}".format(api_key))

    if api_key:
        if isinstance(api_key, bytes):
            print("Key is bytes")
            api_key = api_key.replace(b'Basic ', b'', 1)
        elif isinstance(api_key, str):
            print("Key is string")
            api_key = api_key.replace('Basic ', '', 1)
        try:
            api_key = base64.b64decode(api_key).decode()
            print("KEY Decode to {}".format(api_key))
            api_username = api_key.split(":")[0]
            api_password = api_key.split(":")[1]
            print("Username is {}".format(api_username))
            print("Password is {}".format(api_password))
        except TypeError:
            print("Type error")
            pass
        user = User.query.filter_by(username=api_username).first()
        if user:
            if user.check_password(api_password):
                return user
        else:
            return None

    # finally, return None if both methods did not login the user
    return None


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('welcome.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login_page.html", error=False)

    user = load_user(request.form['username'])
    if user is None:
        return render_template("login_page.html", error=True)

    if not user.check_password(request.form['password']):
        return render_template('login_page.html', error=True)

    login_user(user)
    return redirect(url_for('index'))


@app.route('/api/v1/token', methods=['POST'])
def get_auth_token():

    # Requires authorization

    user = load_user_from_request(request)
    print(user)
    if user:
        token = user.generate_auth_token()
        return jsonify({'token': token.decode('ascii')})
    else:
        return abort(404)

@app.route('/api/v1/test', methods=['GET'])
@requires_key
def t():
    return jsonify({'message': 'success'})


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():

    if request.method == 'GET':
        return render_template('search.html', success='None')

    elif request.method == 'POST':


        search_query = {'title_0': '%{}%'.format(request.form.get('job_title', 'empty')),
                        'company_0': '%{}%'.format(request.form.get('company', 'empty')),
                        'metro': '%{}%'.format(request.form.get('metro', 'empty'))}
                        # 'keywords': '%{}%'.format(request.form.get('keywords', 'empty'))}


        search_query = {k: v for (k, v) in search_query.items() if v != '%empty%' and v != '%%'}
        print(search_query)

        if search_query == {}:
            return render_template('search.html', success='None')

        base_query = LinkedInRecord.query
        for k, v in search_query.items():

            base_query = base_query.filter(LinkedInRecord.__dict__[k].ilike(v))

        print(base_query)
        search_results = base_query.all()
        print(search_results)

        # TODO Better way to define headers, return values

        headers = ['Name', 'Job Title', 'Company', 'Location', 'Skills']
        results = []
        for searched_result in search_results:
            result_tuple = (searched_result.name, searched_result.title_0, searched_result.company_0, searched_result.metro, searched_result.skills)
            results.append(result_tuple)
        if results:
            print("Prinitng results")
            return render_template('results.html', success='True', headers=headers, results=results)
        else:
            return render_template('search.html', success='False')

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profiles', methods=['GET'])
@login_required
def list():
    return render_template("list.html", rows=LinkedInRecord.query.all())

@app.route('/api/v1/profiles', methods=['POST'])
def profile():
    if not request.json:
        abort(400)

    data = request.json

    parsed_data = LinkedInProfile(data)

    profile_record = LinkedInRecord(parsed_data)

    # Is the profile already present?
    #
    db.session.add(profile_record)
    db.session.commit()
    return jsonify({'status': 'success'}), 201

if __name__ == '__main__':
    app.run()
