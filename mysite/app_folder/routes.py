import base64
from datetime import date, timedelta
from functools import wraps
from operator import itemgetter

from flask import render_template, redirect, url_for, request, abort, jsonify, send_file
from flask_login import login_user, current_user, logout_user, login_required
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer)

from app_folder import app_run, db, login, csv_parser, profile_parser, request_pruner
from app_folder.models import User, LinkedInRecord, UserCache, UserActivity


def requires_key(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        api_key = request.headers.get('Api-Key', False)
        if api_key is False:
            abort(400)
        if User.verify_auth_token(api_key) is False:
            abort(401)
        elif User.verify_auth_token(api_key) is None:
            abort(401)
        else:
            return func(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapped


def generate_auth_token(user_id, session_number, expiration=86400):
    s = Serializer(app_run.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id': user_id, 'session': session_number})


def update_user_token(user):
    current_session = user.current_session_user
    new_session = current_session + 1
    # Increment session number
    user.current_session_user = new_session
    user_id_ = user.id
    auth_token = generate_auth_token(user_id_, new_session)
    user.api_key = auth_token
    db.session.add(user)
    db.session.commit()
    return user.api_key


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


@app_run.route('/')
def index():
    return render_template('layout.html', media='True')


@app_run.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login_page.html", error=False)

    user = User.query.filter_by(username=request.form['username']).first()
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
# TODO Pagination
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
        if uc.active is True:
            is_active = 'Yes'
        else:
            is_active = 'No'
        uc_count = len(uc.profiles)
        td = (uc.cache_id, uc.friendly_id, uc_count, uc.created, is_active)
        user_files.append(td)
    user_files = sorted(user_files, key=itemgetter(4, 3), reverse=True)

    return render_template('cache_list.html', user_files=user_files, code=request.args.get('code'))


@app_run.route('/download/<cache_id>', methods=['GET'])
@login_required
def serve_file(cache_id):

    current_user_id = current_user.id

    # Find User with this ID
    user = User.query.filter_by(id=current_user_id).first()

    if user is None or user is False:
        abort(401)
    user_caches = user.caches
    user_caches_ids = [uc.cache_id for uc in user_caches]
    if cache_id not in user_caches_ids:
        abort(404)
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

    xlsx_stream = csv_parser.db_to_excel(data)
    if xlsx_stream:
        return send_file(xlsx_stream, attachment_filename="{}.xlsx".format(cache_file_name), as_attachment=True)
    else:
        return "Error"


@app_run.route('/manage/files/<category>', methods=['GET'])
@login_required
def file_manager(category):

    # Displays the requested file action

    user = User.query.filter_by(id=current_user.id).first()
    users_caches = user.caches
    user_files = []
    for uc in users_caches:
        # Get count just once, expensive. If 0, skip it
        uc_count = len(uc.profiles)
        if uc_count == 0:
            # Remove files with 0 records that aren't from today
            if uc.created.date() != date.today():
                if uc.active is False:
                    continue
        td = (uc.cache_id, uc.friendly_id, uc_count, uc.created)
        user_files.append(td)
    user_files = sorted(user_files, key=itemgetter(3))

    return render_template('file_manager.html', user_files=user_files, category=category,
                           code=request.args.get('code'))


@app_run.route('/manage/files/<category>/do', methods=['POST'])
@login_required
def file_manager_do(category):

    if category == 'rename':

        user = User.query.filter_by(id=current_user.id).first()
        file_name = request.form.get('file_name')
        file_new_name = request.form.get('new_name')

        allowchar = [' ', '_']
        file_new_name = "".join([c for c in file_new_name if c.isalnum() or c in allowchar]).rstrip()

        # Locate the file referenced
        user_file = UserCache.query.join(User).filter(User.id == user.id).filter(UserCache.cache_id == file_name).first()
        if user_file:
            pass
        else:
            user_file = UserCache.query.join(User).filter(User.id == user.id).filter(
                UserCache.friendly_id == file_name).first()
            if user_file:
                pass
            else:
                return redirect(url_for('file_manager', category='rename', code="error_rename"))

        user_file.friendly_id = file_new_name
        db.session.add(user_file)
        db.session.commit()
        return redirect(url_for('file_manager', category='rename', code="success_rename"))

    elif category == 'new':

        user = User.query.filter_by(id=current_user.id).first()
        file_new_name = request.form.get('new_name')

        allowchar = [' ', '_']
        file_new_name = "".join([c for c in file_new_name if c.isalnum() or c in allowchar]).rstrip()

        # Find any active caches set them inactive
        active_files = UserCache.query.join(User).filter(User.id == user.id).filter(
            UserCache.active == True).all()

        for ac in active_files:
            ac.active = False
            db.session.add(ac)

        # Create new file
        new_file = UserCache()
        new_file.friendly_id = file_new_name
        new_file.active = True
        user.caches.append(new_file)

        db.session.add(user)
        db.session.add(new_file)
        db.session.commit()
        return redirect(url_for('file_manager', category='new', code="success_new"))

    elif category == 'set_active':

        user = User.query.filter_by(id=current_user.id).first()
        file_name = request.form.get('file_name')

        # Find the cache referenced
        target_file = UserCache.query.join(User).filter(User.id == user.id).filter(
            UserCache.cache_id == file_name).first()
        if target_file:
            pass
        else:
            target_file = UserCache.query.join(User).filter(User.id == user.id).filter(
                UserCache.friendly_id == file_name).first()
            if target_file:
                pass
            else:
                return redirect(url_for('file_manager', category='set_active', code="error_set"))

        # Find active caches

        active_files = UserCache.query.join(User).filter(User.id == user.id).filter(
            UserCache.active == True).all()

        for ac in active_files:
            ac.active = False
            db.session.add(ac)
            db.session.commit()

        target_file.active = True
        db.session.add(target_file)
        db.session.commit()
        return redirect(url_for('file_manager', category='set_active', code="success_set"))


@app_run.route('/manage/files/delete/<cache_id>')
@login_required
def delete_cache(cache_id):

    user = User.query.filter_by(id=current_user.id).first()
    target_file = UserCache.query.join(User).filter(User.id == user.id).filter(
        UserCache.cache_id == cache_id).first()
    if target_file:
        pass
    else:
        return redirect(url_for('fetch_user_caches_view', code="error_delete"))

    db.session.delete(target_file)
    db.session.commit()

    return redirect(url_for('fetch_user_caches_view', code="success_delete"))


# TODO User Deletes File

@app_run.route('/manage/self/<category>', methods=['GET', 'POST'])
@login_required
def manage_self(category):
    user = User.query.filter_by(id=current_user.id).first()

    if category == 'activity':
        user_activities = user.activities.all()
        user_act_show = []
        for ua in user_activities:
            ua_new = ua.new_records
            ua_borrow = ua.borrowed_records
            ua_created = ua.created
            ua_active = ua.active
            if ua_active:
                ua_active = "Yes"
            else:
                ua_active = "No"
            if ua_new >= 450:
                ua_warn = "Yes"
            else:
                ua_warn = "No"
            if ua_borrow == 0 and ua_new == 0 and ua_active == 'No':
                continue
            td = (ua_created, ua_new, ua_borrow, ua_active, ua_warn)
            user_act_show.append(td)
        user_act_show = sorted(user_act_show, key=itemgetter(0))

        return render_template('user_manager.html', user_info=user_act_show,
                               category=category, code=request.args.get('code'))

# Displays the requested file action

    elif category == 'password':

        if request.method == 'GET':
            return render_template('user_manager.html', category=category, code=request.args.get('code'))

        elif request.method == 'POST':
            old = request.form.get('old_password')
            correct_old = user.check_password(old)
            if correct_old is False:
                return render_template('user_manager.html', category=category, code='error_wrong')

            new1 = request.form.get('new_password1')
            new2 = request.form.get('new_password2')

            if new1 != new2:
                return render_template('user_manager.html', category=category, code='error_confirm')

            if len(new1) == 0:
                return render_template('user_manager.html', category=category, code='error_no_password')

            user.generate_new_password(new1)
            db.session.commit()

            return render_template('user_manager.html', category=category, code='success')

@app_run.route('/resumes/<member_id>')
@login_required
def show_resume(member_id):
    member_id = int(member_id)
    member = LinkedInRecord.query.filter_by(member_id=member_id).first()
    if not member_id:
        return render_template('open_resume.html', code='error')

    # build dict for template
    data = {}
    data['first_name'] = member.first_name
    data['last_name'] = member.last_name
    data['title_0'] = member.title_0
    data['metro'] = member.metro
    data['postal_code'] = member.postal_code
    data['country_code'] = member.country_code.upper()
    data['public_url'] = member.public_url
    data['summary'] = member.summary
    data['skills'] = member.skills.split(', ')
    data['work_history'], data['job_count'] = build_work_history(member)

    return render_template('open_resume.html', code='success', data=data)

def build_work_history(member):
    history = []

    for i in range(3):
        companyName = 'companyName_{}'.format(i)
        title = 'title_{}'.format(i)
        start_date = 'start_date_{}'.format(i)
        end_date = 'end_date_{}'.format(i)
        summary = 'summary_{}'.format(i)

        td = {}
        td['title'] = getattr(member, title)
        td['companyName'] = getattr(member, companyName)
        try:
            td['start_date'] = getattr(member, start_date).strftime('%b %Y')
        except AttributeError:
            td['start_date'] = None
        end_date_data = getattr(member, end_date)
        if not end_date_data:
            td['end_date'] = 'Present'
        else:
            try:
                td['end_date'] = getattr(member, end_date).strftime('%b %Y')
            except AttributeError:
                td['end_date'] = None
        td['summary'] = getattr(member, summary)

        if not any(td.values()):  # If nothing would be included
            continue
        else:
            td['index'] = i
        history.append(td)
    return history, len(history)




@app_run.route('/api/v1/token', methods=['POST'])
def get_auth_token():

    user = load_user_from_request(request)
    if user:
        token = update_user_token(user)
        if isinstance(token, str):
            return jsonify({'token': token})
        elif isinstance(token, bytes):
            return jsonify({'token': token.decode('ascii')})
    else:
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

    data = request.json
    parsed_data = profile_parser.LinkedInProfile(data)
    profile_record = LinkedInRecord(parsed_data)

    # Get user id to associate to the record
    user_from_api = load_user_from_request(request)
    user_id = user_from_api.id

    # Check if record already exists

    matched_records = LinkedInRecord.query.filter_by(member_id=profile_record.member_id).first()

    if matched_records:
        profile_record = handle_update(profile_record)

    # Done with record, add it to session
    db.session.add(profile_record)

    # Create association with record and User
    user_from_api.records.append(profile_record)
    db.session.add(user_from_api)


    # Tally 1 to user activity
    activity_tracker = user_from_api.get_activity()
    if activity_tracker:
        new_count = activity_tracker.new_records + 1
        activity_tracker.new_records = new_count
        db.session.add(activity_tracker)
        db.session.add(user_from_api)

    # get_activity() returns False if no Active AND less than 1 day old found
    else:
        activity_tracker = UserActivity(new_records=1, active=True)
        user_from_api.activities.append(activity_tracker)
        db.session.add(user_from_api)


    # Get the user's active cache
    active_cache = UserCache.query.join(User).filter(User.id == user_from_api.id).filter(
            UserCache.active == True).first()

    # If no active, create new and set to active
    if active_cache:
        pass
    else:
        active_cache = UserCache()
        active_cache.active = True
        user_from_api.caches.append(active_cache)
        # User has new cache, add to session
        db.session.add(user_from_api)

    # Create association with the record and Cache
    active_cache.profiles.append(profile_record)

    # Cache is modified add it to session
    db.session.add(active_cache)

    db.session.commit()
    # Form to JSON and reply with it

    if activity_tracker.new_records >= user_from_api.allowance:
        return jsonify({'action': 'exceeded limit'}), 429

    return jsonify({'action': 'success'}), 201


@app_run.route('/api/v1/prune', methods=['POST'])
@requires_key
def prune():
    data = request.json['data']

    profile_pruner = request_pruner.ProfilePruner(data)
    pruned_urls = []
    user_from_api = load_user_from_request(request)

    active_cache = UserCache.query.join(User).filter(User.id == user_from_api.id).filter(
        UserCache.active == True).first()

    # If no active, create new and set to active
    if active_cache:
        pass
    else:
        active_cache = UserCache()
        active_cache.active = True
        user_from_api.caches.append(active_cache)
        # User has new cache, add to session
        db.session.add(user_from_api)
        db.session.commit()

    activity_tracker = user_from_api.get_activity()
    if activity_tracker:
        pass

    # get_activity() returns False if no Active AND less than 1 day old found
    else:
        activity_tracker = UserActivity(new_records=1, active=True)
        user_from_api.activities.append(activity_tracker)
        db.session.add(user_from_api)
        db.session.add(activity_tracker)
        db.session.commit()

    def prune_record(lookup_result):
        created_date = lookup_result.created
        if created_date is None:
            return True  # incomplete record, get it
        if (date.today() - created_date).days >= profile_pruner.RECORD_IS_OLD:
            return True  # old record, get it
        else:
            return False  # don't get it

    append_to_cache_bin = []

    for k, v in profile_pruner.reference.items():
        member_id = v['member_id']
        lookup_result = LinkedInRecord.query.filter_by(member_id=member_id).first()
        if lookup_result:
            if prune_record(lookup_result) is False:
                # We don't want to fetch it
                # But we want to create association
                # Get the user's active cache
                # Create association with the record and Cache
                append_to_cache_bin.append(lookup_result)

                # Remove the url from the response
                profile_pruner.reference[k] = False

    for k, v in profile_pruner.reference.items():
        if v:
            pruned_urls.append(v['clean_url'])

    if append_to_cache_bin:
        for lr in append_to_cache_bin:
            active_cache.profiles.append(lr)
            new_count = activity_tracker.borrowed_records + 1
            activity_tracker.borrowed_records = new_count
        db.session.add(activity_tracker)
        db.session.add(active_cache)
        db.session.commit()
    return jsonify({'data': pruned_urls, 'active_id': active_cache.cache_id, 'active_name': active_cache.friendly_id})\
        , 201


@app_run.route('/api/v1/activity', methods=['GET'])
@requires_key
def activity():
    user = load_user_from_request(request)
    if user:
        pass
    else:
        return abort(401)

    # Get the active cache for the user
    active_cache = UserCache.query.join(User).filter(User.id == user.id).filter(
        UserCache.active == True).first()

    # If no active cache, message should indicate

    if active_cache:
        ac_filename = active_cache.friendly_id
        if ac_filename:
            pass
        else:
            ac_filename = active_cache.cache_id
    else:
        ac_filename = 'No Active File'

    # Get the active activity record for user
    activity_tracker = user.get_activity()
    if activity_tracker is False:  # Retrieve stats
        activity_tracker = UserActivity(active=True)
        user.activities.append(activity_tracker)
        db.session.add(user)
        db.session.commit()

    # Calculate when allowance is reset (created + 1 day)
    allowance_reset = (activity_tracker.created + timedelta(1)).isoformat()

    # Handle User Allowance
    if user.allowance:
        user_allowance = user.allowance
        if user.allowance < activity_tracker.new_records:
            allowance_remaining = 0
        else:
            allowance_remaining = user.allowance - activity_tracker.new_records
    else:
        user_allowance = 450
        allowance_remaining = 450 - activity_tracker.new_records

    activity_values = {'start': activity_tracker.created, 'new': activity_tracker.new_records,
                       'borrow': activity_tracker.borrowed_records, 'allowance': user_allowance, 'allowance_remain':
                           allowance_remaining, 'allowance_reset': allowance_reset, 'active_file': ac_filename}

    return jsonify({'activity': activity_values}), 200


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
