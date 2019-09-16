from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, session, request
from datetime import datetime

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(75), nullable=True)
	password = db.Column(db.String(255), nullable=False)
	created = db.Column(db.DateTime, default=datetime.now())

	def __repr__(self):
		return '<User %r>' % self.username

class Sub(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), unique=True, nullable=False)
	created_by = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
	created = db.Column(db.DateTime, default=datetime.now())

	def __repr__(self):
		return '<Sub %r>' % self.name

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)	
	url = db.Column(db.String(2000), nullable=False)
	title = db.Column(db.String(400), nullable=False)
	ups = db.Column(db.Integer, default=0, nullable=False)
	downs = db.Column(db.Integer, default=0, nullable=False)
	inurl_title = db.Column(db.String(75), nullable=False)
	author = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
	sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
	created = db.Column(db.DateTime, default=datetime.now())

	def __repr__(self):
		return '<Post %r>' % self.id

class JSON_Post(db.Model):
	id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
	comments = db.Column(db.JSON)

	def __repr__(Self):
		return '<JSON_Post %r>' % self.id

class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

	text = db.Column(db.String(20000), nullable=False)
	ups = db.Column(db.Integer, default=0, nullable=False)
	downs = db.Column(db.Integer, default=0, nullable=False)
	username = db.Column(db.String(20), nullable=False)
	parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
	level = db.Column(db.Integer, default=0)
	created = db.Column(db.DateTime, default=datetime.now())

	def __repr__(self):
		return '<Comment %r>' % self.id


