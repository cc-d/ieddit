from ieddit import *
import json
from functools import wraps

abp = Blueprint('admin', 'admin', url_prefix='/admin')

def admin_only(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'admin' not in session:
			return '403 ad sess'
		if 'username' not in session:
			return '403 sess'
		admins = db.session.query(Iuser).filter_by(admin=True).all()
		anames = [a.username for a in admins]
		if session['username'] not in anames:
			return '403 names'
		return f(*args, **kwargs)
	return decorated_function

@abp.route('/',  methods=['GET'])
@admin_only
def admincp():
	keys = db.session.query(Api_key).all()
	return render_template('admin.html', keys=keys)


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
		return 'ok'
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
		return 'deleted'
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







