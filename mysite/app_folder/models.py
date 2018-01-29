from app_folder import app_run, db
from werkzeug.security import check_password_hash
from flask_login import UserMixin
from app_folder import login
from datetime import date, datetime
from string import ascii_letters
import random
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

# Login checking can be done here
# Classes Here


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


User_Records = db.Table('User_Records',
                        db.Column('user_id', db.Integer, db.ForeignKey('Users.id'), primary_key=True),
                        db.Column('member_id', db.Integer, db.ForeignKey('Profiles.member_id'), primary_key=True)
                        )

Cache_Records = db.Table('Cache_Records',
                         db.Column('cache_id', db.String(16), db.ForeignKey('UserCache.cache_id'), primary_key=True),
                         db.Column('member_id', db.Integer, db.ForeignKey('Profiles.member_id'), primary_key=True)
                         )


class LinkedInRecord(db.Model):
    """
    DB Model for Profile Data
    """
    __tablename__ = 'Profiles'
    member_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    summary = db.Column(db.Text)

    metro = db.Column(db.Text)
    postal_code = db.Column(db.Text)
    country_code = db.Column(db.Text)
    language = db.Column(db.Text)
    industry = db.Column(db.Text)
    skills = db.Column(db.Text)

    companyName_0 = db.Column(db.Text)
    companyUrl_0 = db.Column(db.Text)
    title_0 = db.Column(db.Text)
    start_date_0 = db.Column(db.Date)
    end_date_0 = db.Column(db.Date)
    summary_0 = db.Column(db.Text)

    companyName_1 = db.Column(db.Text)
    companyUrl_1 = db.Column(db.Text)
    title_1 = db.Column(db.Text)
    start_date_1 = db.Column(db.Date)
    end_date_1 = db.Column(db.Date)
    summary_1 = db.Column(db.Text)

    companyName_2 = db.Column(db.Text)
    companyUrl_2 = db.Column(db.Text)
    title_2 = db.Column(db.Text)
    start_date_2 = db.Column(db.Date)
    end_date_2 = db.Column(db.Date)
    summary_2 = db.Column(db.Text)

    created = db.Column(db.Date, default=date.today())
    updated = db.Column(db.Date, default=None)

    education_school = db.Column(db.Text)
    education_start = db.Column(db.Date)
    education_end = db.Column(db.Date)
    education_degree = db.Column(db.Text)
    education_study_field = db.Column(db.Text)
    public_url = db.Column(db.Text)
    recruiter_url = db.Column(db.Text)

    def __init__(self, LinkedInProfile):
        """
        :param LinkedInProfile:
        """
        for k, v in LinkedInProfile.__dict__.items():
            if k[0] == '_': # Include or exclude properties based on _prop naming convetion
                continue
            try:
                setattr(self, k, v)
            except AttributeError:
                self._set_entry(k, v)

    def _set_entry(self, k, v):
        # Handles if Table object is intended to be internal
        k_ = "_" + k
        setattr(self, k_, v)


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
        return self.username
