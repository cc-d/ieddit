from flask import Flask, render_template, session, request, redirect
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash
import re
import config

from models import *
from functions import *

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

@app.route('/')
def hello_world():
	return 'hi'

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
				return 'login succeded'

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
		return 'ok'

@app.route('/r/<subi>')
def subi(subi):
	subname = Sub.query.filter_by(name=subi).first()
	if subname == None:
		return 'invalid sub'
	posts = Post.query.filter_by(sub=subi).all()
	if len(posts) < 1:
		return 'no posts'
	p = ''
	for po in posts:
		p += str(vars(po)) + '<br>' 
	return p

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
			return 'created'
		return 'invalid'
	elif request.method == 'GET':
		return render_template('create.html')

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

















