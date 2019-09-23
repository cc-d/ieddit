from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, session, request
from datetime import datetime

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

class Iuser(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(75), nullable=True)
	password = db.Column(db.String(255), nullable=False)
	created = db.Column(db.DateTime, default=datetime.now())
	admin = db.Column(db.Boolean, default=False, unique=False)

	def __repr__(self):
		return '<Iuser %r>' % self.username

class Sub(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), unique=True, nullable=False)
	created_by = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
	created_by_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)
	created = db.Column(db.DateTime, default=datetime.now())

	def __repr__(self):
		return '<Sub %r>' % self.name

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)	
	url = db.Column(db.String(2000), nullable=True)
	self_text = db.Column(db.String(20000), nullable=True)
	post_type = db.Column(db.String(15), nullable=False)
	title = db.Column(db.String(400), nullable=False)
	ups = db.Column(db.Integer, default=0, nullable=False)
	downs = db.Column(db.Integer, default=0, nullable=False)
	inurl_title = db.Column(db.String(75), nullable=False)
	author = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
	author_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)
	sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
	created = db.Column(db.DateTime, default=datetime.now())

	def __repr__(self):
		return '<Post %r>' % self.id

class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
	text = db.Column(db.String(20000), nullable=False)
	ups = db.Column(db.Integer, default=0, nullable=False)
	downs = db.Column(db.Integer, default=0, nullable=False)
	author = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
	author_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)
	parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
	level = db.Column(db.Integer, default=0)
	created = db.Column(db.DateTime, default=datetime.now())
	sub_name = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)

	def __repr__(self):
		return '<Comment %r>' % self.id

class Vote(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
	comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
	vote = db.Column(db.Integer, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)

	def __repr__(self):
		return '<Vote %r>' % self.id

class Moderator(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)
	sub_id = db.Column(db.Integer, db.ForeignKey('sub.id'), nullable=False)
	sub_name = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
	rank = db.Column(db.Integer, default=0)

	def __repr__(self):
		return '<Moderator %r>' % self.id