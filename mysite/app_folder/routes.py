from app_folder import app_run, db, login, csv_parser, profile_parser
from app_folder.models import User, LinkedInRecord, UserCache
from flask import render_template, redirect, url_for, request, abort, jsonify, Response
from flask_login import login_user, current_user, logout_user, login_required
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from functools import wraps
import base64
from datetime import date
from operator import itemgetter
import string


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


def generate_auth_token(user_id, session_number, cache_id, expiration=86400):
    s = Serializer(app_run.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id': user_id, 'session': session_number, 'cache_id': cache_id})


def update_user_token(user):
    current_session = user.current_session_user
    new_session = current_session + 1
    # Increment session number
    user.current_session_user = new_session
    # Create a new Cache and append to user's caches
    new_cache = UserCache()
    cache_name = new_cache.cache_id
    user_id_ = user.id
    user.caches.append(new_cache)
    db.session.add(user)
    db.session.commit()
    auth_token = generate_auth_token(user_id_, new_session, cache_name)
    return auth_token


@login.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()


@login.request_loader
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
    else:
        return None
    return None


@app_run.route('/', methods=['GET', 'POST'])
def index():
    return render_template('welcome.html')


@app_run.route('/login/', methods=['GET', 'POST'])
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


@app_run.route('/search', methods=['GET', 'POST'])
@login_required
def search():

    if request.method == 'GET':
        return render_template('search.html', success='None')

    elif request.method == 'POST':

        search_query = {'title_0': '%{}%'.format(request.form.get('job_title', 'empty')),
                        'companyName_0': '%{}%'.format(request.form.get('company', 'empty')),
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

        search_results = base_query.all()


        # TODO Better way to define headers, return values

        headers = ['Name', 'Job Title', 'Company', 'Location', 'Job Description']
        results = []
        for searched_result in search_results:
            result_tuple = (("{} {}".format(searched_result.first_name, searched_result.last_name)),
                            searched_result.title_0,
                            searched_result.companyName_0, searched_result.metro, searched_result.summary_0)
            results.append(result_tuple)
        if results:

            return render_template('results.html', success='True', headers=headers, results=results)
        else:
            return render_template('search.html', success='False')


@app_run.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app_run.route('/profiles', methods=['GET'])
@login_required
def list():
    if current_user.user_type == 'admin':
        return render_template("list.html", rows=LinkedInRecord.query.all())
    else:
        return render_template("list.html", rows=[LinkedInRecord.query.filter_by(member_id=cur.member_id).first() for
                                                  cur in current_user.records])


@app_run.route('/fetch', methods=['GET'])
@login_required
def fetch_user_caches_view():
    user = User.query.filter_by(id=current_user.id).first()
    users_caches = user.caches
    user_files = []
    for uc in users_caches:
        # Get count just once, expensive. If 0, skip it
        uc_count = len(uc.profiles)
        if uc_count == 0:
            # Remove files with 0 records that aren't from today
            if uc.created.date() != date.today():
                continue
        td = (uc.cache_id, uc.friendly_id, uc_count, uc.created)
        user_files.append(td)
    user_files = sorted(user_files, key=itemgetter(3))

    return render_template('cache_list.html', user_files=user_files)


@app_run.route('/download/<cache_id>', methods=['GET'])
@login_required
def serve_file(cache_id):

    current_user_id = current_user.id

    # Find User with this ID
    user = User.query.filter_by(id=current_user_id).first()

    if user is None or user is False:
        abort(400)
    user_caches = user.caches
    user_caches_ids = [uc.cache_id for uc in user_caches]
    if cache_id not in user_caches_ids:
        abort(400)
    fetched_cache = UserCache.query.filter_by(cache_id=cache_id).first()
    if fetched_cache.friendly_id:
        cache_file_name = fetched_cache.friendly_id
    else:
        cache_file_name = fetched_cache.cache_id
    cached_data = fetched_cache.profiles
    data = []

    def row2dict(row):
        d = {}
        for column in row.__table__.columns:
            if column.name[0] == '_':
                continue
            row_val = str(getattr(row, column.name))
            if row_val is None or row_val == 'None':
                row_val = ''
            d[column.name] = row_val
        return d

    for prof in cached_data:
        data.append(row2dict(prof))

    csv_text = csv_parser.db_to_csv(data)
    return Response(csv_text, mimetype="text/csv",
                    headers={"Content-disposition": "attachment; filename={}.csv".format(cache_file_name)})

@app_run.route('/manage/files', methods=['GET'])
@login_required
def file_manager():
    user = User.query.filter_by(id=current_user.id).first()
    users_caches = user.caches
    user_files = []
    for uc in users_caches:
        # Get count just once, expensive. If 0, skip it
        uc_count = len(uc.profiles)
        if uc_count == 0:
            # Remove files with 0 records that aren't from today
            if uc.created.date() != date.today():
                continue
        td = (uc.cache_id, uc.friendly_id, uc_count, uc.created)
        user_files.append(td)
    user_files = sorted(user_files, key=itemgetter(3))

    return render_template('file_manager.html', user_files=user_files, code=request.args.get('code'))

@app_run.route('/manage/files/rename', methods=['POST'])
@login_required
def file_rename():
    user = User.query.filter_by(id=current_user.id).first()
    file_name = request.form.get('file_name')
    file_new_name = request.form.get('new_name')
    for char in string.punctuation:
        if char in file_new_name:
            return redirect(url_for('file_manager', code="error"))

    # Locate the file referenced
    user_file = UserCache.query.join(User).filter(User.id == user.id).filter(UserCache.cache_id == file_name).first()
    if user_file:
        pass
    else:
        user_file = UserCache.query.join(User).filter(User.id == user.id).filter(UserCache.friendly_id == file_name).first()
        if user_file:
            pass
        else:
            return redirect(url_for('file_manager', code="error"))

    user_file.friendly_id = file_new_name
    db.session.add(user_file)
    db.session.commit()
    return redirect(url_for('file_manager', code="success"))

@app_run.route('/api/v1/token', methods=['POST'])
def get_auth_token():

    user = load_user_from_request(request)
    if user:
        token = update_user_token(user)
        return jsonify({'token': token.decode('ascii')})
    else:
        print("User not found from token")
        return abort(401)



@app_run.route('/api/v1/test_token', methods=['GET'])
@requires_key
def t():
    return jsonify({'message': 'valid token'})


@app_run.route('/api/v1/profiles', methods=['POST'])
@requires_key
def profile():

    if not request.json:
        abort(400)
        print("Request not JSON")

    data = request.json
    parsed_data = profile_parser.LinkedInProfile(data)
    profile_record = LinkedInRecord(parsed_data)

    # Get user id to associate to the record
    user_from_api = load_user_from_request(request)
    user_id = user_from_api.id
    print("New record from {}".format(user_id))

    # Check if record already exists

    matched_records = LinkedInRecord.query.filter_by(member_id=profile_record.member_id).first()

    if matched_records:
        print("Handled update")
        profile_record = handle_update(profile_record)

    # Done with record, add it to session
    db.session.add(profile_record)

    # Create association with record and User
    user_from_api.records.append(profile_record)

    # Get the cache referred to in token
    api_key = request.headers.get('Api-Key')
    user_current_cache_id = User.current_cache_from_token(api_key)
    user_current_cache = user_from_api.caches.filter(UserCache.cache_id == user_current_cache_id).first()

    # Create association with the record and Cache
    user_current_cache.profiles.append(profile_record)

    # Cache is modified add it to session
    db.session.add(user_current_cache)
    db.session.commit()
    # Form to JSON and reply with it

    return jsonify({'action': 'success'}), 201


@app_run.route('/api/v1/prune', methods=['POST'])
@requires_key
def prune():
    data = request.json['data']

    profile_pruner = csv_parser.ProfilePruner(data)
    pruned_urls = []

    def prune_record(lookup_result):
        created_date = lookup_result.created
        if created_date is None:
            return True  # incomplete record, get it
        if (date.today() - created_date).days >= profile_pruner.RECORD_IS_OLD:
            return True  # old record, get it
        else:
            return False  # don't get it

    for k, v in profile_pruner.reference.items():
        member_id = v['member_id']
        print("Searching for {}".format(member_id))
        lookup_result = LinkedInRecord.query.filter_by(member_id=member_id).first()
        print("Found {}".format(lookup_result))
        if lookup_result:
            if prune_record(lookup_result) is False:
                print("We have {} in database".format(lookup_result))
                # We don't want to fetch it
                # But we want to create association
                user_from_api = load_user_from_request(request)
                api_key = request.headers.get('Api-Key')
                user_current_cache_id = User.current_cache_from_token(api_key)
                print("Users cache_id from token is {}".format(user_current_cache_id))
                user_current_cache = user_from_api.caches.filter(UserCache.cache_id == user_current_cache_id).first()
                print("Found this cache {}".format(user_current_cache))

                # Create association with the record and Cache
                user_current_cache.profiles.append(lookup_result)

                # Cache is modified, add it to session
                db.session.add(user_current_cache)
                db.session.commit()

                # Remove the url from the response
                profile_pruner.reference[k] = False

    for k, v in profile_pruner.reference.items():
        if v:
            pruned_urls.append(v['clean_url'])

    return jsonify({'data': pruned_urls}), 201


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


def handle_update(profile_record):

    # Fetch the record that is a duplicate

    old_record = LinkedInRecord.query.filter_by(member_id=profile_record.member_id).first()

    record_keys = profile_record.__dict__.keys()
    for key in record_keys:
        if key[0] == '_' or key == 'updated':  # These will never be equal, internal key
            continue
        try:
            old_value = getattr(old_record, key)
            new_value = getattr(profile_record, key)
        except AttributeError as e:
            print(e)
            continue
        if old_value != new_value:
            setattr(old_record, key, new_value)

    old_record.updated = date.today()
    return old_record
