from ieddit import *
from jinja2 import escape
import json

bp = Blueprint('api', 'api', url_prefix='/api')

def require_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = db.session.query(Api_key).filter_by(username=normalize_username(request.headers['ieddit-username']),
            key=request.headers['ieddit-api-key']).first()
        if key != None:
            return f(*args, **kwargs)
        else:
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
    text = request.form.get('comment_text')
    post_id = request.form.get('post_id')
    parent_id = request.form.get('parent_id')
    anonymous = request.form.get('anonymous')

    post_obj = db.session.query(Post).filter_by(id=post_id).first()

    sub_name = post_obj.sub

    if anonymous != None:
        anonymous = True
    else:
        anonymous = False

    if parent_id == '':
        parent_id = None

    print(text, post_id, sub_name)
    if text == None or post_id == None or sub_name == None:
        return json.dumps({'error': 'bad comment'})

    if parent_id != None:
        level = (db.session.query(Comment).filter_by(
            id=parent_id).first().level) + 1
    else:
        level = None

    post = db.session.query(Post).filter_by(id=post_id).first()
    if post.locked == True:
        return json.dumps({'error': 'post is locked'})

    author_id = get_user_from_name(request.headers['ieddit-username']).id

    new_comment = Comment(post_id=post_id, sub_name=sub_name, text=text,
              author=request.headers['ieddit-username'], author_id=author_id,
              parent_id=parent_id, level=level, anonymous=anonymous)

    db.session.add(new_comment)
    db.session.commit()

    new_comment.permalink = config.URL + '/i/' + new_post.sub + '/' + str(new_post.id) + '/' + new_post.inurl_title + '/' + str(new_comment.id) + '/'
    db.session.commit()

    new_vote = Vote(comment_id=new_comment.id, vote=1,
                    user_id=author_id, post_id=None)
    db.session.add(new_vote)

    new_comment.ups += 1
    db.session.add(new_comment)
    db.session.commit()

    return sqla_to_json(new_comment)

@bp.route('/new_post', methods=['POST'])
@require_key
def new_post():
    anonymous = request.form.get('anonymous')
    self_text = request.form.get('self_text')
    sub = request.form.get('sub')
    title = request.form.get('title')
    url = request.form.get('url')

    sub = db.session.query(Sub).filter_by(name=normalize_sub(sub)).first()

    if sub.nsfw:
        nsfw = True
    else:
        nsfw = False

    sub = sub.name

    if anonymous != None:
        anonymous = True
    else:
        anonymous = False

    if self_text != None:
        post_type = 'self_post'
    elif url != None:
        post_type = 'url'
    else:
        return json.dumps({'error':'invalid post type, not url or self'})

    if title == None:
        json.dumps({'error':'invalid post, no title'})
    if len(title) > 400 or len(title) < 1 or len(sub) > 30 or len(sub) < 1:
        json.dumps({'error':'invalid title/sub length'})

    if sub == None or title == None or post_type == None:
        return json.dumps({'error': 'bad post'})

    author_id = get_user_from_name(request.headers['ieddit-username']).id

    new_post = Post(post_type=post_type, anonymous=anonymous,
                    self_text=self_text, sub=sub,
                    title=title, url=url, inurl_title=convert_ied(title), author=request.headers['ieddit-username'],
                    author_id=author_id)

    db.session.add(new_post)
    db.session.commit()

    new_post.permalink = config.URL + '/i/' + new_post.sub + '/' + str(new_post.id) + '/' + new_post.inurl_title + '/'
    post_id = new_post.id
    new_vote = Vote(vote=1, user_id=author_id, post_id=post_id)
    db.session.add(new_vote)

    new_post.ups += 1
    db.session.add(new_post)
    db.session.commit()

    return sqla_to_json(new_post)

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
