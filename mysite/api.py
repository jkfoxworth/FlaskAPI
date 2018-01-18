import sys
sys.path.append('mysite')
from app_config import AppConfiguration
from flask import Flask, render_template, session, redirect, url_for, request, abort, jsonify
from profile_parser import LinkedInProfile
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from flask_migrate import Migrate
from flask_login import login_user, LoginManager, UserMixin, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, date
import random
from string import ascii_letters
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from functools import wraps
import base64
import json

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
    updated = db.Column(db.Date, default=None)
    metro = db.Column(db.Text)
    postal_code = db.Column(db.Text)
    country_code = db.Column(db.Text)
    language = db.Column(db.Text)
    industry = db.Column(db.Text)
    skills = db.Column(db.Text)
    summary = db.Column(db.Text)

    company_0 = db.Column(db.Text)
    company_1 = db.Column(db.Text)
    company_2 = db.Column(db.Text)

    company_url_0 = db.Column(db.Text)
    company_url_1 = db.Column(db.Text)
    company_url_2 = db.Column(db.Text)

    title_0 = db.Column(db.Text)
    title_1 = db.Column(db.Text)
    title_2 = db.Column(db.Text)

    start_date_0 = db.Column(db.Date)
    end_date_0 = db.Column(db.Date)
    start_date_1 = db.Column(db.Date)
    end_date_1 = db.Column(db.Date)
    start_date_2 = db.Column(db.Date)
    end_date_2 = db.Column(db.Date)

    summary_0 = db.Column(db.Text)
    summary_1 = db.Column(db.Text)
    summary_2 = db.Column(db.Text)
    education_school = db.Column(db.Text)
    education_start = db.Column(db.Date)
    education_end = db.Column(db.Date)
    education_degree = db.Column(db.Text)
    education_study_field = db.Column(db.Text)
    public_url = db.Column(db.Text, unique=True)
    recruiter_url = db.Column(db.Text, unique=True)

    from_users = db.Column(db.Text, default=None)

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

        self.company_0 = LinkedInProfile.companyName_0
        self.company_1 = LinkedInProfile.companyName_1
        self.company_2 = LinkedInProfile.companyName_2

        self.company_url_0 = LinkedInProfile.companyUrl_0
        self.company_url_1 = LinkedInProfile.companyUrl_1
        self.company_url_2 = LinkedInProfile.companyUrl_2

        self.title_0 = LinkedInProfile.title_0
        self.title_1 = LinkedInProfile.title_1
        self.title_2 = LinkedInProfile.title_2

        self.start_date_0 = LinkedInProfile.start_date_0
        self.end_date_0 = LinkedInProfile.end_date_0
        self.start_date_1 = LinkedInProfile.start_date_1
        self.end_date_1 = LinkedInProfile.end_date_1
        self.start_date_2 = LinkedInProfile.start_date_2
        self.end_date_2 = LinkedInProfile.end_date_2

        self.summary_0 = LinkedInProfile.summary_0
        self.summary_1 = LinkedInProfile.summary_1
        self.summary_2 = LinkedInProfile.summary_2

        self.education_school = LinkedInProfile.education_school
        self.education_start = LinkedInProfile.education_start
        self.education_end = LinkedInProfile.education_end
        self.education_degree = LinkedInProfile.education_degree
        self.education_study_field = LinkedInProfile.education_study_field
        self.public_url = LinkedInProfile.public_url
        self.recruiter_url = LinkedInProfile.recruiter_url

