import os
from flask import Flask, render_template, session, redirect, url_for, request, abort, jsonify
from mysite.profile_parser import LinkedInProfile
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///profiles.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class LinkedInRecord(db.Model):
    __tablename__ = 'Profiles'
    member_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
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




@app.route('/', methods=['GET', 'POST'])
def index():
    return '<h1>Hello</h1>'

@app.route('/profiles', methods=['GET'])
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

    pp = LinkedInProfile(member_id=profile['member_id'], recruiter_url=profile['recruiter_url'],
                         raw_html=profile['raw_html'])

    profile_record = LinkedInRecord(pp.sqlData)

    # Is the profile already present?



    db.session.add(profile_record)
    print("Added")
    db.session.commit()
    return jsonify({'status': 'success'}), 201

if __name__ == '__main__':
    db.create_all()
    app.run()
