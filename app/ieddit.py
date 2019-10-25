from flask import Flask, render_template, request, redirect, flash, url_for, Blueprint, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, exists
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from flask_caching import Cache
from flask_session import Session
from flask_session_captcha import FlaskSessionCaptcha
from datetime import timedelta, datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address, get_ipaddr
from jinja2 import escape, Markup
import logging

import time
import re
import config
import base64
#from subprocess import call
import os
import _thread
import urllib.parse
from functools import wraps
import requests

from sqlalchemy.orm import load_only
import traceback

from email.mime.text import MIMEText

from models import *

from functions.functions import *

from sqlalchemy.orm import load_only

app = Flask(__name__)
app.config.from_object('config')
cache = Cache(app, config={'CACHE_TYPE': config.CACHE_TYPE})

logger = logging.getLogger(__name__)


if (config.SENTRY_ENABLED):
	import sentry_sdk
	from sentry_sdk.integrations.flask import \
		FlaskIntegration

	sentry_sdk.init(
		config.SENTRY_DSN,
		integrations=[FlaskIntegration()]
	)

db = SQLAlchemy(app)
db.session.rollback()

Session(app)
captcha = FlaskSessionCaptcha(app)

limiter = Limiter(
	app,
	key_func=get_ipaddr,
	default_limits=config.LIMITER_DEFAULTS
)

#cache.clear()

cache_bust = '?' + str(time.time()).split('.')[0]

@app.before_request
def before_request():

	g.cache_bust = cache_bust

	if app.debug:
		g.start = time.time()
	session.permanent = True

	try:
		request.sub
	except:
		request.sub = False

	if 'blocked_subs' not in session:
		if 'username' in session:
			session['blocked_subs'] = get_blocked_subs(session['username'])
		else:
			session['blocked_subs'] = []

	request.is_mod = False

	uri = request.environ['REQUEST_URI']
	if len(uri) > 2:
		if uri[:3] == '/i/':
			getsub = re.findall('\/i\/([a-zA-Z1-9-_]*)', request.environ['REQUEST_URI'])
			if len(getsub) > 0:
				if getsub[0] != 'all':
					getsub[0] = normalize_sub(getsub[0])
					oldsub = request.sub
					request.sub = getsub[0]
					if 'username' in session:
						if session['username'] in get_sub_mods(request.sub):
							request.is_mod = True

					if oldsub != request.sub:
						request.subtitle = get_subtitle(request.sub)

	if 'username' in session:
		has_messages(session['username'])
		get_blocked(session['username'])
		session['blocked'] = get_blocked(session['username'])
	else:
		session['blocked'] = {'comment_id':[], 'post_id':[], 'other_user':[], 'anon_user':[]}


	if 'anon_user' not in session['blocked']:
		session['blocked']['anon_user'] = []
	# disabled due to lack of use

	#if 'set_darkmode_initial' not in session:
	#	session['darkmode'] = True
	#	if 'username' in session:
	#		u = db.session.query(Iuser).filter_by(username=session['username'])
	#		u.darkmode = True
	#		db.session.commit()
	#	session['set_darkmode_initial'] = True


@app.after_request
def apply_headers(response):
	if response.status_code == 500:
		db.session.rollback()
		print(str(vars(response)))


	response.headers["X-Frame-Options"] = "SAMEORIGIN"
	response.headers["X-XSS-Protection"] = "1; mode=block"
	response.headers['X-Content-Type-Options'] = 'nosniff'
	if config.CSP:
		response.headers['Content-Security-Policy'] = "default-src 'self' *.ieddit.com ieddit.com; img-src *; style-src" +\
		" 'self' 'unsafe-inline' *.ieddit.com ieddit.com; script-src 'self' 'unsafe-inline' *.ieddit.com ieddit.com;"

	#response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	#response.headers["Pragma"] = "no-cache"
	#response.headers["Expires"] = "0"
	#response.headers['Cache-Control'] = 'public, max-age=0'
	session['last_url'] = request.url
	if app.debug:
		if hasattr(g, 'start'):
			load_time = str(time.time() - g.start)
			print('\n[Load: %s]' % load_time)


	if request.environ['REQUEST_METHOD'] == 'POST':
		cache.clear()


	return response


@app.teardown_request
def teardown_request(exception):
	if exception:
		db.session.rollback()
	db.session.remove()


def only_cache_get(*args, **kwargs):
	if request.method == 'GET':
		return False
	return True

@app.errorhandler(Exception)
def handle_error(error):
	code = 500
	description = error
	if isinstance(error, HTTPException):
		code = error.code
		description = error.description
	if code >= 500:
		description = "A(n) {} occurred. The developers have been notified of this.".format(type(error).__name__  or 'unknown error')
		logger.error(error)
		logger.error(traceback.format_exc())
	return render_template("error.html", error=description, code=code)

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_style(sub=None):
	if sub != None:
		sub = db.session.query(Sub).filter_by(name=normalize_sub(sub)).first()
		return sub.css
	return None

app.jinja_env.globals.update(get_style=get_style)


