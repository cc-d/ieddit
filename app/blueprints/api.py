from ieddit import *
from jinja2 import escape
import json

bp = Blueprint('api', 'api', url_prefix='/api')

def require_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = db.session.query(Api_key).filter_by(username=normalize_username(request.headers['ieddit-username']),
            key=request.headers['ieddit-api-key']).first()

        if key is not None:
            #session['username'] = key.username
            #session['user_id'] = (db.session.query(Iuser).filter_by(username=key.username).first())
            return f(*args, **kwargs)

        return 'verify args failed'

    return decorated_function


# single post
@bp.route('/get_post/<post_id>/', methods=['GET'])
def get_post(post_id=None):
    return sqla_to_json((db.session.query(Post).filter_by(id=post_id).first()))


# multiple posts comma seperated, example /1,2,3,4,5/
@bp.route('/get_posts/<post_ids>/', methods=['GET'])
def get_posts(post_ids=None):
    post_ids = post_ids.split(',')
    r = []

    for pid in post_ids:
        try:
            int(pid)
        except:
            continue
        post = db.session.query(Post).filter_by(id=pid).first()
        print(post)
        if post != None:
            r.append(as_dict(post))

    return json.dumps(r)

# single comment
@bp.route('/get_comment/<comment_id>/', methods=['GET'])
def get_comment(comment_id=None):
    return sqla_to_json((db.session.query(Comment).filter_by(id=comment_id).first()))


# multiple comments comma seperated, example /1,2,3,4,5/
@bp.route('/get_comments/<comment_ids>/', methods=['GET'])
def get_comments(comment_ids=None):
    comment_ids = comment_ids.split(',')
    r = []

    for pid in comment_ids:
        try:
            int(pid)
        except:
            continue
        comment = db.session.query(Comment).filter_by(id=pid).first()
        print(comment)
        if comment != None:
            r.append(as_dict(comment))

    return json.dumps(r)


#r = requests.post('http://dev.ieddit.com/api/new_comment', data={text='comment text', post_id=1)
@bp.route('/new_comment', methods=['POST'])
@require_key
def new_comment():
    """
    Create a new comment through api, same post data as main
    """
    text = request.form.get('text')
    parent_id = request.form.get('parent_id')
    parent_type = request.form.get('parent_type')

    anonymous = request.form.get('anonymous')
    override = request.form.get('override')

    return str(create_comment(api=True, text=text, parent_id=parent_id, parent_type=parent_type,
                            override=override, anonymous=anonymous))


@bp.route('/new_post', methods=['POST'])
@require_key
def new_post():
    """
    Create a new post through api, same post data as main
    """
    title = request.form.get('title')
    url = request.form.get('url')
    sub = request.form.get('sub')
    self_post_text = request.form.get('self_post_text')

    return str(create_post(api=True, title=title, url=url, sub=sub, self_post_text=self_post_text))


# single sub
@bp.route('/get_sub/<sub_name>/', methods=['GET'])
def get_sub(sub_name=None):
    return sqla_to_json((db.session.query(Sub).filter_by(name=sub_name).first()))

# multiple subs comma seperated, example /1,2,3,4,5/
@bp.route('/get_subs/<sub_names>/', methods=['GET'])
def get_subs(sub_names=None):
    sub_names = sub_names.split(',')
    r = []

    for name in sub_names:
        sub = db.session.query(Sub).filter_by(name=name).first()
        print(sub)
        if sub != None:
            r.append(as_dict(sub))

    return json.dumps(r)

@bp.route("/get_user/<username>/", methods=["GET"])
def get_user(username=None):
    return {
        "meta": sqla_to_dict((db.session.query(Iuser).filter_by(username=username).first()), expunge=["email", "password"]),
        "posts": [sqla_to_dict(post) for post in (db.session.query(Post).filter_by(author=username))]
    }
