import random
from datetime import date, datetime
from string import ascii_letters

from flask_login import UserMixin
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from werkzeug.security import check_password_hash, generate_password_hash

from app_folder import app_run, db
from app_folder import login

User_Records = db.Table('User_Records',
                        db.Column('user_id', db.Integer, db.ForeignKey('Users.id'), primary_key=True),
                        db.Column('member_id', db.Integer, db.ForeignKey('Profiles.member_id'), primary_key=True)
                        )

Cache_Records = db.Table('Cache_Records',
                         db.Column('cache_id', db.String(16), db.ForeignKey('UserCache.cache_id'), primary_key=True),
                         db.Column('member_id', db.Integer, db.ForeignKey('Profiles.member_id'), primary_key=True)
                         )

profile_skill_table = db.Table('profile_skill',
                               db.Column('skill_id', db.Integer, db.ForeignKey('Skill.id'), primary_key=True),
                               db.Column('member_id', db.Integer, db.ForeignKey('Profiles.member_id'), primary_key=True)
                               )


# TODO Relationship Record to Positions


class Job(db.Model):
    """
    Many-to-One : LinkedInProfile
    One-to-One : Company

    current: Most current position?
    title: Job Title
    company: The associated company
    company_id: company id key
    start_date:
    end_date:
    text: Job description
    member_id:
    member:
    """

    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    current = db.Column(db.Boolean, nullabe=True)
    title = db.Column(db.Text)
    company = db.relationship("Company", uselist=False, back_populates="jobs")
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    summary = db.Column(db.Text)
    member_id = db.Column(db.Integer, db.ForeignKey('Profiles.id'))
    member = db.relationship("LinkedInRecord", back_populates="positions")


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    company_names = db.relationship("CompanyName", back_populates="company")
    external_identifiers = db.Column(db.Integer, nullable=True)
    partner_id = db.Column(db.Integer, default=None, nullable=True)
    jobs = db.relationship("Job", back_populates="company")


class CompanyName(db.Model):
    __tablename__ = 'company_names'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    company = db.relationship("Company", uselist=False, back_populates="company_names")
    name = db.Column(db.Text)


class Education(db.Model):
    __tablename__ = 'educations'
    id = db.Column(db.Integer, primary_key=True)
    current = db.Column(db.Boolean)
    education_school = db.Column(db.Text)
    education_start = db.Column(db.Date)
    education_end = db.Column(db.Date, nullable=True)
    education_degree = db.Column(db.Text)
    education_study_field = db.Column(db.Text)
    member_id = db.Column(db.Integer, db.ForeignKey('Profiles.id'))
    member = db.relationship("LinkedInRecord", back_populates="educations", uselist=False)


class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    members = db.relationship("LinkedInRecord", secondary=profile_skill_table, backpopulates="skills")


class LinkedInRecord(db.Model):
    """
    DB Model for Profile Data
    """
    __tablename__ = 'Profiles'
    member_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    created = db.Column(db.Date, default=date.today())
    updated = db.Column(db.Date, default=None)
    metro = db.Column(db.Text)
    postal_code = db.Column(db.Text)
    country_code = db.Column(db.Text)
    summary = db.Column(db.Text)
    language = db.Column(db.Text)
    industry = db.Column(db.Text)
    first_graduation_date = db.Column(db.Date)
    public_url = db.Column(db.Text)
    recruiter_url = db.Column(db.Text)
    isCompanyFollower = db.Column(db.Boolean)
    careerInterests = db.Column(db.Boolean)

    positions = db.relationship("Job", back_populates="member")
    skills = db.relationship("Skill", secondary=profile_skill_table, back_populates="members")
    educations = db.relationship("Education", back_populates="member")


    def __init__(self, LinkedInProfile):
        """
        :param LinkedInProfile:
        """

        ready_keys = ['member_id', 'first_name', 'last_name', 'created', 'updated', 'metro', 'postal_code',
                      'country_code', 'summary', 'language', 'industry', 'first_graduation_date', 'public_url',
                      'recruiter_url', 'isCompanyFollower', 'careerInterests']

        rel_keys = ['positions', 'skills', 'educations']

        # Straight forward mapping
        for rk in ready_keys:
            v = getattr(LinkedInProfile, rk, None)
            if not v:
                # Prevent overwriting potentially existing data with None
                continue
            setattr(self, rk, v)

        # Relational keys
        # Positions
        position_data = getattr(LinkedInProfile, 'positions', None)
        if position_data:
            for position in position_data:
                self.make_job(position)



    def make_job(self, pd):

        ready_keys = ['current', 'job_title', 'start_date', 'end_date']
        job_keys = ['current', 'job_title', 'companyName', 'companyUrl', 'companyId', 'start_date', 'end_date',
                    'summary']

        job = Job()
        for rk in ready_keys:
            if rk in pd:
                setattr(job, rk, pd[rk])
        db.session.add(job)

        # Associate job with company
        company = self.lookup_company(pd)
        if not company:
            company = self.make_company(pd)


        self.positions.append(job)

    def lookup_company(self, pd):
        if 'companyId' in pd:
            company_result = Company.query.filter_by(external_identifiers=int(pd['companyId'])).first()
            if company_result:
                return company_result
            else:
                return None
        else:
            company_name_result = CompanyName.query.filter_by(name=pd['companyName']).first()
            if company_name_result:
                return company_name_result.company
            else:
                return None


    def make_company(self, pd):
        company = Company()
        if 'companyId' in pd:
            company.external_identifiers = int(pd['companyId'])