def catch_all_exceptions(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception as e:
			print('\n\nCaught unkown error in catch_all_exceptions wrapped function %s .\n\n' % f, e)
	return decorated_function

def notbanned(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'username' not in session:
			return redirect(url_for('login'))
		busers = db.session.query(Iuser).filter_by(banned=True).all()
		bnames = [a.username for a in busers]
		if session['username'] in bnames:
			return redirect('/')
		return f(*args, **kwargs)
	return decorated_function


def send_email(etext=None, subject=None, to=None, from_domain=config.MAIL_FROM):
	if config.MAIL_TYPE == 'mailgun':
		etext = '<html><head><body>' + etext + '</body></html>'
		r = requests.post(config.MG_URL + '/messages',
			auth=('api', config.MG_API_KEY),
			data={'from': 'no-reply <%s>' % (from_domain),
				'to': [to, from_domain], 'subject':subject, 'html':etext})
		print('sending email %s %s %s %s' % (MIMEText(etext, 'html'), subject, to, from_domain))
		print(r.status_code)
		print(r.text)
		print('email %s %s %s' % (to, from_domain, subject))
		return True


# i hate sending external requests
@app.route('/suggest_title')
@limiter.limit("5/minute")
def suggest_title(url=None):
	import requests
	from bs4 import BeautifulSoup
	import urllib.parse
	url = request.args.get('u')
	url = urllib.parse.unquote(url)
	r = requests.get(url, proxies=config.PROXIES)
	if r.status_code == 200:
		try:
			soup = BeautifulSoup(r.text)
			title = soup.find('meta', property='og:title')
			if title != None:
				title = title.get('content', None)
				return title
			else:
				return soup.title.string
		except Exception as e:
			return ''
	return ''

@app.route('/fonts/<file>')
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def send_font(file=None, methods=['GET']):
	if file != None:
		if len(re.findall('^.*.*$', file)) != 1:
			return str(re.findall('^.*.*$'))
		else:
			return app.send_static_file(file)
	else:
		return abort(403)

@app.route('/sitemap.xml')
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def sitemap():
	return app.send_static_file('sitemap.xml')

@app.route('/robots.txt')
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def robotstxt():
	return app.send_static_file('robots.txt')

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_subtitle(sub):
	try:
		title = db.session.query(Sub).filter_by(name=sub).first()
		title = title.title
	except:
		title = None
	return title

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_api_key(username):
	key = db.session.query(Api_key).filter_by(username=username).first()
	return key

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def has_messages(username):
	if 'username' in session:
		messages = db.session.query(Message).filter_by(sent_to=username, read=False).count()
		if messages != None:
			if messages > 0:
				session['has_messages'] = True
				session['unread_messages'] = messages
				return True
	return False

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_sub_mods(sub, admin=True):
	mod_subs = db.session.query(Moderator).filter_by(sub=sub).all()
	if admin == False:
		return [m.username for m in mod_subs]
	admins = db.session.query(Iuser).filter_by(admin=True).all()
	for a in admins:
		mod_subs.append(a)
	return [m.username for m in mod_subs]

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_banned_subs(username):
	subs = db.session.query(Ban).filter_by(username=username).all()
	b = []
	for s in subs:
		b.append(s.sub)
	return b

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def anon_block(obj):
	for c in obj:
		if c.anonymous:
			if c.author_id in session['blocked']['anon_user']:
				c.noblock = False
			else:
				c.noblock = True

		else:
			if c.author_id in session['blocked']['other_user']:
				c.noblock = False
			else:
				c.noblock = True
	return obj

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_muted_subs():
	return [x.name for x in db.session.query(Sub).filter_by(muted=True).all()]

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_blocked(username):
	bdict = {'comment_id':[], 'post_id':[], 'other_user':[], 'anon_user':[]}
	if username == None:
		return bdict
	blocked = db.session.query(Hidden).filter_by(username=username).all()

	if len(blocked) == 0:
		return bdict

	for b in blocked:
		if b.comment_id != None:
			i = db.session.query(Comment).filter_by(id=b.comment_id).first()
			if i != None:
				bdict['comment_id'].append(i.id)
		elif b.post_id != None:
			i = db.session.query(Post).filter_by(id=b.post_id).first()
			if i != None:
				bdict['post_id'].append(i.id)
		elif b.other_user != None:
			i = db.session.query(Iuser).filter_by(id=b.other_user).first()
			if i != None:
				if b.anonymous != True:
					bdict['other_user'].append(i.id)
				else:
					bdict['anon_user'].append(i.id)

	return bdict

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
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

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def is_admin(username):
	if db.session.query(db.session.query(Iuser).filter_by(admin=True, username=username).exists()).scalar():
	#if 'admin' in session:
		return True
	return False

def set_rate_limit(limit_seconds=None):
	if 'username' in session:
		if limit_seconds == None:
			session['rate_limit'] = int(time.time()) + (config.RATE_LIMIT_TIME)
		else:
			session['rate_limit'] = int(time.time()) + (limit_seconds)
		#cache.clear()

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def normalize_username(username, dbuser=False):
	if username == None:
		return False
	username = db.session.query(Iuser).filter(func.lower(Iuser.username) == func.lower(username)).first()
	if username != None:
		if dbuser:
			return username
		return username.username
	return False

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def normalize_sub(sub):
	subl = db.session.query(Sub).filter(func.lower(Sub.name) == func.lower(sub)).first()
	if subl != None:
		return subl.name
	return sub

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_all_subs(explore=False):
	subs = db.session.query(Sub).all()
	if explore == False:
		return subs
	else:
		esubs = []
		for sub in subs:
			if hasattr(sub, 'rules'):
				if sub.rules != None:
					sub.new_rules = pseudo_markup(sub.rules)

			if hasattr(sub, 'rules'):
				if sub.rules != None:
					sub.new_rules = pseudo_markup(sub.rules)

			sub.posts = sub.get_posts(count=True)

			if sub.posts == 0:
				continue

			sub.comments = sub.get_comments(count=True)
			#sub.comments = anon_block(sub.comments)

			sub.score = sub.comments + sub.posts

			esubs.append(sub)

		esubs.sort(key=lambda x: x.score, reverse=True)
		return esubs


@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_pgp_from_username(username):
	u = normalize_username(username)
	if u == False:
		return False

	else:
		pgp = db.session.query(Pgp).filter_by(username=normalize_username(username)).first()
	
	if pgp != None:
		return pgp
	return False

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_user_from_name(username):
	if username == '' or username == False or username == None:
		return False
	return normalize_username(username, dbuser=True)

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_user_from_id(uid):
	if uid == None or uid == False:
		return False
	return db.session.query(Iuser).filter_by(id=uid).first()

@app.route('/login/',  methods=['GET', 'POST'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def login():
	if request.method == 'GET':
		return render_template('login.html')
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		if config.CAPTCHA_ENABLE and config.CAPTCHA_LOGIN:
			if request.form.get('captcha') == '':
				flash('no captcha', 'danger')
				return redirect(url_for('login'))
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
				if login_user.admin:
						session['admin'] = login_user.admin

				session['hide_sub_style'] = login_user.hide_sub_style

				if hasattr(login_user, 'anonymous'):
					if login_user.anonymous:
						session['anonymous'] = True
				session['darkmode'] = login_user.darkmode

				if get_pgp_from_username(login_user.username):
					session['pgp_enabled'] = True


				return redirect(url_for('index'), 302)

		flash('Username or Password incorrect.', 'danger')
		return redirect(url_for('login'), 302)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
	[session.pop(key) for key in list(session.keys())]

	return redirect(url_for('index'), 302)

@app.route('/register', methods=['POST'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def register():
	if request.method == 'POST':
		if config.CAPTCHA_ENABLE and config.CAPTCHA_REGISTER:
			if request.form.get('captcha') == '':
				flash('no captcha', 'danger')
				return redirect(url_for('register'))

			if captcha.validate() == False:
				flash('invalid captcha', 'danger')
				return redirect(url_for('login'))
		username = request.form.get('username')
		password = request.form.get('password')
		email = request.form.get('email')

		if 'username' in session:
			flash('already logged in', 'danger')
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

		if len(password) > 100 or len(password) < 1:
			flash('password length invalid', 'danger')
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

		#cache.clear()

		return redirect(config.URL, 302)

@app.route('/')
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def index():
	return subi(subi='all', nsfw=False)

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def is_sub_nsfw(sub):
	s = db.session.query(Sub).filter_by(name=sub).first()
	if s.nsfw:
		return True
	return False

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_subi(subi, user_id=None, posts_only=False, deleted=False, offset=0, limit=15, nsfw=True, d=None, s=None):
	if offset != None:
		offset = int(offset)


	muted_subs = False

	if subi != 'all':
		subname = db.session.query(Sub).filter(func.lower(Sub.name) == subi.lower()).first()
		if subname == None:
			return {'error':'sub does not exist'}
		subi = subname.name
		posts = db.session.query(Post).filter_by(sub=subi, deleted=False)
	elif user_id != None:
		muted_subs = get_muted_subs()
		posts = db.session.query(Post).filter_by(author_id=user_id, deleted=False)
	else:
		muted_subs = get_muted_subs()
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
		posts = posts.all()
	elif s == 'new':
		posts = posts.order_by((Post.created).desc())
		posts = posts.all()
	else:
		posts = posts.all()
		for p in posts:
			p.hot = hot(p.ups, p.downs, p.created)
		posts.sort(key=lambda x: x.hot, reverse=True)
	#posts = [post for post in posts if post.created > ago]
	

	if muted_subs:
		posts = [c for c in posts if c.sub not in muted_subs]	

	if nsfw == False:
		posts = [p for p in posts if p.nsfw == False]

	more = False
	pc = len(posts)
	if pc > limit:
		more = True

	try:
		offset + 1
	except:
		offset = 0



	if 'blocked_subs' in session and 'username' in session:
		posts = [c for c in posts if c.sub not in session['blocked_subs']]

	if 'blocked' in session:
		posts = [post for post in posts if post.id not in session['blocked']['post_id']]
		posts = anon_block(posts)
		posts = [post for post in posts if post.noblock == True]

	posts = posts[offset:offset+limit]

	stid = False
	for p in posts:
		if p.stickied == True:
			stid = p.id

	if subi != 'all':
		if stid:
			posts = [post for post in posts if post.id != stid]

	if subi != 'all':
		sticky = db.session.query(Post).filter(func.lower(Post.sub) == subi.lower(), Post.stickied == True).first()
		if sticky:
			if 'blocked_subs' in session:
				if sticky.sub in session['blocked_subs']:
					pass
				else:
					posts.insert(0, sticky)
			else:
				posts.insert(0, sticky)


	if more and len(posts) > 0:
		posts[len(posts)-1].more = True

	p = []
	for post in posts:
		if is_sub_nsfw(post.sub):
			post.sub_nsfw = True
		else:
			post.sub_nsfw = False

		if hasattr(post, 'text'):
			post.new_text = pseudo_markup(post.text)
		if thumb_exists(post.id):
			post.thumbnail = 'thumbnails/thumb-' + str(post.id) + '.PNG'


		if get_youtube_vid_id(post.url):
			post.video = 'https://www.youtube.com/embed/%s?version=3&enablejsapi=1' % get_youtube_vid_id(post.url)

		post.mods = get_sub_mods(post.sub)
		post.created_ago = time_ago(post.created)
		if subi != 'all':
			post.site_url = config.URL + '/i/' + subi + '/' + str(post.id) + '/' + post.inurl_title
		post.remote_url_parsed = post_url_parse(post.url)
		post.comment_count = db.session.query(Comment).filter_by(post_id=post.id).count()
		if 'user_id' in session and 'username' in session:

			v = post.has_voted(session['user_id'])
			if v != None:
				post.has_voted = v.vote

			if db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']), Moderator.sub.like(post.sub)).exists()).scalar():
				post.is_mod = True
		p.append(post)
	return p

@app.route('/i/<subi>/')
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def subi(subi, user_id=None, posts_only=False, offset=0, limit=15, nsfw=True, show_top=True, s=None, d=None):
	offset = request.args.get('offset')
	d = request.args.get('d')
	s = request.args.get('s')
	subi = normalize_sub(subi)

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


	session['top_url'] = re.sub('[&\?]?s=\w+', '', request.url) + '&s=top'
	session['new_url'] = re.sub('[&\?]?s=\w+', '', request.url) + '&s=new'
	session['hot_url'] = re.sub('[&\?]?s=\w+', '', request.url) + '&s=hot'

	session['hour_url'] = re.sub('[&\?]?d=\w+', '', request.url) + '&d=hour'
	session['day_url'] = re.sub('[&\?]?d=\w+', '', request.url) + '&d=day'
	session['week_url'] = re.sub('[&\?]?d=\w+', '', request.url) + '&d=week'
	session['month_url'] = re.sub('[&\?]?d=\w+', '', request.url) + '&d=month'

	for a in ['top_url', 'new_url', 'day_url', 'week_url', 'hour_url', 'month_url', 'hot_url']:
		if session[a].find('/&') != -1:
			session[a] = session[a].replace('/&', '/?')

	if 'prev_off_url' in session:
		if session['prev_off_url']:
			if session['prev_off_url'].find('/&'):
				session['prev_off_url'] = session['prev_off_url'].replace('/&', '/?')

	sub_posts = get_subi(subi=subi, user_id=user_id, posts_only=posts_only, deleted=False, offset=offset, limit=15, d=d, s=s, nsfw=nsfw)
	if type(sub_posts) == dict:
		if 'error' in sub_posts.keys():
			flash(sub_posts['error'], 'danger')
			return redirect('/')

	for p in sub_posts:
		if hasattr(p, 'self_text'):
			if p.self_text != None:
				p.new_self_text = pseudo_markup(p.self_text)


	if posts_only:
		return sub_posts

	sub_stats = get_top_stats(subi)

	return render_template('sub.html', posts=sub_posts, url=config.URL, sub_stats=sub_stats)


@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_cached_children(comment, deleted=False):
	return comment.get_children(deleted=deleted)

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def recursive_children(comment=None, current_depth=0, max_depth=8, deleted=False):
	found_children = []
	found_children.append(comment)
	children = comment.get_children(deleted=deleted).all()

	while len(children) > 0 and current_depth < max_depth :
		for c in children:
			if c not in found_children:
				found_children.append(c)
				c2 = c.get_children(deleted=deleted).all()
				if c2 != None:
					[children.append(c3) for c3 in c2]
			ex = [x for x in children if x != c]
		children = ex
		current_depth += 1

	return found_children

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def c_get_comments(sub=None, post_id=None, inurl_title=None, comment_id=False, sort_by=None, comments_only=False, user_id=None, deleted=False):
	post = None
	parent_comment = None
	if not comments_only:
		if post_id != None:
			post = db.session.query(Post).filter_by(id=post_id).first()
			post.mods = get_sub_mods(post.sub)
			post.comment_count = db.session.query(Comment).filter_by(post_id=post.id).count()
			post.created_ago = time_ago(post.created)
			post.remote_url_parsed = post_url_parse(post.url)

			if is_sub_nsfw(post.sub):
				post.sub_nsfw = True
			else:
				post.sub_nsfw = False
			if hasattr(post, 'text'):
				post.new_text = pseudo_markup(post.text)
			
			if thumb_exists(post.id):
				post.thumbnail = 'thumbnails/thumb-' + str(post.id) + '.PNG'
			elif hasattr(post, 'url'):
				post.thumbnail = 'globe.png'


			if hasattr(post, 'self_text'):
				if post.self_text != None:
					post.new_self_text = pseudo_markup(post.self_text)

			if get_youtube_vid_id(post.url):
				post.video = 'https://www.youtube.com/embed/%s?version=3&enablejsapi=1' % get_youtube_vid_id(post.url)

		else:
			post = None

		if 'user_id' in session:
			post.has_voted = db.session.query(Vote).filter_by(post_id=post.id, user_id=session['user_id']).first()
			if post.has_voted != None:
				post.has_voted = post.has_voted.vote	

		if comment_id == None:
			comments = db.session.query(Comment).filter_by(post_id=post_id, deleted=deleted).all()
			show_blocked = False
		
		else:
			comments = []
			parent_comment = db.session.query(Comment).filter_by(id=comment_id).first()
			show_blocked = False

			# if direct link, just show it 
			if parent_comment.id in session['blocked']['comment_id'] or parent_comment.author_id in session['blocked']['other_user']:
				flash('you are viewing a comment you have blocked', 'danger')
				show_blocked = True

			comments = recursive_children(comment=parent_comment, deleted=True)
			
	else:
		comments = db.session.query(Comment).filter(Comment.author_id == user_id,
			Comment.deleted == deleted).order_by(Comment.created.desc()).all()
		show_blocked = False



	if 'blocked_subs' in session and 'username' in session:
		comments = [c for c in comments if c.sub_name not in session['blocked_subs']]

	if 'blocked' in session and show_blocked != True:
		comments = [c for c in comments if c.id not in session['blocked']['comment_id']]
		comments = anon_block(comments)

		comments = [c for c in comments if c.noblock == True]

	#print(comments)
	for c in comments:
		c.score = (c.ups - c.downs)
		c.new_text = pseudo_markup(c.text)
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

@app.route('/i/<sub>/<post_id>/<inurl_title>/<comment_id>/sort-<sort_by>')
@app.route('/i/<sub>/<post_id>/<inurl_title>/<comment_id>/')
@app.route('/i/<sub>/<post_id>/<inurl_title>/sort-<sort_by>')
@app.route('/i/<sub>/<post_id>/<inurl_title>/')
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_comments(sub=None, post_id=None, inurl_title=None, comment_id=None, sort_by=None, comments_only=False, user_id=None):
	try:
		if sub == None or post_id == None or inurl_title == None:
			if not comments_only:
				return 'badlink'

		sub = normalize_sub(sub)

		if comment_id == None:
			is_parent = False
		else:
			is_parent = True

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

		last = '%s/i/%s/%s/%s/' % (config.URL, sub, post_id, post.inurl_title)

		if comment_id != False and comment_id != None:
			last = last + str(comment_id)

		session['last_return_url'] = last

		return render_template('comments.html', comments=comments, post_id=post_id, 
			post_url='%s/i/%s/%s/%s/' % (config.URL, sub, post_id, post.inurl_title), 
			post=post, tree=tree, parent_comment=parent_comment, is_parent=is_parent,
			config=config)
	except Exception as e:
		print(str(e))
		return(str(e))
		db.session.rollback()




# need to entirely rewrite how comments are handled once everything else is complete
# this sort of recursion KILLS performance, especially when combined with the already
# terrible comment_structure function.

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
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
	return comments

@app.route('/create', methods=['POST', 'GET'])
@notbanned
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def create_sub():
	if request.method == 'POST':
		subname = request.form.get('subname')
		if subname.lower() == 'all':
			flash('reserved name')
			return redirect(url_for('create_sub'))

		if config.CAPTCHA_ENABLE and config.CAPTCHA_CREATE:
			if request.form.get('captcha') == '':
				flash('no captcha', 'danger')
				return redirect(url_for('create_sub'))

			if captcha.validate() == False:
				flash('invalid captcha', 'danger')
				return redirect(url_for('create_sub'))
			if 'rate_limit' in session and config.RATE_LIMIT == True:
				rl = session['rate_limit'] - time.time()
				if rl > 0:
					flash('rate limited, try again in %s seconds' % str(rl), 'danger')
					return redirect('/')

		if subname != None and verify_subname(subname) and 'username' in session:
			if len(subname) > 30 or len(subname) < 1:
				return 'invalid length'

			already = db.session.query(Sub).filter(func.lower(Sub.name) == subname.lower()).first()
			if already != None:
				flash('sub already exists', 'danger')
				return redirect('/create')

			title = request.form.get('title')
			new_sub = Sub(name=escape(subname), created_by=session['username'], created_by_id=session['user_id'], title=escape(title))
			db.session.add(new_sub)
			db.session.commit()
			new_mod = Moderator(username=new_sub.created_by, sub=new_sub.name)
			db.session.add(new_mod)
			db.session.commit()


			set_rate_limit()
			flash('You have created a new sub! Mod actions are under the "info" tab.', 'success')
			return redirect(config.URL + '/i/' + subname, 302)

		if verify_subname(subname) == False:
			flash('Invalid sub name. Valid Characters are A-Z 1-9 - _ ')
			return(redirect(config.URL + '/create'))
		return 'invalid'
	elif request.method == 'GET':
		if 'username' not in session:
			flash('please log in to create subs', 'danger')
			return redirect(url_for('login'))
		return render_template('create.html')

@app.route('/u/<username>/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def view_user(username):
	vuser = db.session.query(Iuser).filter(func.lower(Iuser.username) == func.lower(username)).first()
	mod_of = db.session.query(Moderator).filter_by(username=vuser.username).all()
	mods = {}
	for s in mod_of:
		mods[s.sub] = s.rank
	vuser.mods = mods

	posts = vuser.get_recent_posts()#.all()
	comments = vuser.get_recent_comments()#.all()

	for p in posts:
		p.created_ago = time_ago(p.created)
		p.comment_count = db.session.query(Comment).filter_by(post_id=p.id).count()
		p.mods = get_sub_mods(p.sub)
		if 'user_id' in session:
			v = p.has_voted(session['user_id'])
			if v != None:
				p.has_voted = str(v.vote)
		if p.self_text != None:
			p.new_self_text = pseudo_markup(p.self_text)

		p.remote_url_parsed = post_url_parse(p.url)

		if hasattr(p, 'text'):
			p.new_text = pseudo_markup(p.text)
		if thumb_exists(p.id):
			p.thumbnail = 'thumbnails/thumb-' + str(p.id) + '.PNG'

	comments_with_posts = []

	for c in comments:
		c.mods = get_sub_mods(c.sub_name)
		cpost = db.session.query(Post).filter_by(id=c.post_id).first()
		comments_with_posts.append((c, cpost))

		c.new_text = pseudo_markup(c.text)
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

	return render_template('user.html', vuser=vuser, posts=posts, url=config.URL, comments_with_posts=comments_with_posts, userpage=True)

@limiter.limit('25 per minute')
@app.route('/vote', methods=['GET', 'POST'])
def vote(post_id=None, comment_id=None, vote=None, user_id=None):
	if request.method == 'POST':
		if post_id == None:
			post_id = request.form.get('post_id')
		if comment_id == None:
			comment_id = request.form.get('comment_id')
		if vote == None:
			vote = request.form.get('vote')
		else:
			vote = str(vote)
	
		if 'username' not in session or 'user_id' not in session:
			return 'not logged in'
		elif user_id == None:
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



		if vote == 0:
			if last_vote.post_id != None:
				if last_vote.post_id != None:
					vpost = db.session.query(Post).filter_by(id=last_vote.post_id).first()
				elif last_vote.comment_id != None:
					vpost = db.session.query(Comment).filter_by(id=last_vote.comment_id).first()
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
@notbanned
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def create_post(postsub=None):
	if 'previous_post_form' not in session:
		session['previous_post_form'] = None

	if request.method == 'POST':
		title = request.form.get('title')
		url = request.form.get('url')
		sub = request.form.get('sub')
		#if db.session.query(db.session.query(Iuser).filter(func.lower(Iuser.username) == func.lower(username)).exists()).scalar():
		self_post_text = request.form.get('self_post_text')

		session['previous_post_form'] = {'title':title, 'url':url, 'sub':sub, 'self_post_text':self_post_text}

		anonymous = request.form.get('anonymous')

		show_captcha = True

		api = get_api_key(session['username'])
		if api != None:
			show_captcha = False

		if config.CAPTCHA_ENABLE and config.CAPTCHA_POSTS and show_captcha:
			if request.form.get('captcha') == '':
				flash('no captcha', 'danger')
				return redirect(url_for('create_post'))
			if captcha.validate() == False:
				flash('invalid captcha', 'danger')
				return redirect(url_for('create_post'))
			if 'rate_limit' in session and config.RATE_LIMIT == True:
				rl = session['rate_limit'] - time.time()
				if rl > 0:
					flash('rate limited, try again in %s seconds' % str(rl))
					return redirect('/')

		sub = db.session.query(Sub).filter(func.lower(Sub.name) == func.lower(sub)).first()
		if sub == None:
			flash('sub does not exist', 'danger')
			return redirect('/create_post')

		if sub.nsfw:
			nsfw = True
		else:
			nsfw = False

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

		deleted = False
		if sub in get_banned_subs(session['username']):
			deleted = True

		if post_type == 'url':
			if len(url) > 2000 or len(url) < 1:
				flash('invalid url length', 'danger')
				return redirect(url_for('create_post'))

			prot = re.findall('^https?:\/\/', url)
			if len(prot) != 1:
				url = 'https://' + url
			new_post = Post(url=url, title=title, inurl_title=convert_ied(title), author=session['username'],
						author_id=session['user_id'], sub=sub, post_type=post_type, anonymous=anonymous, nsfw=nsfw,
						deleted=deleted)

		elif post_type == 'self_post':
			if len(self_post_text) < 1 or len(self_post_text) > 20000:
				flash('invalid self post length', 'danger')
				return redirect(url_for('create_post'))
			new_post = Post(self_text=self_post_text, title=title, inurl_title=convert_ied(title),
				author=session['username'], author_id=session['user_id'], sub=sub, post_type=post_type, anonymous=anonymous, nsfw=nsfw,
				deleted=deleted)

		db.session.add(new_post)
		db.session.commit()
		

		if post_type == 'url':
			#os.system('python3 get_thumbnail.py %s "%s"' % (str(new_post.id), urllib.parse.quote(url)))
			#call(['python3', 'get_thumbnail.py', str(new_post.id), urllib.parse.quote(url)])
			_thread.start_new_thread(os.system, ('python3 utilities/get_thumbnail.py %s "%s"' % (str(new_post.id), urllib.parse.quote(url)),))

		new_post.permalink = config.URL + '/i/' + new_post.sub + '/' + str(new_post.id) + '/' + new_post.inurl_title +  '/'
		if is_admin(session['username']) and anonymous == False:
			new_post.author_type = 'admin'
		elif is_mod(new_post, session['username']) and anonymous == False:
			new_post.author_type = 'mod'

		db.session.commit()
		

		url = new_post.permalink
		set_rate_limit()

		new_vote = Vote(post_id=new_post.id, vote=1, user_id=session['user_id'], comment_id=None)
		db.session.add(new_vote)

		new_post.ups += 1

		db.session.add(new_post)
		db.session.commit()



		if 'previous_post_form' in session:
			session['previous_post_form'] = None
		return redirect(url)

	if request.method == 'GET':
		if 'username' not in session:
			flash('please log in to create new posts', 'danger')
			return redirect(url_for('login'))
		if request.referrer:
			subref = re.findall('\/i\/([a-zA-z1-9-_]*)', request.referrer)
		if 'subref' in locals():
			if len(subref) == 1:
				if len(subref[0]) > 0:
					postsub = subref[0]
		
		sppf = session['previous_post_form']
		session['previous_post_form'] = None
		return render_template('create_post.html', postsub=postsub, sppf=sppf)

@app.route('/get_sub_list', methods=['GET'])
def get_sub_list():
	subs = get_all_subs()
	if subs != None:
		for s in subs:
			s.comments = s.get_comments()
			s.posts = s.get_posts()
			if s.comments != None and s.posts != None:
				s.rank = s.comments.count() + s.posts.count()
			else:
				s.rank = 0
		subs = [s for s in subs]
		subs.sort(key=lambda x: x.rank, reverse=True)
		sublinks = []
		for s in subs:
			sublinks.append('<a class="dropdown-item sublist-dropdown"' +
			' href="javascript:setSub(\'%s\')">/i/%s</a>' % (s.name, s.name))
		return '\n'.join(sublinks)
	else:
		return ''


@limiter.limit('1 per second')
@limiter.limit('10 per minute')
@app.route('/create_comment', methods=['POST'])
@notbanned
def create_comment():
	text = request.form.get('comment_text')
	post_id = request.form.get('post_id')
	post_url = request.form.get('post_url')
	parent_id = request.form.get('parent_id')
	sub_name = request.form.get('sub_name')
	anonymous = request.form.get('anonymous')

	show_captcha = True

	api = get_api_key(session['username'])
	if api != None:
		show_captcha = False

	if config.CAPTCHA_ENABLE and config.CAPTCHA_COMMENTS and show_captcha:
		if request.form.get('captcha') == '':
			flash('no captcha', 'danger')
			if 'last_return_url' in session:
				return redirect(session['last_return_url'])
			return redirect('/')

		if captcha.validate() == False:
			flash('invalid captcha', 'danger')
			if 'last_return_url' in session:
				return redirect(session['last_return_url'])
			return redirect('/')


		if 'rate_limit' in session and config.RATE_LIMIT == True:
			rl = session['rate_limit'] - time.time()
			if rl > 0:
				flash('rate limited, try again in %s seconds' % str(rl), 'danger')
				if 'last_return_url' in session:
					return redirect(session['last_return_url'])
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
		flash('post is locked', 'danger')
		return redirect(post.get_permalink())

	deleted = False
	sub = normalize_sub(sub_name)
	if sub in get_banned_subs(session['username']):
		deleted = True
		#flash('you are banned from commenting', 'danger')
		#return redirect(post.get_permalink())
	sub_name = sub

	new_comment = Comment(post_id=post_id, sub_name = sub_name, text=text,
		author=session['username'], author_id=session['user_id'], parent_id=parent_id, level=level,
		anonymous=anonymous, deleted=deleted)
	db.session.add(new_comment)
	db.session.commit()
	
	new_comment.permalink = post.get_permalink() +  str(new_comment.id)

	if is_admin(session['username']) and anonymous == False:
		new_comment.author_type = 'admin'
	elif is_mod(post.sub, session['username']) and anonymous == False:
		new_comment.author_type = 'mod'
	else:
		new_comment.author_type = 'user'

	db.session.commit()
	

	new_vote = Vote(comment_id=new_comment.id, vote=1, user_id=session['user_id'], post_id=None)
	db.session.add(new_vote)

	new_comment.ups += 1
	db.session.add(new_comment)

	db.session.commit()
	

	sender = new_comment.author

	if new_comment.parent_id and not deleted:
		cparent = db.session.query(Comment).filter_by(id=new_comment.parent_id).first()
		if cparent.author != session['username']:
			new_message = Message(title='comment reply', text=new_comment.text, sender=sender, sender_type=new_comment.author_type,
				sent_to=cparent.author, in_reply_to=new_comment.permalink, anonymous=anonymous)
			db.session.add(new_message)
			db.session.commit()
	else:
		if not deleted:
			if post.author != session['username']:
				new_message = Message(title='comment reply', text=new_comment.text, sender=sender, sender_type=new_comment.author_type,
					sent_to=post.author, in_reply_to=post.get_permalink(), anonymous=anonymous)
				db.session.add(new_message)
				db.session.commit()

	set_rate_limit()

	flash('created new comment', 'success')
	return redirect(post_url, 302)

def send_message(title=None, text=None, sent_to=None, sender=None, in_reply_to=None, encrypted=False, encrypted_key_id=None):
	new_message = Message(title=title, text=text, sent_to=sent_to, sender=sender,
		in_reply_to=in_reply_to, encrypted=encrypted, encrypted_key_id=encrypted_key_id)
	db.session.add(new_message)
	db.session.commit()


@app.route('/u/<username>/messages/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def user_messages(username=None):
	if 'username' not in session or username == None:
		flash('not logged in', 'danger')
		return redirect(url_for('login'))
	else:
		if session['username'] != username:
			flash('you are not that user', 'danger')
			return redirect('/')
		else:
			has_encrypted = False

			read = db.session.query(Message).filter_by(sent_to=username, read=True)
			unread = db.session.query(Message).filter_by(sent_to=username, read=False)
			read = read.order_by((Message.created).desc()).limit(50).all()
			unread = unread.order_by((Message.created).desc()).limit(50).all()

			read = [x for x in read if x.sender == None or get_user_from_name(x.sender).id not in session['blocked']['other_user']]
			unread = [x for x in unread if x.sender == None or get_user_from_name(x.sender).id not in session['blocked']['other_user']]

			for r in unread:
				r.read = True

			sent = db.session.query(Message).filter_by(sender=username, read=False)
			sent = sent.order_by((Message.created).desc()).limit(5).all()

			for s in sent:
				s.is_sent = True
				if s.encrypted:
					s.new_text = '<p style="color: green;">ENCRYPTED</p>'

			for r in read:
				if r.encrypted == False:
					r.new_text = pseudo_markup(r.text)
				else:
					r.sender_pgp = get_pgp_from_username(r.sender)
					r.new_text = pseudo_markup(r.text, escape_only=True)
				if r.in_reply_to != None:
					r.ppath = r.in_reply_to.replace(config.URL, '')
				if r.encrypted == True:
					has_encrypted = True
			
			session['has_messages'] = False
			session['unread_messages'] = None
			
			db.session.commit()

			for r in unread:
				if r.encrypted == False:
					r.new_text = pseudo_markup(r.text)
				else:
					r.sender_pgp = get_pgp_from_username(r.sender)
					r.new_text = pseudo_markup(r.text, escape_only=True)
				if r.in_reply_to != None:
					r.ppath = r.in_reply_to.replace(config.URL, '')
				if r.encrypted == True:
					has_encrypted = True

			if 'pgp_enabled' in session:
				self_pgp = get_pgp_from_username(session['username'])
			else:
				self_pgp = False

			return render_template('messages.html', read=read, unread=unread, has_encrypted=has_encrypted, self_pgp=self_pgp,
				sent=sent)

@app.route('/u/<username>/messages/reply/<mid>', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def reply_message(username=None, mid=None):
	if 'username' not in session or username == None:
		flash('not logged in', 'danger')
		return redirect(url_for('login'))
	if session['username'] != username:
		flash('you are not that user', 'danger')
		return redirect('/')

	m = db.session.query(Message).filter_by(sent_to=username, id=mid).first()
	if m == None:
		flash('invalid message id', 'danger')
		return redirect('/')
	else:
		m.new_text = pseudo_markup(m.text)
		if hasattr(m, 'in_reply_to'):
			if m.in_reply_to != None:
				m.ppath = m.in_reply_to.replace(config.URL, '')


		return render_template('message_reply.html', message=m, sendto=False, self_pgp=get_pgp_from_username(session['username']),
			other_pgp=get_pgp_from_username(m.sender), other_user=get_user_from_name(username))


def sendmsg(title=None, text=None, sender=None, sent_to=None, encrypted=False, encrypted_key_id=None, in_reply_to=None):
	new_message = Message(title=title, text=text, sender=sender, in_reply_to=in_reply_to, sent_to=sent_to, encrypted=encrypted, 
		encrypted_key_id=encrypted_key_id)
	db.session.add(new_message)
	db.session.commit()

@app.route('/message/', methods=['GET', 'POST'])
@app.route('/message/<username>', methods=['GET', 'POST'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def msg(username=None):
	if 'username' not in session:
		flash('not logged in', 'danger')
		return redirect(url_for('login'))
	if request.method == 'POST':
		text = request.form.get('message_text')
		title = request.form.get('message_title')
		sent_to = request.form.get('sent_to')
		encrypted = request.form.get('msgencrypted')
		encrypted_key_id = request.form.get('key_id')

		if encrypted == 'true':
			encrypted = True
			encrypted_key_id = encrypted_key_id
		else:
			encrypted = False
			encrypted_key_id = None

		if encrypted_key_id == '':
			encrypted_key_id = None

		if sent_to == None:
			sent_to = username

		if 'rate_limit' in session and config.RATE_LIMIT == True:
			rl = session['rate_limit'] - time.time()
			if rl > 0:
				flash('rate limited, try again in %s seconds' % str(rl))
				return redirect('/')

		if len(text) > 20000 or len(title) > 200:
			flash('text/title too long')
			return redirect('/message/')

		if str(sent_to) == 'None':
			flash('this user is not valid', 'danger')
			return redirect('/message/')

		sender = session['username']

		sendmsg(title=title, text=text, sender=session['username'], sent_to=sent_to, encrypted=encrypted,
			encrypted_key_id=encrypted_key_id)
		

		set_rate_limit()
		flash('sent message', category='success')
		return redirect(url_for('msg'))

	if request.method == 'GET':
		if username != None:
			if len(str(username)) < 1:
				flash('invalid username')
				return redirect('/')
		if request.referrer:
			ru = re.findall('\/i\/([a-zA-z1-9-_]*)', request.referrer)
			if ru != None:
				if len(ru) == 1:
					if len(ru[0]) > 0:
						username = ru[0]
		return render_template('message_reply.html', sendto=username, message=None, other_pgp=get_pgp_from_username(username),
								other_user=get_user_from_name(username), self_pgp=get_pgp_from_username(session['username']))


@app.route('/i/<sub>/mods/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def submods(sub=None):
	sub = normalize_sub(sub)
	modactions = db.session.query(Mod_action).filter_by(sub=sub).limit(5).all()
	if type(modactions) != None:
		modactions = [m for m in modactions]
	return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), modactions=modactions)

@app.route('/i/<sub>/actions/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def subactions(sub=None):
	sub = normalize_sub(sub)
	modactions = db.session.query(Mod_action).filter_by(sub=sub).all()
	if type(modactions) != None:
		modactions = [m for m in modactions]
	return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), modactions=modactions, allactions=True)


@app.route('/i/<sub>/mods/banned/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def bannedusers(sub=None):
	sub = normalize_sub(sub)
	banned = db.session.query(Ban).filter_by(sub=sub).all()
	if type(banned) != None:
		banned = [b for b in banned]
	else:
		banned = []
	return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), banned=banned)

@app.route('/i/<sub>/mods/add/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def addmod(sub=None):
	sub = normalize_sub(sub)
	if hasattr(request, 'is_mod'):
		if request.is_mod:
			return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), addmod=True)
	return abort(403)

@app.route('/i/<sub>/mods/remove/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def removemod(sub=None):
	sub = normalize_sub(sub)
	if hasattr(request, 'is_mod'):
		if request.is_mod:
			return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), addmod=True)
	return abort(403)

@app.route('/i/<sub>/info/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def description(sub=None):
	sub = normalize_sub(sub)
	subr = db.session.query(Sub).filter_by(name=sub).first()
	if hasattr(subr, 'rules') == False:
		rtext = False
	else:
		if subr.rules != None:
			rtext = pseudo_markup(subr.rules)
		else:
			rtext = False
	return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), desc=True, rules=Markup(rtext))

@app.route('/i/<sub>/settings/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def settings(sub=None):
	sub = normalize_sub(sub)
	subr = db.session.query(Sub).filter_by(name=sub).first()
	if request.is_mod:
		return render_template('sub_mods.html', mods=get_sub_mods(sub, admin=False), settings=True, nsfw=subr.nsfw, sub_object=subr)
	return abort(403)

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_blocked_subs(username=None):
	subs = db.session.query(Sub_block).filter_by(username=session['username']).all()
	if subs != None:
		return [s.sub for s in subs]
	else:
		return []

@app.route('/i/<sub>/block', methods=['POST'])
def blocksub(sub=None):
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))
	if sub == None:
		return abort(500)

	blocks = db.session.query(Sub_block).filter_by(username=session['username']).all()
	if blocks != None:
		bsubs = [b.sub for b in blocks]
	else:
		bsubs = []

	#cache.clear()

	if blocks == None or sub not in bsubs:
		session['blocked_subs'].append(sub)
		new_block = Sub_block(username=session['username'], sub=sub)
		db.session.add(new_block)
		db.session.commit()
		bsubs.append(sub)
		flash('unsubscribed from %s' % sub, 'success')
	else:
		dblock = db.session.query(Sub_block).filter_by(username=session['username'], sub=sub).first()
		db.session.delete(dblock)
		db.session.commit()
		bsubs = [b for b in bsubs if b != sub]
		flash('subscribed to %s' % sub, 'success')

	session['blocked_subs'] = bsubs

	return redirect('/i/%s/' % sub)

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def explore_stats(sub):
	if hasattr(sub, 'rules'):
		if sub.rules != None:
			sub.new_rules = pseudo_markup(sub.rules)
	sub.posts = sub.get_posts(count=True)

	sub.comments = sub.get_comments(count=True)
	sub.score = sub.comments + sub.posts
	sub.users = len(sub.get_total_users())
	return sub


@app.route('/explore/', methods=['GET'])
def explore():
	esubs = []
	subs = get_all_subs(explore=True)
	for sub in subs:
		new_sub = explore_stats(sub)
		if new_sub.posts > 0:
			esubs.append(new_sub)

	esubs.sort(key=lambda x: x.users, reverse=True)

	return render_template('explore.html', subs=esubs)

@app.route('/clear_cache', methods=['GET'])
def clear_cache():
	#return str(vars(remote_addr))
	if request.remote_addr == '127.0.0.1':
		#cache.clear()
		return 'cleared'

@app.route('/about/', methods=['GET'])
@app.route('/readme/', methods=['GET'])
@app.route('/news/2019/10/21/ieddit-beta-release/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def about():
	from markdown import markdown
	with open('../README.md') as r:
		return render_template('about.html', about=markdown(r.read()))


@app.route('/comments/', methods=['GET'])
@app.route('/i/<sub>/comments/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def subcomments(sub=None, offset=0, limit=15, s=None):
	# code is copy pasted from user page... the post stuff can probably be gotten rid of.
	# the username stuff can be gotten rid of too
	mods = {}

	offset = request.args.get('offset')
	if offset == None:
		offset = 0

	offset = int(offset)

	s = request.args.get('s')
	if s == None:
		s = 'new'

	muted_subs = False

	if sub == 'all':
		posts = subi('all', posts_only=True, nsfw=True)
		muted_subs = get_muted_subs()
		posts = [p for p in posts if p.sub not in muted_subs]	
	elif sub != None:
		posts = subi(sub, posts_only=True)
	else:
		posts = subi('all', posts_only=True, nsfw=False)
		muted_subs = get_muted_subs()
		posts = [p for p in posts if p.sub not in muted_subs]	


	posts = posts[offset:offset+limit]

	for p in posts:
		p.mods = get_sub_mods(p.sub)

	comments_with_posts = []

	if sub == None:
		sub = 'all'

	if sub == 'all':
		comments = db.session.query(Comment)
		comcount = db.session.query(Comment).count()
	else:
		comments = db.session.query(Comment).filter_by(sub_name=normalize_sub(sub))
		comcount = comments.count()


	if comcount <= offset:
		more = comcount
	


	if s == 'top':
		comments = comments.order_by((Comment.ups - Comment.downs).desc())
		comments = comments.offset(offset).limit(limit).all()
	elif s == 'new':
		comments = comments.order_by((Comment.created).desc())
		comments = comments.offset(offset).limit(limit).all()
	else:
		comments = comments.offset(offset).limit(limit).all()

	comments = [c for c in comments if c.id not in session['blocked']['comment_id']]

	if muted_subs:
		comments = [c for c in comments if c.sub_name not in muted_subs]

	comments = anon_block(comments)
	comments = [c for c in comments if c.noblock == True]

	for c in comments:
		c.new_text = pseudo_markup(c.text)
		c.mods = get_sub_mods(c.sub_name)
		cpost = db.session.query(Post).filter_by(id=c.post_id).first()
		comments_with_posts.append((c, cpost))
		c.hot = hot(c.ups, c.downs, c.created)
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




	if request.environ['QUERY_STRING'] == '':
		session['off_url'] = request.url + '?offset=15'
		session['prev_off_url'] = request.url
	else:
		if offset == None:
			session['off_url'] = request.url + '&offset=15'
			session['prev_off_url'] = request.url
		else:
			offset = str(offset)

			if (int(offset) - 15) > 0:
				session['prev_off_url'] = request.url.replace('offset=' + offset, 'offset=' + str(int(offset) -15))
			else:
				session['prev_off_url'] = re.sub('[&\?]?offset=(\d+)', '', request.url)
			session['off_url'] = request.url.replace('offset=' + offset, 'offset=' + str(int(offset) +15))
	if request.url.find('offset=') == -1:
		session['off_url'] = request.url + '&offset=15'
		session['prev_off_url'] = False

	session['top_url'] = re.sub('[&\?]?s=\w+', '', request.url) + '&s=top'
	session['new_url'] = re.sub('[&\?]?s=\w+', '', request.url) + '&s=new'
	session['hot_url'] = re.sub('[&\?]?s=\w+', '', request.url) + '&s=hot'

	session['hour_url'] = re.sub('[&\?]?d=\w+', '', request.url) + '&d=hour'
	session['day_url'] = re.sub('[&\?]?d=\w+', '', request.url) + '&d=day'
	session['week_url'] = re.sub('[&\?]?d=\w+', '', request.url) + '&d=week'
	session['month_url'] = re.sub('[&\?]?d=\w+', '', request.url) + '&d=month'

	for a in ['top_url', 'new_url', 'day_url', 'week_url', 'hour_url', 'month_url', 'hot_url']:
		if session[a].find('/&') != -1:
			session[a] = session[a].replace('/&', '/?')

	if 'prev_off_url' in session:
		if session['prev_off_url']:
			if session['prev_off_url'].find('/&'):
				session['prev_off_url'] = session['prev_off_url'].replace('/&', '/?')

	if 'off_url' in session:
		if session['off_url']:
			session['off_url'] = session['off_url'].replace('/&', '/?')

	if s == 'hot':
			comments.sort(key=lambda x: x.hot, reverse=True)

	return render_template('recentcomments.html', posts=posts, url=config.URL, comments_with_posts=comments_with_posts, no_posts=True)

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_votes(obj):
	v = obj.get_votes()
	return v

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_posts_and_comments(subi=None, day=False):
	filter_today = datetime.now() - timedelta(days=1)
	if subi == None or subi == 'all':
		posts = db.session.query(Post).filter(Post.created >= filter_today)
		comments = db.session.query(Comment).filter(Comment.created >= filter_today)
	else:
		posts = db.session.query(Post).filter(Post.sub == subi, Post.created >= filter_today)
		comments = db.session.query(Comment).filter(Comment.sub_name == subi, Comment.created >= filter_today)

	if day:
		posts = posts.filter(Post.created >= filter_today)
		comments = comments.filter(Comment.created >= filter_today)

	posts = posts.options(load_only('author'))
	comments = comments.options(load_only('author'))

	return posts.all(), comments.all()

@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_top_stats(subi=None):
	t = time.time()
	votes = []
	users = []
	filter_today = datetime.now() - timedelta(days=1)

	posts, comments = get_posts_and_comments(subi=subi, day=True)	
	print(time.time() - t, '@@@@@@@@')	

	for p in posts:
		if p.author not in users:
			users.append(p.author)
		[votes.append(v) for v in get_votes(p) if v != None]


	for c in comments:
		if c.author not in users:
			users.append(c.author)
		[votes.append(v) for v in get_votes(c) if v != None]

	for v in votes:
		user = get_user_from_id(v.user_id)
		if user.username not in users:
			users.append(user.username)
	print(time.time() - t, '@@@@@@@@')
	return {'active_users':len(users), 'posts_today':len(posts)}



@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def get_stats(subi=None):
	if subi == None:
		votes = db.session.query(Vote).all()
		posts = db.session.query(Post).all()
		comments = db.session.query(Comment).all()
		users = db.session.query(Iuser).all()
		bans = db.session.query(Ban).count()
		messages = db.session.query(Message).count()
		mod_actions = db.session.query(Mod_action).count()
		subs = db.session.query(Sub).count()
		subscripts = 0
	else:
		posts = db.session.query(Post).filter_by(sub=subi).all()
		comments = db.session.query(Comment).filter_by(sub_name=subi).all()
		bans = db.session.query(Ban).filter_by(sub=subi).count()
		mod_actions = db.session.query(Mod_action).filter_by(sub=subi).count()
		users = []
		votes = []
		for v in posts:
			[votes.append(vv) for vv in db.session.query(Vote).filter_by(post_id=v.id).all()]
			[users.append(vv) for vv in db.session.query(Iuser).filter_by(username=v.author).all()]
		for v in comments:
			[votes.append(vv) for vv in db.session.query(Vote).filter_by(comment_id=v.id).all()]
			[users.append(vv) for vv in db.session.query(Iuser).filter_by(username=v.author).all()]
		users_blocked = [n.username for n in db.session.query(Sub_block).filter_by(sub=subi).all()]
		subscripts = len([u for u in db.session.query(Iuser) if u.username not in users_blocked])
		messages = 0
		subs = 0

	daycoms = [c for c in comments if ((datetime.now() - c.created).total_seconds()) < 86400]


	dayusers = []

	for uu in daycoms:
		if uu.author not in dayusers:
			dayusers.append(uu.author)

	dayposts = [p for p in posts if ((datetime.now() - p.created).total_seconds()) < 86400]

	for uuu in dayposts:
		if uuu.author not in dayusers:
			dayusers.append(uuu.author)

	dayvotes = []

	for vvv in votes:
		if hasattr(vvv, 'created'):
			if((datetime.utcnow() - vvv.created).total_seconds()) < 86400:
				dayvotes.append(vvv)

	for vz in dayvotes:
		new_user = db.session.query(Iuser).filter(Iuser.id == vz.user_id).first()
		if hasattr(new_user, 'username'):
			if new_user.username not in dayusers:
				dayusers.append(new_user.username)

	users = len(users)
	daycoms = len(daycoms)
	dayposts = len(dayposts)
	dayvotes = len(dayvotes)
	dayusers = len(dayusers)

	# requires user be on linux, and have log file in this location, so this is
	# only set to try to be calculated on the ieddit prod/dev server. it makes
	# assumptions that cannot be made for any user on a different setup
	if config.URL == 'https://ieddit.com' or config.URL == 'http://dev.ieddit.com' and subi == None:
		try:
			fline = str(os.popen('head -n 1 /var/log/nginx/access.log').read()).split(' ')[3][1:]
			lline = str(os.popen('tail -n 1 /var/log/nginx/access.log').read()).split(' ')[3][1:]

			fline = datetime.strptime(fline, '%d/%b/%Y:%H:%M:%S')
			lline = datetime.strptime(lline, '%d/%b/%Y:%H:%M:%S')

			timediff = lline - fline

			timediff = ' total requests in past %s hours' % str(timediff.total_seconds() / 60 / 24)

			lc = str(os.popen('wc -l /var/log/nginx/access.log').read()).split(' ')[0]

			timediff = lc + timediff


			# cache_bust = '?' + str(time.time()).split('.')[0]
			uptime = (time.time() - int(cache_bust[1:])) / 60 / 60
		except Exception as e:
			print(e)
			timediff, uptime = False, False
	else:
		timediff, uptime = False, False


	return (len(posts), len(comments), users, bans, messages, mod_actions, subs, len(votes), daycoms, dayposts, dayvotes, dayusers,
		timediff, uptime, subscripts)

@app.route('/i/<subi>/stats/', methods=['GET'])
@app.route('/stats/', methods=['GET'])
#@cache.memoize(config.DEFAULT_CACHE_TIME, unless=only_cache_get)
def stats(subi=None):
	(posts, comments, users, bans, messages, mod_actions, subs, votes, daycoms, dayposts, dayvotes,
		dayusers, timediff, uptime, subscripts) = get_stats(subi=subi)

	if 'admin' in session:
		debug = str(vars(request))
	else:
		debug = False

	return render_template('stats.html', posts=posts, dayposts=dayposts, comments=comments, daycoms=daycoms,
		users=users, bans=bans, messages=messages, mod_actions=mod_actions, subs=subs, votes=votes, dayvotes=dayvotes,
		dayusers=dayusers, timediff=timediff, uptime=uptime, debug=debug, subi=subi, subscripts=subscripts)


from blueprints import mod
app.register_blueprint(mod.bp)

from blueprints import user
app.register_blueprint(user.ubp)

from blueprints import admin
app.register_blueprint(admin.abp)

from blueprints import api
app.register_blueprint(api.bp)
