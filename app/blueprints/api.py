from ieddit import *
from jinja2 import escape
import json

bp = Blueprint('api', 'api', url_prefix='/api')


def verify_api_key(username, key):
	key = db.session.query(Api_key).filter_by(
	username=normalize_username(username), key=key).first()
	if key == None:
		return False
		return True

# require auth


def require_key(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		try:
			verified = verify_api_key(request.headers['username'], request.headers['api_key'])
			if verified == True:
				return f(*args, **kwargs)
			else:
				return 'verify args failed'
		except Exception as e:
			print(e)
			return json.dumps({'error':str(e)})

	return decorated_function

# convert to dict


def as_dict(obj):
	obj = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
	if obj['created']:
		obj['created'] = obj['created'].isoformat()
	return obj

# convert to obj and then pretty print


def jcon(obj):
	return json.dumps(as_dict(obj), sort_keys=True, indent=4, separators=(',', ': '))

# just a pretty print function


def pjson(obj):
	return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))

# single post
@bp.route('/get_post/<post_id>/', methods=['GET'])
@require_key
def get_post(post_id=None):
	return jcon((db.session.query(Post).filter_by(id=post_id).first()))

# multiple posts comma seperated, example /1,2,3,4,5/
@bp.route('/get_posts/<post_ids>/', methods=['GET'])
@require_key
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
@require_key
def get_comment(comment_id=None):
	return jcon((db.session.query(Comment).filter_by(id=comment_id).first()))


# multiple comments comma seperated, example /1,2,3,4,5/
@bp.route('/get_comments/<comment_ids>/', methods=['GET'])
@require_key
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


@bp.route('/new_comment', methods=['POST'])
@require_key
def new_comment(comment_ids=None):
	text = request.form.get('comment_text')
	post_id = request.form.get('post_id')
	post_url = request.form.get('post_url')
	parent_id = request.form.get('parent_id')
	sub_name = request.form.get('sub_name')
	anonymous = request.form.get('anonymous')

	if anonymous != None:
		anonymous = True
	else:
		anonymous = False

	if parent_id == '':
		parent_id = None

	if post_url != None:
		if post_url_parse(post_url) != post_url_parse(config.URL):
			return json.dumps({'error': 'bad origin url'})

	elif text == None or post_id == None or sub_name == None:
		return json.dumps({'error': 'bad comment'})

	if parent_id != None:
		level = (db.session.query(Comment).filter_by(id=parent_id).first().level) + 1
	else:
		level = None

	post = db.session.query(Post).filter_by(id=post_id).first()
	if post.locked == True:
		return json.dumps({'error': 'post is locked'})

	new_comment = Comment(post_id=post_id, sub_name=sub_name, text=text,
			  author=request.headers['username'], author_id=session['user_id'],
			  parent_id=parent_id, level=level, anonymous=anonymous, deleted=deleted)

	db.session.add(new_comment)
	db.session.commit()

	new_comment.permalink = post.get_permalink() + str(new_comment.id)
	db.session.commit()

	new_vote = Vote(comment_id=new_comment.id, vote=1,
			user_id=session['user_id'], post_id=None)
	db.session.add(new_vote)

	new_comment.ups += 1
	db.session.add(new_comment)
	db.session.commit()

	return redirect(url_for('get_comment', comment_ids=comment_ids))


@bp.route('/new_post', methods=['POST'])
@require_key
def new_post(post_ids=None):
	post_type = request.form.get('post_type')
	anonymous = request.form.get('anonymous')
	remote_image_url = request.form.get('remote_image_url')
	self_text = request.form.get('self_text')
	sub = request.form.get('sub')
	title = request.form.get('title')
	url = request.form.get('url')

	if anonymous != None:
		anonymous = True
	else:
		anonymous = False

	if sub == None or title == None or post_type == None:
		return json.dumps({'error': 'bad post'})

	author_id = (db.session.query(Iuser).filter_by(username=request.headers['username']).first().id)

	new_post = Post(post_type=post_type, anonymous=anonymous,
			remote_image_url=remote_image_url, self_text=self_text, sub=sub,
			title=title, url=url, inurl_title=convert_ied(title), author=request.headers['username'],
			author_id=author_id)

	db.session.add(new_post)
	db.session.commit()

	new_vote = Vote(vote=1, user_id=author_id, post_id=post_ids)
	db.session.add(new_vote)

	new_post.ups += 1
	db.session.add(new_post)
	db.session.commit()

	return redirect(url_for('api.get_post', post_ids=post_ids))
