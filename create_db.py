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
import json
fake = Faker()

#su postgres
#os.system('rm -rf test.db')
os.system('bash recreate_psql_db.sh')

# force clear user sessions by changing key
with open('config.py', 'r+') as f:
	ctext = f.read()
	ctext = ctext.split('|r|')
	ctext[1] = rstring(10)
	f.seek(0)
	f.write('|r|'.join(ctext))

db.create_all()
db.session.commit()

new_user = Iuser(username='test', email='test@test.com',
	password=generate_password_hash('test'))
db.session.add(new_user)
db.session.commit()

for i in range(20):
	new_user = Iuser(username=rstring(3,10), email= rstring(4) + '@test.com',
	password=generate_password_hash('test'))
	db.session.add(new_user)
db.session.commit()

new_sub = Sub(name='test', created_by='test', created_by_id=1)
db.session.add(new_sub)
db.session.commit()
new_mod = Moderator(username='test', user_id=1, sub_id=1, sub_name='test')
db.session.add(new_mod)
db.session.commit()

for i in range(10):
	new_sub = Sub(name=rstring(3, 10), created_by='test', created_by_id=1)
	db.session.add(new_sub)
	db.session.commit()
	new_mod = Moderator(username=new_sub.created_by, user_id=new_sub.created_by_id, sub_id=new_sub.id, sub_name=new_sub.name)
	db.session.add(new_mod)
	db.session.commit()

new_post = Post(url='https://google.com', title='Test Title', inurl_title=convert_ied('Test Title'),
 author='test', author_id=1, sub='test', ups=randint(100,200), downs=randint(1,5), post_type='url')
db.session.add(new_post)
db.session.commit()


for i in range(10):
	title = fake.text()[:randint(10,200)]
	db.session.add(Post(url='https://google.com/' + rstring(5, 10), title=title, inurl_title=convert_ied(title), 
		author='test', author_id=1, sub='test', ups=randint(1,20), downs=randint(1,5), post_type='url'))
for i in range(10):
	title = fake.text()[:randint(10,200)]
	db.session.add(Post(title=title, inurl_title=convert_ied(title), self_text=psuedo_markup(fake.text(2000))[:randint(500,2000)],
		author='test', author_id=1, sub='test', ups=randint(1,20), downs=randint(1,5), post_type='self_post'))

db.session.commit()

new_comment = Comment(post_id=1, sub_name='test', text='this is comment text', author='test', author_id=1, ups=randint(1,20), downs=randint(1,5))
db.session.add(new_comment)
db.session.commit()

new_comment = Comment(post_id=1, sub_name='test', text='this is a reply', author='test', author_id=1, parent_id=1, ups=randint(1,20), downs=randint(1,5))
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
	new_comment = Comment(post_id=1, sub_name='test', text=psuedo_markup(fake.text()[:randint(1,200)]),  author='test', author_id=1,  parent_id=pid, level=level, ups=randint(1,20), downs=randint(1,5))
	db.session.add(new_comment)
	db.session.commit()
	comments.append(new_comment)

db.session.commit()