class UserCache(db.Model):

    __tablename__ = "UserCache"
    cache_id = db.Column(db.Text, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    cached = db.Column(db.PickleType)

    def __init__(self):
        self.cache_id = self.generate_string()
        self.cached = []

    def generate_string(self):
        l = ascii_letters
        holder = []
        for i in range(16):
            holder.append(l[random.randrange(0, len(l))])
        return ''.join(holder)

    def append_cache(self, member_id):
        current_cache = self.cached
        new_cache = current_cache + [member_id]
        self.cached = new_cache

def requires_key(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        api_key = request.headers.get('Api-Key', False)
        if api_key is False:
            abort(400)
        if User.verify_auth_token(api_key) is False:
            abort(400)
        elif User.verify_auth_token(api_key) is None:
            abort(401)
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
    caches = db.relationship('UserCache', backref='user')
    # Generating a random key to return to Extension after login success

    def generate_auth_token(self, expiration=86400):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        session_number = self.new_user_session()
        cache_id = self.new_user_cache()

        print("Cache is  {}".format(cache_id))
        return s.dumps({'id': self.id, 'session': session_number, 'cache_id': cache_id})



    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            print("Expired Token")
            return None  # valid token, but expired
        except BadSignature:
            print("Bad Signature")
            return False  # invalid token
        user = User.query.get(data['id'])
        if user:
            token_session = data['session']
            if token_session == user.current_session_user:
                return user
            else:
                print("Session does not match, generate new token")
                return None
        else:
            return False

    def new_user_session(self):
        current_session = self.current_session_user
        new_session = current_session + 1
        self.current_session_user = new_session
        self.last_session_user = current_session
        db.session.commit()
        return new_session

    def new_user_cache(self):
        new_cache = UserCache()
        self.caches.append(new_cache)
        new_cache_id = new_cache.cache_id
        db.session.add(new_cache)
        db.session.commit()
        return new_cache_id


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
    api_key = request.headers.get('Api-Key')
    if api_key:
        user = User.verify_auth_token(api_key)
        if user:
            return user

    # next, try to login using Basic Auth
    api_key = request.headers.get('Authorization')
    print("Auth header {}".format(api_key))

    if api_key:
        if isinstance(api_key, bytes):
            api_key = api_key.replace(b'Basic ', b'', 1)
        elif isinstance(api_key, str):
            api_key = api_key.replace('Basic ', '', 1)
        try:
            api_key = base64.b64decode(api_key).decode()
            api_username = api_key.split(":")[0]
            api_password = api_key.split(":")[1]
        except TypeError:
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
        return abort(401)

@app.route('/api/v1/test_token', methods=['GET'])
@requires_key
def t():
    return jsonify({'message': 'valid token'})


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():

    if request.method == 'GET':
        return render_template('search.html', success='None')

    elif request.method == 'POST':

        search_query = {'title_0': '%{}%'.format(request.form.get('job_title', 'empty')),
                        'company_0': '%{}%'.format(request.form.get('company', 'empty')),
                        'metro': '%{}%'.format(request.form.get('metro', 'empty')),
                        'summary_0': '%{}%'.format(request.form.get('summary_0', 'empty'))}
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

        headers = ['Name', 'Job Title', 'Company', 'Location', 'Job Description']
        results = []
        for searched_result in search_results:
            result_tuple = (searched_result.name, searched_result.title_0, searched_result.company_0, searched_result.metro, searched_result.summary_0)
            results.append(result_tuple)
        if results:

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
@requires_key
def profile():

    if not request.json:
        abort(400)

    data = request.json
    parsed_data = LinkedInProfile(data)
    profile_record = LinkedInRecord(parsed_data)

    # Get user id to associate to the record
    user_from_api = load_user_from_request(request)
    user_id = user_from_api.id
    print("New record from {}".format(user_id))

    # Check if record already exists

    matched_records = LinkedInRecord.query.filter_by(member_id=profile_record.member_id).first()
    print(matched_records)

    if matched_records:
        print("Handled update")
        profile_record = handle_update(profile_record, user_id)
    else:
        profile_record.from_users = str(user_id) + "_"

    # Add the member id to the user's most recent cache

    user_current_cache = user_from_api.caches[0]
    user_current_cache.append_cache(parsed_data.member_id)

    db.session.add(profile_record)
    db.session.commit()

    # Form to JSON and reply with it

    return jsonify({'action': 'success'}), 201


@app.route('/api/v1/fetch', methods=['GET'])
@requires_key
def fetch_profiles():
    user_from_api = load_user_from_request(request)
    user_current_cache = user_from_api.caches[0].cached
    print(user_current_cache)

    # TODO Serve a CSV
    return jsonify({'profiles': user_current_cache})


def format_results(record):
    holder = {}
    for k, v in record.__dict__.items():
        if k[0] == '_' or k == 'updated' or k == 'from_users':
            continue
        if isinstance(v, date):
            str_v = v.strftime('%d-%m-%y')
            holder[k] = str_v
        else:
            holder[k] = v
    return holder

def handle_update(profile_record, user_id):

    # Fetch the record that is a duplicate

    old_record = LinkedInRecord.query.filter_by(member_id=profile_record.member_id).first()

    record_keys = profile_record.__dict__.keys()
    for key in record_keys:
        if key[0] == '_' or key == 'from_users' or key == 'updated':  # These will never be equal, internal key
            continue
        try:
            old_value = getattr(old_record, key)
            new_value = getattr(profile_record, key)
        except KeyError:
            continue
        if old_value != new_value:
            setattr(old_record, new_value)

        old_record.__dict__[k] = v
    old_record.updated = date.today()
    current_from_users = old_record.from_users
    old_record.from_users = current_from_users + "_" + str(user_id) + "_"

    return old_record




if __name__ == '__main__':
    app.run()
