from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from ieddit import db
from models import *
from functions import *

db.create_all()
db.session.commit()

new_user = User(username='test', email='test@test.com',
	password=generate_password_hash('test'))
db.session.add(new_user)

new_sub = Sub(name='test', created_by='test')
db.session.add(new_sub)

new_post = Post(url='https://google.com', title='Test Title', inurl_title=convert_ied('Test Title'), author='test', sub='test')
db.session.add(new_post)

new_comment = Comment(post_id=1, text='this is comment text', username='test')
db.session.add(new_comment)

'''
class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	post_id = db.Column(db.Integer, unique=False, nullable=False)
	text = db.Column(db.String(20000), unique=False, nullable=False)
	ups = db.Column(db.Integer, default=0, nullable=False)
	downs = db.Column(db.Integer, default=0, nullable=False)

	def __repr__(self):
		return '<Comment %r>' % self.id
'''

db.session.commit()