from flask import Flask, render_template, request, redirect, flash, url_for, Blueprint, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, exists
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache
from flask_session import Session
from flask_session_captcha import FlaskSessionCaptcha
from datetime import timedelta, datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import time
import re
import config
import base64
import os
import urllib.parse

from models import *
from functions import *

app = Flask(__name__)
app.config.from_object('config')
cache = Cache(app, config={'CACHE_TYPE': config.CACHE_TYPE})

db = SQLAlchemy(app)

Session(app)
captcha = FlaskSessionCaptcha(app)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=config.LIMITER_DEFAULTS
)

@app.before_request
def before_request():
	if app.debug:
		g.start = time.time()
	session.permanent = True
	
	request.sub = False
	uri = request.environ['REQUEST_URI']
	if len(uri) > 2:
		if uri[:3] == '/r/':
			getsub = re.findall('\/r\/([a-zA-Z1-9-_]*)', request.environ['REQUEST_URI'])
			if len(getsub) > 0:
				request.sub = getsub[0]
				if 'username' in session:
					if session['username'] in get_sub_mods(request.sub):
						request.is_mod = True
	#flash(str(vars(request)))

@app.after_request
def apply_headers(response):
	#response.headers["X-Frame-Options"] = "SAMEORIGIN"
	#response.headers["X-XSS-Protection"] = "1; mode=block"
	#response.headers['X-Content-Type-Options'] = 'nosniff'
	if 'username' in session:
		has_messages(session['username'])
		session['last_url'] = request.url
	if app.debug:
		if hasattr(g, 'start'):
			load_time = str(time.time() - g.start)
			print('\n[Load: %s]' % load_time)
	return response

@cache.memoize(600)
def get_sub_mods(sub, admin=True):
	mod_subs = db.session.query(Moderator).filter_by(sub=sub).all()
	if admin == False:
		return [m.username for m in mod_subs]
	admins = db.session.query(Iuser).filter_by(admin=True).all()
	for a in admins:
		mod_subs.append(a)
	return [m.username for m in mod_subs]

def is_mod(obj, username):
	if hasattr(obj, 'inurl_title'):
		post = obj
		if db.session.query(db.session.query(Moderator).filter(Moderator.username.like(username),
			Moderator.sub.like(obj.sub)).exists()).scalar():
			return True
	elif hasattr(obj, 'parent_id'):
		if db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
			Moderator.sub.like(obj.sub)).exists()).scalar():
			return True
	return False

def is_admin(username):
	#if db.session.query(db.session.query(Iuser).filter_by(admin=True, username=username).exists()).scalar():
	if 'admin' in session:
		if session['admin'] == True:
			return True
	return False

def set_rate_limit():
	if 'username' in session:
		session['rate_limit'] = int(time.time()) + (config.RATE_LIMIT_TIME * 60)

def normalize_username(username):
	username = db.session.query(Iuser).filter(func.lower(Iuser.username) == func.lower(username)).first()
	if username != None:
		return username.username
	return False

def normalize_sub(sub):
	sub = db.session.query(Sub).filter(func.lower(Sub.name) == func.lower(sub)).first()
	if sub != None:
		return sub.name
	return False


