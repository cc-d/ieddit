from flask import abort, make_response
from share import *
import json
from functools import wraps
from utilities.error_decorator import exception_log
from html import escape

# Logging Initialization
import logging 
logger = logging.getLogger(__name__)

abp = Blueprint('admin', 'admin', url_prefix='/admin')

@abp.route('/stats/', methods=['GET'])
@cache.memoize(config.DEFAULT_CACHE_TIME)
def show_admin_stats():
    """
    returns json string of every admin action for display
    """
    j = {}
    j['site_banned'] = [sqla_to_dict(x) for x in db.session.query(Iuser).filter_by(banned=True).all()]
    j['muted_subs'] = [sqla_to_dict(x) for x in db.session.query(Sub).filter_by(muted=True).all()]
    j['api_key_users'] = [x.username for x in db.session.query(Api_key).all()]

    j = str(json.dumps(j))

    r = make_response(j)
    r.mimetype = 'application/json'
    return r


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            logger.critical("Unauthorized User Attempted to Access Admin Utilities")
            return abort(403)
        if 'username' not in session:
            logger.critical("Unauthorized User Attempted to Access Admin Utilities")
            return abort(403)
        admins = db.session.query(Iuser).filter_by(admin=True).all()
        anames = [a.username for a in admins]
        if session['username'] not in anames:
            logger.critical("Unauthorized User Attempted to Access Admin Utilities")
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@abp.route('/',  methods=['GET'])
@admin_only
def admincp():
    keys = db.session.query(Api_key).all()
    muted_subs = db.session.query(Sub).filter_by(muted=True).all()
    return render_template('admin.html', keys=keys, muted_subs=muted_subs)

@abp.route('/add_sub_mute', methods=['POST'])
@admin_only
def add_sub_mute():
    sub = request.form.get('sub')
    sub = db.session.query(Sub).filter_by(name=normalize_sub(sub)).first()
    if sub.muted == False:
        sub.muted = True
        db.session.add(sub)
        db.session.commit()
    return redirect('/admin/')

@abp.route('/remove_sub_mute', methods=['POST'])
@admin_only
def remove_sub_mute():
    sub = request.form.get('sub')
    sub = db.session.query(Sub).filter_by(name=normalize_sub(sub)).first()
    if sub.muted == True:
        sub.muted = False
        db.session.add(sub)
        db.session.commit()
    return redirect('/admin/')

@abp.route('/add_api_key', methods=['POST'])
@admin_only
def add_api_key():
    user = request.form.get('username')
    user = normalize_username(user, dbuser=True)
    if user:
        keys = db.session.query(Api_key).all()
        for k in keys:
            if k.username == user.username:
                return 'already has key'
        new_key = Api_key(username=user.username, key=rstring(30))
        db.session.add(new_key)
        db.session.commit()
        return redirect('/admin/')
    else:
        return 'no user'

@abp.route('/remove_api_key', methods=['POST'])
@admin_only
def del_api_key():
    user = request.form.get('username')
    user = normalize_username(user, dbuser=True)
    if user:
        key = db.session.query(Api_key).filter_by(username=user.username).first()
        db.session.delete(key)
        db.session.commit()
        return redirect('/admin/')
    else:
        return 'no user'

@abp.route('/ban_and_delete', methods=['POST'])
@admin_only
def ban_and_delete():
    post_id = request.form.get('post_id')
    comment_id = request.form.get('comment_id')
    print(post_id, comment_id)
    if post_id != None:
        username = db.session.query(Post).filter_by(id=post_id).first()
        username = username.author
    elif comment_id != None:
        username = db.session.query(Post).filter_by(id=post_id).first()
        username = username.author
    else:
        username = request.form.get('username')
        username = normalize_username(username)

    posts = db.session.query(Post).filter_by(author=username).all()
    posts = [p for p in posts]

    comments = db.session.query(Comment).filter_by(author=username).all()
    comments = [c for c in comments]

    user = db.session.query(Iuser).filter_by(username=username).first()

    for p in posts:
        p.deleted = True
        db.session.add(p)
    for c in comments:
        c.deleted = True
        db.session.add(c)
    user.banned = True
    db.session.add(user)

    db.session.commit()
    flash('banned and deleted %s' % user.username, 'success')

    return redirect('/admin/')







