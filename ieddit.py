from flask import Flask, render_template, session, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

from werkzeug.security import generate_password_hash, check_password_hash
import re
import config

from models import *
from functions import *

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

@app.route('/')
def index():
	return all_sub_posts(index=True)
	
@app.route('/login',  methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		if username == None or password == None or len(username) > 20 or len(password) > 100:
			return 'invalid login'

		if db.session.query(db.session.query(User)
				.filter_by(username=username)
				.exists()).scalar():
			hashed_pw = User.query.filter_by(username=username).first().password
			if check_password_hash(hashed_pw, password):
				session['username'] = username
				return redirect(config.URL, 302)

		return 'login failed' 

@app.route('/register', methods=['POST'])
def register():
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		email = request.form.get('email')

		if verify_username(username):
			if db.session.query(db.session.query(User)
				.filter_by(username=username).exists()).scalar():
				return 'exists'
		else:
			return 'invalid username'

		if len(password) > 100:
			return 'pass to long'

		if email != '':
			if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
				return 'invalid email'

		new_user = User(username=username, email=email,
			password=generate_password_hash(password))
		db.session.add(new_user)
		db.session.commit()
		session['username'] = username
		return redirect(config.URL, 302)

# These two functions look the same, but they will work somewhat different in fucture
@app.route('/r/<subi>/')
def subi(subi):
	if verify_subname(subi) == False:
		return 'invalid subpath'
	subname = Sub.query.filter(func.lower(Sub.name) == subi.lower()).first()

	if subname == None:
		return 'invalid sub'
	posts = Post.query.filter_by(sub=subi).all()

	p = []
	for post in posts:
		post.created_ago = time_ago(post.created)
		post.site_url = config.URL + '/r/' + subi + '/' + str(post.id) + '/' + post.inurl_title
		post.remote_url_parsed = post_url_parse(post.url)
		post.comment_count = Comment.query.filter_by(post_id=post.id).count()
		p.append(post)

	return render_template('sub.html', posts=p, url=config.URL)

# These two functions look the same, but they will work somewhat different in fucture
@app.route('/r/all/')
def all_sub_posts(index=False):
	posts = Post.query.filter_by().order_by(Post.id.asc()).limit(10)
	p = []
	for post in posts:
		post.created_ago = time_ago(post.created)
		post.site_url = config.URL + '/r/' + post.sub + '/' + str(post.id) + '/' + post.inurl_title
		post.remote_url_parsed = post_url_parse(post.url)
		post.comment_count = Comment.query.filter_by(post_id=post.id).count()
		p.append(post)
	if index:
		return render_template('index.html', posts=p, url=config.URL)
	else:
		return render_template('sub.html', posts=p, url=config.URL)

@app.route('/r/<sub>/<post_id>/<inurl_title>/<comment_id>/')
@app.route('/r/<sub>/<post_id>/<inurl_title>/')
def comment(sub, post_id, inurl_title, comment_id=False):
	if sub == None or post_id == None or inurl_title == None:
		return 'badlink'
	post = Post.query.filter_by(id=post_id, sub=sub).first()
	post.comment_count = Comment.query.filter_by(post_id=post.id).count()
	post.created_ago = time_ago(post.created)
	post.remote_url_parsed = post_url_parse(post.url)

	if not comment_id:
		comments = Comment.query.filter(Comment.post_id == post_id, Comment.level < 7).all()
	else:
		comments = list_of_child_comments(comment_id)
		comment = Comment.query.filter_by(id=comment_id).first()
		comments.append(comment)

	for c in comments:
		c.created_ago = time_ago(c.created)

	if not comment_id:
		tree = create_id_tree(comments)
	else:
		tree = create_id_tree(comments, parent_id=comment_id)
	tree = comment_structure(comments, tree)
	return render_template('comments.html', comments=comments, post_id=post_id, 
		post_url='%s/r/%s/%s/%s/' % (config.URL, sub, post_id, post.inurl_title), post=post, tree=tree)

# need to entirely rewrite how comments are handled once everything else is complete
# this sort of recursion KILLS performance, especially when combined with the already
# terrible comment_structure function. only reason i'm doing it this way now is
# performance doens't matter and i don't have redis/similar setup yet
def list_of_child_comments(comment_id):
	comments = {}
	current_comments = []
	start = Comment.query.filter_by(parent_id=comment_id).all()
	for c in start:
		current_comments.append(c.id)
		comments[c.id] = c
	while len(current_comments) > 0:
		for current_c in current_comments:
			for c in Comment.query.filter_by(parent_id=current_c).all():
				current_comments.append(c.id)
				comments[c.id] = c
			current_comments.remove(current_c)
	return [comments[c] for c in comments]

@app.route('/create', methods=['POST', 'GET'])
def create_sub():
	if request.method == 'POST':
		subname = request.form.get('subname')
		if subname != None and verify_subname(subname) and 'username' in session:
			if len(subname) > 30 or len(subname) < 1:
				return 'invalid length'
			new_sub = Sub(name=subname, created_by=session['username'])
			db.session.add(new_sub)
			db.session.commit()
			return redirect(config.URL + '/r/' + subname, 302)
		return 'invalid'
	elif request.method == 'GET':
		return render_template('create.html')

@app.route('/u/<uname>/', methods=['GET'])
def view_user(uname):
	return render_template('user.html', user=uname);

@app.route('/create_post', methods=['POST', 'GET'])
def create_post():
	if request.method == 'POST':
		title = request.form.get('title')
		url = request.form.get('url')
		sub = request.form.get('sub')
		if title == None or url == None or 'username' not in session:
			return 'invalid post'
		if len(title) > 400 or len(title) < 1 or len(sub) > 30 or len(sub) < 1 or len(url) > 2000 or len(url) < 1:
			return 'invalid post len'
		new_post = Post(url=url, title=title, inurl_title=convert_ied(title), author=session['username'], sub=sub)
		db.session.add(new_post)
		db.session.commit()
		url = config.URL + '/r/' + sub
		return redirect(url, 302)

	if request.method == 'GET':
		return render_template('create_sub.html')

@app.route('/create_comment', methods=['POST'])
def create_comment():
	text = request.form.get('comment_text')
	post_id = request.form.get('post_id')
	post_url = request.form.get('post_url')
	parent_id = request.form.get('parent_id')
	if parent_id == '':
		parent_id = None
	if text == None or 'username' not in session or post_id == None or post_url == None:
		return 'bad comment'
	if parent_id != None:
		level = (Comment.query.filter_by(id=parent_id).first().level) + 1
	new_comment = Comment(post_id=post_id, text=text, username=session['username'], parent_id=parent_id, level=level)
	db.session.add(new_comment)
	db.session.commit()
	return redirect(post_url, 302)

@app.route('/logout', methods=['POST', 'GET'])
def logout():
	session.pop('username', None)
	return redirect(config.URL, 302)