@app.route('/login/',  methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		if config.CAPTCHA_ENABLE:
			if captcha.validate() == False:
				flash('invalid captcha', 'danger')
				return redirect(url_for('login'))
		if username == None or password == None:
			flash('Username or Password missing.', 'danger')
			return redirect(url_for('login'), 302)
		if username == '' or password == '' or len(username) > 20 or len(password) > 100:
			flash('Username or Password empty.', 'danger')
			return redirect(url_for('login'), 302)

		if db.session.query(db.session.query(Iuser)
				.filter_by(username=username)
				.exists()).scalar():
			login_user = db.session.query(Iuser).filter_by(username=username).first()
			hashed_pw = login_user.password
			if check_password_hash(hashed_pw, password):
				logout()
				[session.pop(key) for key in list(session.keys())]
				session['username'] = login_user.username
				session['user_id'] = login_user.id
				session['admin'] = login_user.admin
				if hasattr(login_user, 'anonymous'):
					if login_user.anonymous:
						session['anonymous'] = True

				return redirect(url_for('index'), 302)

		flash('Username or Password incorrect.', 'danger')
		return redirect(url_for('login'), 302)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
	[session.pop(key) for key in list(session.keys())]
	return redirect(url_for('index'), 302)

@app.route('/register', methods=['POST'])
def register():
	if request.method == 'POST':
		if config.CAPTCHA_ENABLE:
			if captcha.validate() == False:
				flash('invalid captcha', 'danger')
				return redirect(url_for('login'))
		username = request.form.get('username')
		password = request.form.get('password')
		email = request.form.get('email')

		if 'username' in session:
			flash('already logged in', 'danger')
			if 'last_url' in session:
				return redirect(session['last_url'] or "/")
			return redirect('/')

		if username == None or password == None:
			flash('username or password missing', 'danger')
			return redirect(url_for('login'))

		if verify_username(username):
			if db.session.query(db.session.query(Iuser).filter(func.lower(Iuser.username) == func.lower(username)).exists()).scalar():
				flash('username exists', 'danger')
				return redirect(url_for('login'))
		else:
			flash('invalid username', 'danger')
			return redirect(url_for('login'))

		if len(password) > 100:
			flash('password too long', 'danger')
			return redirect(url_for('login'))

		if email != None and email != '':
			if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
				flash('invalid email', 'danger')
				return redirect(url_for('login'))

		new_user = Iuser(username=username, email=email,
			password=generate_password_hash(password))
		db.session.add(new_user)
		db.session.commit()
		logout()
		session['username'] = new_user.username
		session['user_id'] = new_user.id
		set_rate_limit()
		return redirect(config.URL, 302)

@app.route('/')
def index():
	return subi('all', nsfw=False)

@cache.memoize(600)
def get_subi(subi, user_id=None, posts_only=False, deleted=False, offset=0, limit=15, nsfw=None, d=None, s=None):
	if type(offset) == int:
		offset = int(offset)
	else:
		offset = 0
	if subi != 'all':
		subname = db.session.query(Sub).filter(func.lower(Sub.name) == subi.lower()).first()
		if subname == None:
			return {'error':'sub does not exist'}
		subi = subname.name
		posts = db.session.query(Post).filter_by(sub=subi, deleted=False)
	elif user_id != None:
		posts = db.session.query(Post).filter_by(author_id=user_id, deleted=False)
	else:
		posts = db.session.query(Post).filter_by(deleted=False)

# .order_by((Post.created).desc())
#			posts = db.session.query(Post).filter_by(deleted=False).order_by((Post.ups - Post.downs).desc())
	if d == 'hour':
		ago = datetime.now() - timedelta(hours=1)
	elif d == 'day':
		ago = datetime.now() - timedelta(hours=24)
	elif d == 'week':
		ago = datetime.now() - timedelta(days=7)
	elif d == 'month':
		ago = datetime.now() - timedelta(days=31)
	else:
		ago = datetime.now() - timedelta(days=9999)

	if d:
		posts.filter(Post.created > ago)

	if s == 'top':
		posts = posts.order_by((Post.ups - Post.downs).desc())
	elif s == 'new':
		posts = posts.order_by((Post.created).desc())

	posts = [post for post in posts if post.created > ago]
	more = False
	pc = len(posts)
	if pc > limit:
		more = True
	
	posts = posts[offset:]
	posts = posts[:limit]

	stid = False
	for p in posts:
		if p.stickied == True:
			stid = p.id

	if stid:
		posts = [post for post in posts if post.id != stid]

	if subi != 'all':
		sticky = db.session.query(Post).filter(func.lower(Post.sub) == subi.lower(), Post.stickied == True).first()
		if sticky:
			posts.insert(0, sticky)

	if more and len(posts) > 0:
		posts[len(posts)-1].more = True

	p = []
	for post in posts:
		if hasattr(post, 'text'):
			post.text = psuedo_markup(post.text)
		if thumb_exists(post.id):
			post.thumbnail = 'thumb-' + str(post.id) + '.JPEG'
		post.mods = get_sub_mods(post.sub)
		post.created_ago = time_ago(post.created)
		if subi != 'all':
			post.site_url = config.URL + '/r/' + subi + '/' + str(post.id) + '/' + post.inurl_title
		post.remote_url_parsed = post_url_parse(post.url)
		post.comment_count = db.session.query(Comment).filter_by(post_id=post.id).count()
		if 'user_id' in session and 'username' in session:
			post.has_voted = db.session.query(Vote).filter_by(post_id=post.id, user_id=session['user_id']).first()
			if post.has_voted != None:
				post.has_voted = post.has_voted.vote
			if db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']), Moderator.sub.like(post.sub)).exists()).scalar():
				post.is_mod = True
		p.append(post)
	return p

@app.route('/r/<subi>/')
def subi(subi, user_id=None, posts_only=False, offset=0, limit=15, nsfw=None, show_top=True, s=None, d=None):
	offset = request.args.get('offset')
	d = request.args.get('d')
	s = request.args.get('s')

	if type(offset) == None:
		offset = 0

	if request.environ['QUERY_STRING'] == '':
		session['off_url'] = request.url + '?offset=15'
		session['prev_off_url'] = request.url
	else:
		if offset == None:
			session['off_url'] = request.url + '&offset=15'
			session['prev_off_url'] = request.url
		else:
			if (int(offset) - 15) > 0:
				session['prev_off_url'] = request.url.replace('offset=' + offset, 'offset=' + str(int(offset) -15))
			else:
				session['prev_off_url'] = re.sub('[&\?]?offset=(\d+)', '', request.url)
			session['off_url'] = request.url.replace('offset=' + offset, 'offset=' + str(int(offset) +15))
	if request.url.find('offset=') == -1:
		session['prev_off_url'] = False

	prefix = '&'

	session['top_url'] = re.sub('[&\?]?s=\w+', '', request.url) + prefix + 's=top'
	session['new_url'] = re.sub('[&\?]?s=\w+', '', request.url) + prefix + 's=new'

	session['hour_url'] = re.sub('[&\?]?d=\w+', '', request.url) + prefix + 'd=hour'
	session['day_url'] = re.sub('[&\?]?d=\w+', '', request.url) + prefix + 'd=day'	
	session['week_url'] = re.sub('[&\?]?d=\w+', '', request.url) + prefix + 'd=week'
	session['month_url'] = re.sub('[&\?]?d=\w+', '', request.url) + prefix + 'd=month'

	for a in ['top_url', 'new_url', 'day_url', 'week_url', 'hour_url', 'month_url']:
		if session[a].find('/&') != -1:
			session[a] = session[a].replace('/&', '/?')

	sub_posts = get_subi(subi=subi, user_id=user_id, posts_only=posts_only, deleted=False, offset=offset, limit=15, d=d, s=s)
	if type(sub_posts) == dict:
		if 'error' in sub_posts.keys():
			flash(sub_posts['error'], 'danger')
			return redirect('/')	

	if posts_only:
		return sub_posts

	return render_template('sub.html', posts=sub_posts, url=config.URL, show_top=show_top)

	#return str(hasattr(request.environ, 'QUERY_STRING'))#str(vars(request))

@cache.memoize(600)
def c_get_comments(sub=None, post_id=None, inurl_title=None, comment_id=False, sort_by=None, comments_only=False, user_id=None):
	post = None
	parent_comment = None
	if not comments_only:
		if post_id != None:
			post = db.session.query(Post).filter_by(id=post_id, sub=sub).first()
			post.mods = get_sub_mods(post.sub)
			post.comment_count = db.session.query(Comment).filter_by(post_id=post.id).count()
			post.created_ago = time_ago(post.created)
			post.remote_url_parsed = post_url_parse(post.url)
		else:
			post = None
		if 'user_id' in session:
			post.has_voted = db.session.query(Vote).filter_by(post_id=post.id, user_id=session['user_id']).first()
			if post.has_voted != None:
				post.has_voted = post.has_voted.vote	

		if not comment_id:
			if sort_by == 'new':
				comments = db.session.query(Comment).filter(Comment.post_id == post_id, Comment.level < 7, Comment.deleted == False)\
				.order_by((Comment.created).asc()).all()
			else:
				comments = db.session.query(Comment).filter(Comment.post_id == post_id, Comment.level < 7, Comment.deleted == False)\
				.order_by((Comment.ups - Comment.downs).desc()).all()
	
			parent_comment = None
			parent_posturl = None
		else:
			comments = list_of_child_comments(comment_id, sort_by=sort_by)
			parent_comment = db.session.query(Comment).filter_by(id=comment_id).first()
			comments.append(parent_comment)
	else:
		comments = db.session.query(Comment).filter(Comment.author_id == user_id).order_by(Comment.created.desc()).all()


	for c in comments:
		c.text = psuedo_markup(c.text)
		c.mods = get_sub_mods(c.sub_name)
		c.created_ago = time_ago(c.created)
		if 'user_id' in session:
			c.has_voted = db.session.query(Vote).filter_by(comment_id=c.id, user_id=session['user_id']).first()
			if c.has_voted != None:
				c.has_voted = c.has_voted.vote
				if Comment.sub_name:
					if db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']), Moderator.sub.like(Comment.sub_name)).exists()).scalar():
						Comment.is_mod = True
					else:
						Comment.is_mod = False

	return comments, post, parent_comment

@app.route('/r/<sub>/<post_id>/<inurl_title>/<comment_id>/sort-<sort_by>')
@app.route('/r/<sub>/<post_id>/<inurl_title>/<comment_id>/')
@app.route('/r/<sub>/<post_id>/<inurl_title>/sort-<sort_by>')
@app.route('/r/<sub>/<post_id>/<inurl_title>/')
def get_comments(sub=None, post_id=None, inurl_title=None, comment_id=False, sort_by=None, comments_only=False, user_id=None):
	if sub == None or post_id == None or inurl_title == None:
		if not comments_only:
			return 'badlink'
	try:
		int(comment_id)
	except:
		comment_id = False

	comments, post, parent_comment = c_get_comments(sub=sub, post_id=post_id, inurl_title=inurl_title, comment_id=comment_id, sort_by=sort_by, comments_only=comments_only, user_id=user_id)
	
	if post != None and 'username' in session:
		if db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']), Moderator.sub.like(post.sub)).exists()).scalar():
			post.is_mod = True

	if comments_only:
		return comments

	if not comment_id:
		tree = create_id_tree(comments)
	else:
		tree = create_id_tree(comments, parent_id=comment_id)

	tree = comment_structure(comments, tree)
	return render_template('comments.html', comments=comments, post_id=post_id, 
		post_url='%s/r/%s/%s/%s/' % (config.URL, sub, post_id, post.inurl_title), 
		post=post, tree=tree, parent_comment=parent_comment)

# need to entirely rewrite how comments are handled once everything else is complete
# this sort of recursion KILLS performance, especially when combined with the already
# terrible comment_structure function.
@cache.memoize(600)
def list_of_child_comments(comment_id, sort_by=None):
	comments = {}
	current_comments = []
	if sort_by == 'new':
		start = db.session.query(Comment).filter(Comment.parent_id == comment_id, Comment.deleted == False)\
					.order_by((Comment.created).asc()).all()
	else:
		start = db.session.query(Comment).filter(Comment.parent_id == comment_id, Comment.deleted == False)\
					.order_by((Comment.ups - Comment.downs).desc()).all()

	for c in start:
		current_comments.append(c.id)
		comments[c.id] = c
	while len(current_comments) > 0:
		for current_c in current_comments:
			if sort_by == 'new':
				get_comments = db.session.query(Comment).filter(Comment.parent_id == current_c)\
					.order_by((Comment.created).asc()).all()
			else:
				get_comments = db.session.query(Comment).filter(Comment.parent_id == current_c)\
					.order_by((Comment.ups - Comment.downs).desc()).all()
			for c in get_comments:
				current_comments.append(c.id)
				comments[c.id] = c
			current_comments.remove(current_c)
	return [comments[c] for c in comments]

@app.route('/create', methods=['POST', 'GET'])
def create_sub():
	if request.method == 'POST':
		subname = request.form.get('subname')
		if subname.lower() == 'all':
			flash('reserved name')
			return redirect(url_for('create_sub'))
		if config.CAPTCHA_ENABLE:
			if captcha.validate() == False:
				flash('invalid captcha', 'danger')
				return redirect(url_for('create_sub'))
			if 'rate_limit' in session and config.RATE_LIMIT == True:
				rl = session['rate_limit'] - time.time()
				if rl > 0:
					flash('rate limited, try again in %s seconds' % str(rl))
					if 'last_url' in session:
						return redirect(session['last_url'] or "/")
					return redirect('/')
		if subname != None and verify_subname(subname) and 'username' in session:
			if len(subname) > 30 or len(subname) < 1:
				return 'invalid length'
			new_sub = Sub(name=subname, created_by=session['username'], created_by_id=session['user_id'])
			db.session.add(new_sub)
			db.session.commit()
			new_mod = Moderator(username=new_sub.created_by, sub=new_sub.name)
			db.session.add(new_mod)
			db.session.commit()
			cache.delete_memoized(get_subi)
			set_rate_limit()
			return redirect(config.URL + '/r/' + subname, 302)
		return 'invalid'
	elif request.method == 'GET':
		return render_template('create.html')

@app.route('/u/<username>/', methods=['GET'])
def view_user(username):
	vuser = db.session.query(Iuser).filter_by(username=username).first()
	mod_of = db.session.query(Moderator).filter_by(username=vuser.username).all()
	mods = {}
	for s in mod_of:
		mods[s.sub] = s.rank
	vuser.mods = mods
	posts = subi('all', user_id=vuser.id, posts_only=True)
	for p in posts:
		p.mods = get_sub_mods(p.sub)
	#sub, post_id, inurl_title, comment_id=False, sort_by=None, comments_only=False, user_id=None):
	comments_with_posts = []
	comments = get_comments(comments_only=True, user_id=vuser.id)[:15]
	for c in comments:
		c.mods = get_sub_mods(c.sub_name)
		cpost = db.session.query(Post).filter_by(id=c.post_id).first()
		comments_with_posts.append((c, cpost))
	return render_template('user.html', vuser=vuser, posts=posts, url=config.URL, comments_with_posts=comments_with_posts)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
	if request.method == 'POST':
		post_id = request.form.get('post_id')
		comment_id = request.form.get('comment_id')
		vote = request.form.get('vote')
	
		if 'username' not in session or 'user_id' not in session:
			return 'not logged in'
		else:
			user_id = session['user_id']
			username = session['username']
		if comment_id != None and post_id != None:
			return 'cannot vote for 2 objects'
		if comment_id == None and post_id == None:
			return 'no vote object'
		if vote not in ['1', '-1', '0']:
			return 'invalid vote amount'
	
		vote = int(vote)

		invert_vote = False
		if post_id != None:
			last_vote = db.session.query(Vote).filter_by(user_id=user_id, post_id=post_id).first()
			if last_vote != None:
				if last_vote.vote == vote:
					return 'already voted'
				else:
					invert_vote = True

		elif comment_id != None:
			last_vote = db.session.query(Vote).filter_by(user_id=user_id, comment_id=comment_id).first()
			if last_vote != None:
				if last_vote.vote == vote:
					return 'already voted'
				else:
					invert_vote = True

		if vote == 0 and last_vote == None:
			return 'never voted'

		cache.delete_memoized(get_subi)
		cache.delete_memoized(c_get_comments)
		cache.delete_memoized(list_of_child_comments)

		if vote == 0:
			if last_vote.post_id != None:
				if last_vote.post_id != None:
					vpost = db.session.query(Post).filter_by(id=last_vote.post_id).first()
				elif last_vote.comment_id != None:
					vpost = db.session.query(Comment).filter_by(id=last_vote.post_id).first()
				if last_vote.vote == 1:
					vpost.ups -= 1
				elif last_vote.vote == -1:
					vpost.downs -= 1
			db.session.delete(last_vote)
			db.session.commit()
			return str(vpost.ups - vpost.downs)

		if last_vote == None:
			new_vote = Vote(user_id=user_id, vote=vote, comment_id=comment_id, post_id=post_id)
			db.session.add(new_vote)
			db.session.commit()

		elif invert_vote:
			if last_vote.vote == 1:
				last_vote.vote = -1
			else:
				last_vote.vote = 1
		db.session.commit()

		if comment_id != None:
			vcom = db.session.query(Comment).filter_by(id=comment_id).first()
		elif post_id != None:
			vcom = db.session.query(Post).filter_by(id=post_id).first()


		if vote == 1:
			if not invert_vote:
				vcom.ups += 1
			else:
				vcom.ups += 1
				vcom.downs -= 1

		elif vote == -1:
			if not invert_vote:
				vcom.downs += 1
			else:
				vcom.downs += 1
				vcom.ups -= 1

		db.session.commit()	

	
		return str(vcom.ups - vcom.downs)
	elif request.method == 'GET':
		return 'get'

@app.route('/create_post', methods=['POST', 'GET'])
def create_post(postsub=None):
	if request.method == 'POST':
		title = request.form.get('title')
		url = request.form.get('url')
		sub = request.form.get('sub')
		#if db.session.query(db.session.query(Iuser).filter(func.lower(Iuser.username) == func.lower(username)).exists()).scalar():

		self_post_text = request.form.get('self_post_text')
		anonymous = request.form.get('anonymous')
		if config.CAPTCHA_ENABLE:
			if captcha.validate() == False:
				flash('invalid captcha', 'danger')
				return redirect(url_for('create_post'))
			if 'rate_limit' in session and config.RATE_LIMIT == True:
				rl = session['rate_limit'] - time.time()
				if rl > 0:
					flash('rate limited, try again in %s seconds' % str(rl))
					if 'last_url' in session:
						return redirect(session['last_url'] or "/")
					return redirect('/')

		sub = db.session.query(Sub).filter(func.lower(Sub.name) == func.lower(sub)).first()
		if sub == None:
			flash('invalid sub', 'danger')
			return redirect('/create_post')

		sub = sub.name

		if anonymous != None:
			anonymous = True
		else:
			anonymous = False

		if len(self_post_text) > 0:
			post_type = 'self_post'
		elif len(url) > 0:
			post_type = 'url'
		else:
			flash('invalid post type, not url or self', 'danger')
			return redirect(url_for('create_post'))

		if title == None or 'username' not in session or 'user_id' not in session:
			flash('invalid post, no title/username/uid', 'danger')
			return redirect(url_for('create_post'))
		if len(title) > 400 or len(title) < 1 or len(sub) > 30 or len(sub) < 1:
			flash('invalid title/sub length', 'danger')
			return redirect(url_for('create_post'))

		if post_type == 'url':
			if len(url) > 2000 or len(url) < 1:
				flash('invalid url length', 'danger')
				return redirect(url_for('create_post'))
			new_post = Post(url=url, title=title, inurl_title=convert_ied(title), author=session['username'],
						author_id=session['user_id'], sub=sub, post_type=post_type, anonymous=anonymous)
		elif post_type == 'self_post':
			if len(self_post_text) < 1 or len(self_post_text) > 20000:
				flash('invalid self post length', 'danger')
				return redirect(url_for('create_post'))
			new_post = Post(self_text=self_post_text, title=title, inurl_title=convert_ied(title),
				author=session['username'], author_id=session['user_id'], sub=sub, post_type=post_type, anonymous=anonymous)

		db.session.add(new_post)
		db.session.commit()

		if post_type == 'url':
			os.system('python3 get_thumbnail.py %s "%s"' % (str(new_post.id), urllib.parse.quote(url)))

		new_post.permalink = config.URL + '/r/' + new_post.sub + '/' + str(new_post.id) + '/' + new_post.inurl_title +  '/'
		if is_admin(session['username']) and anonymous == False:
			new_post.author_type = 'admin'
		elif is_mod(new_post, session['username']) and anonymous == False:
			new_post.author_type = 'mod'
		db.session.commit()
		url = config.URL + '/r/' + sub
		set_rate_limit()

		cache.delete_memoized(get_subi)

		return redirect(url, 302)

	if request.method == 'GET':
		if request.referrer:
			subref = re.findall('\/r\/([a-zA-z1-9-_]*)', request.referrer)
		if 'subref' in locals():
			if len(subref) == 1:
				if len(subref[0]) > 0:
					postsub = subref[0]
		return render_template('create_post.html', postsub=postsub)

@app.route('/create_comment', methods=['POST'])
def create_comment():
	text = request.form.get('comment_text')
	post_id = request.form.get('post_id')
	post_url = request.form.get('post_url')
	parent_id = request.form.get('parent_id')
	sub_name = request.form.get('sub_name')
	anonymous = request.form.get('anonymous')

	if 'rate_limit' in session and config.RATE_LIMIT == True:
		rl = session['rate_limit'] - time.time()
		if rl > 0:
			flash('rate limited, try again in %s seconds' % str(rl))
			if 'last_url' in session:
				return redirect(session['last_url'] or "/")
			return redirect('/')

	if anonymous != None:
		anonymous = True
	else:
		anonymous = False

	if parent_id == '':
		parent_id = None

	if post_url != None:
		if post_url_parse(post_url) != post_url_parse(config.URL):
			flash('bad origin url', 'danger')
			return redirect(request.referrer or '/')

	if 'username' not in session:
		flash('not logged in', 'danger')
		return redirect(post_url)

	elif text == None or post_id == None or sub_name == None:
		flash('bad comment', 'danger')
		return redirect(post_url)

	if parent_id != None:
		level = (db.session.query(Comment).filter_by(id=parent_id).first().level) + 1
	else:
		level = None

	post = db.session.query(Post).filter_by(id=post_id).first()
	if post.locked == True:
		flash('post is locked')
		return redirect(post.permalink)

	new_comment = Comment(post_id=post_id, sub_name = sub_name, text=text,
		author=session['username'], author_id=session['user_id'], parent_id=parent_id, level=level, anonymous=anonymous)
	db.session.add(new_comment)
	db.session.commit()

	new_comment.permalink = post.permalink +  str(new_comment.id)

	if is_admin(session['username']) and anonymous == False:
		new_comment.author_type = 'admin'
	elif is_mod(new_comment, session['username']) and anonymous == False:
		new_comment.author_type = 'mod'

	db.session.commit()

	cache.delete_memoized(get_subi)
	cache.delete_memoized(c_get_comments) 
	cache.delete_memoized(list_of_child_comments)

	set_rate_limit()

	return redirect(post_url, 302)

def send_message(title, text, sent_to, sender=None):
	new_message = Message(title=title, text=text, sent_to=sent_to, sender=sender)
	db.session.add(new_message)
	db.session.commit()

@cache.memoize(600)
def has_messages(username):
	if 'username' in session:
		if 'has_messages' not in session:
			messages = db.session.query(Message).filter_by(sent_to=username, read=False).count()
		else:
			messages = None
		if messages != None:
			if messages > 0:
				session['has_messages'] = True
				session['unread_messages'] = messages
				return True
	return False

@app.route('/u/<username>/messages/', methods=['GET'])
def user_messages(username=None):
	if 'username' not in session or username == None:
		flash('not logged in', 'danger')
		return redirect('/login')
	else:
		if session['username'] != username:
			flash('you are not that user', 'danger')
			return redirect('/')
		else:
			read = db.session.query(Message).filter_by(sent_to=username, read=True).all()
			unread = db.session.query(Message).filter_by(sent_to=username, read=False).all()
			for r in read:
				if r.in_reply_to != None:
					r.ppath = r.in_reply_to.replace(config.URL, '')
			
			session['has_messages'] = False
			session['unread_messages'] = None

			for r in unread:
				r.read = True
				session
			db.session.commit()

			for r in unread:
				if r.in_reply_to != None:
					r.ppath = r.in_reply_to.replace(config.URL, '')

			return render_template('messages.html', read=read, unread=unread)

@app.route('/u/<username>/messages/reply/<mid>', methods=['GET'])
def reply_message(username=None, mid=None):
	if 'username' not in session or username == None:
		flash('not logged in', 'danger')
		return redirect('/login')
	if session['username'] != username:
		flash('you are not that user', 'danger')
		return redirect('/')

	m = db.session.query(Message).filter_by(sent_to=username, id=mid).first()
	if m == None:
		flash('invalid message id', 'danger')
		return redirect('/')
	else:
		if hasattr(m, 'in_reply_to'):
			if m.in_reply_to != None:
				m.ppath = m.in_reply_to.replace(config.URL, '')
		return render_template('message_reply.html', message=m, sendto=False)

def sendmsg(title, text, sender, sent_to):
	cache.delete_memoized(has_messages)
	new_message = Message(title=title, text=text, sender=sender, sent_to=sent_to)
	db.session.add(new_message)
	db.session.commit()

@app.route('/message/', methods=['GET', 'POST'])
@app.route('/message/<username>', methods=['GET', 'POST'])
def msg(username=None):
	if 'username' not in session:
		flash('not logged in', 'danger')
		return redirect('/login/')
	if request.method == 'POST':
		text = request.form.get('message_text')
		title = request.form.get('message_title')
		sent_to = request.form.get('sent_to')
		if sent_to == None:
			sent_to = username

		if 'rate_limit' in session and config.RATE_LIMIT == True:
			rl = session['rate_limit'] - time.time()
			if rl > 0:
				flash('rate limited, try again in %s seconds' % str(rl))
				if 'last_url' in session:
					return redirect(session['last_url'] or "/")
				return redirect('/')

		if len(text) > 20000 or len(title) > 200:
			flash('text/title too long')
			return redirect('/message/')

		if str(sent_to) == 'None':
			flash('this user is not valid', 'danger')
			return redirect('/message/')

		sender = session['username']

		sendmsg(title=title, text=text, sender=session['username'], sent_to=sent_to)
		set_rate_limit()
		flash('sent message', category='success')
		return redirect(url_for('msg'))

	if request.method == 'GET':
		if username != None:
			if len(str(username)) < 1:
				flash('invalid username')
				return redirect('/')
		if request.referrer:
			ru = re.findall('\/r\/([a-zA-z1-9-_]*)', request.referrer)
			if ru != None:
				if len(ru) == 1:
					if len(ru[0]) > 0:
						username = ru[0]
		return render_template('message_reply.html', sendto=username, message=None)


@app.route('/r/<sub>/mods/', methods=['GET'])
def submods(sub=None):
	modactions = db.session.query(Mod_action).filter_by(sub=sub).all()
	if type(modactions) != None:
		modactions = [m for m in modactions]
	return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), modactions=modactions)

@app.route('/r/<sub>/mods/banned/', methods=['GET'])
def bannedusers(sub=None):
	banned = db.session.query(Ban).filter_by(sub=sub).all()
	if type(banned) != None:
		banned = [b for b in banned]
	return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), banned=banned)

@app.route('/r/<sub>/mods/add/', methods=['GET'])
def addmod(sub=None):
	if hasattr(request, 'is_mod'):
		if request.is_mod:
			return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), addmod=True)
	return '403'

@app.route('/r/<sub>/mods/remove/', methods=['GET'])
def removemod(sub=None):
	if hasattr(request, 'is_mod'):
		if request.is_mod:
			return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), addmod=True)
	return '403'

from mod import bp
app.register_blueprint(bp)

from user import ubp
app.register_blueprint(ubp)