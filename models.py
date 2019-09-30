from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, session, request
from datetime import datetime
from flask_caching import Cache

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# iuser instead of user to avoid conflicting namespace with postgresql
class Iuser(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(75), nullable=True)
	password = db.Column(db.String(255), nullable=False)
	created = db.Column(db.DateTime, default=datetime.now, nullable=False)
	admin = db.Column(db.Boolean, default=False, nullable=False)
	banned = db.Column(db.Boolean, default=False, nullable=False)
	anonymous = db.Column(db.Boolean, default=False, nullable=False)

	def __repr__(self):
		return '<Iuser %r>' % self.username

class Sub(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), unique=True, nullable=False)
	created_by = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
	created_by_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)
	created = db.Column(db.DateTime, default=datetime.now, nullable=False)
	rules = db.Column(db.String(20000), nullable=True, default=None)
	title = db.Column(db.String(1000), nullable=True, default=None)
	nsfw = db.Column(db.Boolean, default=False, nullable=False)

	def get_comments(self):
		self.comments = db.session.query(Comment).filter_by(sub_name=self.name)

	def get_posts(self):
		self.posts = db.session.query(Post).filter_by(sub=self.name)

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
	author_type = db.Column(db.String(20), default='user', nullable=False)
	sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
	created = db.Column(db.DateTime, default=datetime.now, nullable=False)
	deleted = db.Column(db.Boolean, default=False, nullable=False)
	permalink = db.Column(db.String(2000), nullable=True)
	stickied = db.Column(db.Boolean, default=False, nullable=False)
	locked = db.Column(db.Boolean, default=False, nullable=False)
	anonymous = db.Column(db.Boolean, default=False, nullable=False)
	edited = db.Column(db.Boolean, default=False, nullable=False)
	locked = db.Column(db.Boolean, default=False, nullable=False)
	nsfw = db.Column(db.Boolean, default=False, nullable=False)

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
	author_type = db.Column(db.String(20), default='user', nullable=False)
	parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
	level = db.Column(db.Integer, default=0, nullable=False)
	created = db.Column(db.DateTime, default=datetime.now, nullable=False)
	sub_name = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
	deleted = db.Column(db.Boolean, default=False, unique=False)
	permalink = db.Column(db.String(2000), nullable=True)
	anonymous = db.Column(db.Boolean, default=False, nullable=False)
	edited = db.Column(db.Boolean, default=False, nullable=False)

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
	sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
	rank = db.Column(db.Integer, default=0, nullable=False, autoincrement=True)

	def __repr__(self):
		return '<Moderator %r>' % self.id

class Mod_action(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=False, nullable=False)
	action = db.Column(db.String(20), unique=False, nullable=False)
	url = db.Column(db.String(2000), unique=False, nullable=False)
	created = db.Column(db.DateTime, default=datetime.now, nullable=False)
	sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)

	def __repr__(self):
		return '<Mod_action %r>' % self.id

class Message(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(400), unique=False, nullable=False)
	text = db.Column(db.String(20000), unique=False, nullable=False)
	read = db.Column(db.Boolean, default=False, nullable=False)
	sent_to = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
	sender = db.Column(db.String(20), db.ForeignKey('iuser.username'), default=None, nullable=True)
	created = db.Column(db.DateTime, default=datetime.now, nullable=False)
	in_reply_to = db.Column(db.String(400), default=None, nullable=True)
	anonymous = db.Column(db.Boolean, default=False, nullable=False)
	sender_type = db.Column(db.String(20), default='user', nullable=False)

	def __repr__(self):
		return '<Message %r>' % self.id

class Ban(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
	username = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)

	def __repr__(self):
		return '<Ban %r>' % self.id
