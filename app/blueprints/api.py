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
            return f(*args, **kwargs)

        return 'verify args failed'

    return decorated_function

@bp.after_request
def set_json_type(response):
    response.headers['content-type'] = 'application/json'
    return response

# single post
def api_single_post(post_id=None):
    post = db.session.query(Post).filter_by(id=post_id, deleted=False).first()
    comments = db.session.query(Comment).filter_by(post_id=post_id, deleted=False).all()

    post.comments = [sqla_to_dict(c) for c in comments]

    return sqla_to_json(post, include_attrs=['comments'])


# multiple posts comma seperated, example /1,2,3,4,5/
def api_multiple_posts(post_ids=None):
    post_ids = post_ids.split(',')
    json_posts = []

    for pid in post_ids:
        post = db.session.query(Post).filter_by(id=pid, deleted=False).first()

        if post is not None:
            comments = db.session.query(Comment).filter_by(post_id=post.id, deleted=False).all()
            if comments is not None:
                post.comments = [sqla_to_dict(c) for c in comments]

            json_posts.append(sqla_to_dict(post, include_attrs=['comments']))

    return pretty_json(json_posts)

@bp.route('/get_post/<post_ids>/', methods=['GET'])
def get_post(post_ids=None):
    if post_ids.find(',') != -1:
        return api_multiple_posts(post_ids=post_ids)
    return api_single_post(post_id=post_ids)

# single comment
def api_single_comment(comment_id=None):
    return sqla_to_json((db.session.query(Comment).filter_by(id=comment_id, deleted=False).first()))

# multiple comments comma seperated, example /1,2,3,4,5/
def api_multiple_comments(comment_ids=None):
    comment_ids = comment_ids.split(',')
    return_json = []

    for pid in comment_ids:
        comment = db.session.query(Comment).filter_by(id=pid, deleted=False).first()

        if comment != None:
            return_json.append(sqla_to_dict(comment))

    return pretty_json(return_json)

@bp.route('/get_comment/<comment_ids>/', methods=['GET'])
def get_comment(comment_ids=None):
    if comment_ids.find(',') != -1:
        return api_multiple_comments(comment_ids=comment_ids)
    return api_single_comment(comment_id=comment_ids)

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

    return pretty_json(create_comment(api=True, text=text, parent_id=parent_id, parent_type=parent_type,
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

    return pretty_json(create_post(api=True, title=title, url=url, sub=sub, self_post_text=self_post_text))


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
            r.append(sqla_to_dict(sub))

    return pretty_json(r)

@bp.route('/get_user/<username>/', methods=['GET'])
def get_user(username=None):
    """
    gets information about a user
    """
    user = sqla_to_dict((db.session.query(Iuser).filter_by(username=username).first()), expunge=['email', 'password'])
    user['posts'] = [sqla_to_dict(post) for post in (db.session.query(Post).filter_by(author=username, anonymous=False, deleted=False))]
    user['comments'] = [sqla_to_dict(comment) for comment in (db.session.query(Comment).filter_by(author=username, anonymous=False, deleted=False))]
    return pretty_json(user)

@bp.route('/get_sub_<itype>/<sub>/', methods=['GET'])
@bp.route('/get_sub_<itype>/<sub>/', methods=['GET'])
def get_sub_posts(sub=None, itype=None):
    """
    returns the posts for a given sub
    """
    sub = normalize_sub(sub)

    offset = request.args.get('offset')
    if offset is None:
        offset = 0
    else:
        offset = int(offset)

    limit = request.args.get('limit')
    if limit is None:
        limit = 15
    else:
        limit = int(limit)

    sort = request.args.get('sort')
    if sort is None:
        sort = 'hot'

    if itype == 'comments':
        return subcomments(sub, offset=offset, limit=limit, s=sort, api=True)
    return get_subi(sub, offset=offset, limit=limit, s=sort, api=True)

