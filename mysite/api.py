from app_config import AppConfiguration
from flask import Flask, render_template, session, redirect, url_for, request, abort, jsonify
from profile_parser import LinkedInProfile
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text
from flask_migrate import Migrate
from flask_login import login_user, LoginManager, UserMixin, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime

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
    name = db.Column(db.String(128))
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow)
    metro = db.Column(db.Text)
    zip_code = db.Column(db.Text)
    language = db.Column(db.Text)
    industry = db.Column(db.Text)
    skills = db.Column(db.Text)
    summary = db.Column(db.Text)
    company_0 = db.Column(db.Text)
    company_url_0 = db.Column(db.Text)
    title_0 = db.Column(db.Text)
    dates_0 = db.Column(db.Text)
    description_0 = db.Column(db.Text)
    company_1 = db.Column(db.Text)
    company_url_1 = db.Column(db.Text)
    title_1 = db.Column(db.Text)
    dates_1 = db.Column(db.Text)
    description_1 = db.Column(db.Text)
    company_2 = db.Column(db.Text)
    company_url_2 = db.Column(db.Text)
    title_2 = db.Column(db.Text)
    dates_2 = db.Column(db.Text)
    description_2 = db.Column(db.Text)
    education = db.Column(db.PickleType)
    public_url = db.Column(db.Text)
    recruiter_url = db.Column(db.Text)
    work_history = db.Column(db.PickleType)


    def __init__(self, sd):

        self.member_id = sd['member_id']
        self.name = sd['name']
        self.metro = sd['metro']
        self.zip_code = sd['zip_code']
        self.language = sd['language']
        self.industry = sd['industry']
        self.skills = sd['skills']
        self.summary = sd['summary']
        self.company_0 = sd['company_0']
        self.company_url_0 = sd['company_url_0']
        self.title_0 = sd['title_0']
        self.dates_0 = sd['dates_0']
        self.description_0 = sd['description_0']
        self.company_1 = sd['company_1']
        self.company_url_1 = sd['company_url_1']
        self.title_1 = sd['title_1']
        self.dates_1 = sd['dates_1']
        self.description_1 = sd['description_1']
        self.company_2 = sd['company_2']
        self.company_url_2 = sd['company_url_2']
        self.title_2 = sd['title_2']
        self.dates_2 = sd['dates_2']
        self.description_2 = sd['description_2']
        self.work_history = sd['work_history']
        self.education = sd['education']
        self.public_url = sd['public_url']
        self.recruiter_url = sd['recruiter_url']



class User(UserMixin, db.Model):

    __tablename__ = "Users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username




@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()


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

    profile = {
        'member_id': request.json['id'],
        'recruiter_url': request.json['purl'],
        'raw_html': request.json['raw_html']
        }

    print(profile['raw_html'])

    pp = LinkedInProfile(member_id=profile['member_id'], recruiter_url=profile['recruiter_url'],
                         raw_html=profile['raw_html'])

    profile_record = LinkedInRecord(pp.sqlData)

    # Is the profile already present?

    db.session.add(profile_record)
    db.session.commit()
    return jsonify({'status': 'success'}), 201

if __name__ == '__main__':
    app.run()
