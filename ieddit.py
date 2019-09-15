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
	return r_all(index=True)
	
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

@app.route('/r/<subi>')
def subi(subi):
	if verify_subname(subi) == False:
		return 'invalid subpath'
	subname = Sub.query.filter(func.lower(Sub.name) == subi.lower()).first()

	if subname == None:
		return 'invalid sub'
	posts = Post.query.filter_by(sub=subi).all()

	p = []
	for post in posts:
		post.site_url = config.URL + '/r/' + subi + '/' + str(post.id) + '/' + post.inurl_title
		post.comment_count = Comment.query.filter_by(post_id=post.id).count()
		p.append(post)

	return render_template('sub.html', posts=p, url=config.URL)

@app.route('/r/all')
def r_all(index=False):
	posts = Post.query.filter_by().order_by(Post.id.asc()).limit(10)
	p = []
	for post in posts:
		post.site_url = config.URL + '/r/' + post.sub + '/' + str(post.id) + '/' + post.inurl_title
		post.comment_count = Comment.query.filter_by(post_id=post.id).count()
		p.append(post)
	if index:
		return render_template('index.html', posts=p, url=config.URL)
	else:
		return render_template('sub.html', posts=p, url=config.URL)

@app.route('/r/<sub>/<post_id>/<inurl_title>/')
def comment(sub, post_id, inurl_title):
	if sub == None or post_id == None or inurl_title == None:
		return 'badlink'
	post = Post.query.filter_by(id=post_id, sub=sub).first()
	post.comment_count = Comment.query.filter_by(post_id=post.id).count()

	comments = Comment.query.filter_by(post_id=post_id).all()
	tree = create_comment_tree(comments)
	tree = comment_structure(comments, tree)
	return render_template('comments.html', comments=comments, post_id=post_id, 
		post_url='%s/r/%s/%s/%s/' % (config.URL, sub, post_id, inurl_title), post=post, tree=tree)

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

@app.route('/u/<uname>', methods=['GET'])
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
	new_comment = Comment(post_id=post_id, text=text, username=session['username'], parent_id=parent_id)
	db.session.add(new_comment)
	db.session.commit()
	return redirect(post_url, 302)

@app.route('/logout', methods=['POST', 'GET'])
def logout():
	session.pop('username', None)
	return redirect(config.URL, 302)