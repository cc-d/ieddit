from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from ieddit import db
from models import *
from functions import *
import os
import string
from random import randint, choice
from faker import Faker
fake = Faker()

#su postgres
#os.system('rm -rf test.db')
os.system('bash recreate_psql_db.sh')

db.create_all()
db.session.commit()

new_user = User(username='test', email='test@test.com',
	password=generate_password_hash('test'))
db.session.add(new_user)
db.session.commit()

for i in range(20):
	new_user = User(username=rstring(3,10), email= rstring(4) + '@test.com',
	password=generate_password_hash('test'))
	db.session.add(new_user)
db.session.commit()

new_sub = Sub(name='test', created_by='test')
db.session.add(new_sub)
db.session.commit()

for i in range(10):
	db.session.add(Sub(name=rstring(3, 10), created_by='test'))
db.session.commit()

new_post = Post(url='https://google.com', title='Test Title', inurl_title=convert_ied('Test Title'),
 author='test', sub='test', ups=randint(1,20), downs=randint(1,5))
db.session.add(new_post)
db.session.commit()
json_post = JSON_Post(id=new_post.id, comments={'title':new_post.title, 
	'inurl_title':new_post.inurl_title, 'author':new_post.author,
	'sub':new_post.sub, 'ups':new_post.ups, 'downs':new_post.downs, 'children':{}}
	)
db.session.add(json_post)
db.session.commit()

for i in range(10):
	title = fake.text()[:randint(10,200)]
	db.session.add(Post(url='https://google.com/' + rstring(5, 10), title=title, inurl_title=convert_ied(title), 
		author='test', sub='test', ups=randint(1,20), downs=randint(1,5)))

db.session.commit()

new_comment = Comment(post_id=1, text='this is comment text', username='test', ups=randint(1,20), downs=randint(1,5))
db.session.add(new_comment)
db.session.commit()

new_comment = Comment(post_id=1, text='this is a reply', username='test', parent_id=1, ups=randint(1,20), downs=randint(1,5))
db.session.add(new_comment)
db.session.commit()

comments = list(Comment.query.all())

for i in range(50):
	if choice([x for x in range(3)]) == 0:
		pid = None
		level = None
	else:
		rancom = choice(comments)
		pid = rancom.id
		level = rancom.level + 1
	new_comment = Comment(post_id=1, text=fake.text()[:randint(1,200)], username='test', parent_id=pid, level=level, ups=randint(1,20), downs=randint(1,5))
	db.session.add(new_comment)
	db.session.commit()
	comments.append(new_comment)

db.session.commit()
