from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, session, request
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(75), unique=False, nullable=True)
	password = db.Column(db.String(255), unique=False, nullable=False)

	def __repr__(self):
		return '<User %r>' % self.username

class Sub(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), unique=True, nullable=False)
	created_by = db.Column(db.String(20), unique=False, nullable=False)

	def __repr__(self):
		return '<Sub %r>' % self.name

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)	
	url = db.Column(db.String(2000), unique=False, nullable=False)
	title = db.Column(db.String(400), unique=False, nullable=False)
	ups = db.Column(db.Integer, default=0, nullable=False)
	downs = db.Column(db.Integer, default=0, nullable=False)
	inurl_title = db.Column(db.String(75), unique=False, nullable=False)
	author = db.Column(db.String(20), unique=False, nullable=False)
	sub = db.Column(db.String(30), unique=False, nullable=False)

	def __repr__(self):
		return '<Post %r>' % self.id