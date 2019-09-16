from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from ieddit import db
from models import *
from functions import *
import os
import string
import random
from faker import Faker
fake = Faker()

os.system('rm -rf test.db')

db.create_all()
db.session.commit()

new_user = User(username='test', email='test@test.com',
	password=generate_password_hash('test'))
db.session.add(new_user)

for i in range(20):
	new_user = User(username=rstring(3,10), email= rstring(4) + '@test.com',
	password=generate_password_hash('test'))
	db.session.add(new_user)

new_sub = Sub(name='test', created_by='test')
db.session.add(new_sub)
db.session.commit()

for i in range(10):
	db.session.add(Sub(name=rstring(3, 10), created_by='test'))

new_post = Post(url='https://google.com', title='Test Title', inurl_title=convert_ied('Test Title'), author='test', sub='test')
db.session.add(new_post)
for i in range(10):
	title = fake.text()[:random.randint(10,200)]
	db.session.add(Post(url='https://google.com/' + rstring(5, 10), title=title, inurl_title=convert_ied(title), author='test', sub='test'))

new_comment = Comment(post_id=1, text='this is comment text', username='test')
db.session.add(new_comment)
db.session.commit()


new_comment = Comment(post_id=1, text='this is a reply', username='test', parent_id=1)
db.session.add(new_comment)
db.session.commit()

comments = list(Comment.query.all())

for i in range(50):
	if random.choice([x for x in range(3)]) == 0:
		pid = None
		level = None
	else:
		rancom = random.choice(comments)
		pid = rancom.id
		level = rancom.level + 1
	new_comment = Comment(post_id=1, text=fake.text()[:random.randint(1,200)], username='test', parent_id=pid, level=level)
	db.session.add(new_comment)
	db.session.commit()
	comments.append(new_comment)

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
