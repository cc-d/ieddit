from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash
import re
import config

from models import User
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