class UserCache(db.Model):
    """
    DB Model that holds member IDs in cached. Relationship with User (1) to many
    """
    __tablename__ = "UserCache"
    cache_id = db.Column(db.String(16), primary_key=True)
    active = db.Column(db.Boolean, default=False)
    friendly_id = db.Column(db.Text)
    # We want a backref here so that any updates to user as well as UserCache are reflected on both ends
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    profiles = db.relationship('LinkedInRecord', secondary=Cache_Records, lazy=True,
                               backref=db.backref('caches', lazy=True))
    created = db.Column(db.DateTime, default=datetime.now())

    def __init__(self):
        self.cache_id = self.generate_string

    @property
    def generate_string(self):
        """

        :return: Random ascii letters (string)
        """
        l = ascii_letters
        holder = []
        for i in range(16):
            holder.append(l[random.randrange(0, len(l))])
        return ''.join(holder)


class UserActivity(db.Model):

    __tablename__ = "UserActivity"

    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=True)
    created = db.Column(db.DateTime, default=datetime.now())
    # Tally from /profiles/
    new_records = db.Column(db.Integer, default=0)
    # Tally from /prune/
    borrowed_records = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))


class User(UserMixin, db.Model):

    __tablename__ = "Users"

    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.Text, default='normal')
    username = db.Column(db.String(128))
    password_hash = db.Column(db.Text)
    api_key = db.Column(db.Text)
    current_session_user = db.Column(db.Integer, default=0)
    caches = db.relationship('UserCache', backref='user', lazy='dynamic')
    records = db.relationship('LinkedInRecord', secondary=User_Records, lazy=True,
                              backref=db.backref('users', lazy=True))
    activities = db.relationship('UserActivity', backref='user', lazy='dynamic')
    allowance = db.Column(db.Integer, default=450)  # New records allowed per day
    # Generating a random key to return to Extension after login success

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app_run.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            print("Expired Token")
            return None  # valid token, but expired
        except BadSignature:
            print("Bad Signature")
            return None  # invalid token
        user = User.query.get(data['id'])
        if user:
            token_session = data['session']
            if token_session == user.current_session_user:
                return user
            else:
                print("Session does not match for user {}, generate new token".format(user.id))
                return None
        else:
            return False

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.id

    def get_activity(self):
        """
        Queries a User for associated UserActivities.
        Filters to UserActivities that are active=true
        If UserActivity is active, but older than 1 day, it is set active=false

        :return: UserActivity or False if no active, UserActivity < 1 day are found
        """

        active_trackers = self.activities.filter_by(active=True).all()
        if active_trackers:
            pass
        else:
            return False  # No active tracker
        current_trackers = []
        for t in active_trackers:
            if (datetime.now() - t.created).days > 0:
                t.active = False
                db.session.add(t)
                db.session.commit()
                continue
            else:
                current_trackers.append(t)
        if current_trackers:
            return current_trackers[0]
        else:  # Will occur if 1 or more active trackers must be set inactive
            return False

    def generate_new_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)
        self.current_session_user = self.current_session_user + 1



@login.user_loader
def load_user(id):
    try:
        return User.query.get(int(id))
    except ValueError:
        return User.query.filter_by(username=id)
