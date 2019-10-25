import os, sys
abspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, abspath) 
os.chdir(abspath)

from datetime import timedelta
import logging
from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from ieddit import db
from models import *
from functions.functions import *
import string
from random import randint, choice
from faker import Faker
import json
import config
import psycopg2

fake = Faker()

if config.DB_TYPE == 'postgres':
    if config.USE_RECREATE == False:
        conn = psycopg2.connect(host=config.PG_HOST, database=config.DATABASE, user=config.PG_USER, password=config.PG_PASSWORD)
        conn.set_session(autocommit=True)
        cur = conn.cursor()
        logging.info('connected to {0} on database {1}'.format(config.PG_HOST, config.DATABASE))
        cur.execute("DROP SCHEMA public CASCADE;")
        cur.execute("CREATE SCHEMA public;")
        # commented queries below throw errors about not existing
        #cur.execute("GRANT ALL ON SCHEMA public TO postgres;")
        cur.execute("GRANT ALL ON SCHEMA public TO public;")
        cur.execute("COMMENT ON SCHEMA public IS 'standard public schema';")
        #cur.execute("CREATE USER test WITH PASSWORD 'test';")
        #cur.execute("ALTER SCHEMA public OWNER to postgres;")
        logging.info('Succesfully provisioned database')
    else:
        print('bash ' + abspath + '/utilities/recreate_psql_db.sh')
        os.system('bash ' + abspath + '/utilities/recreate_psql_db.sh')
elif config.DB_TYPE == 'sqlite':
    try:
        os.remove('{0}.db'.format(config.PG_USER))
    except FileNotFoundError:
        pass

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

new_user = Iuser(username='Anonymous', email='test@test.com',
    password=generate_password_hash('test'))
db.session.add(new_user)
db.session.commit()

new_user = Iuser(username='a', email='a@a.com',
    password=generate_password_hash('a'), admin=True, anonymous=True)
db.session.add(new_user)
db.session.commit()

for i in range(20):
    new_user = Iuser(username=rstring(3,10), email= rstring(4) + '@test.com',
    password=generate_password_hash('test'))
    db.session.add(new_user)
db.session.commit()

new_sub = Sub(name='test', created_by='test', created_by_id=1, title='for testing')
db.session.add(new_sub)
db.session.commit()
new_mod = Moderator(username='test', sub='test')
db.session.add(new_mod)
db.session.commit()

for i in range(10):
    new_sub = Sub(name=rstring(3, 10), created_by='test', created_by_id=1)
    db.session.add(new_sub)
    db.session.commit()
    new_mod = Moderator(username=new_sub.created_by, sub=new_sub.name)
    db.session.add(new_mod)
    db.session.commit()

new_post = Post(url='https://google.com', title='Test Title', inurl_title=convert_ied('Test Title'),
 author='test', author_id=1, sub='test', ups=randint(100,200), downs=randint(1,5), post_type='url', 
 author_type='mod', stickied=True)
db.session.add(new_post)
db.session.commit()
new_post.permalink = config.URL + '/i/' + new_post.sub + '/' + str(new_post.id) + '/' + new_post.inurl_title +  '/'
db.session.commit()
test_perma = new_post.permalink
fp = new_post

for i in range(50):
    title = fake.text()[:randint(10,200)]
    new_post = Post(url='https://google.com/' + rstring(5, 10), title=title, inurl_title=convert_ied(title), 
        author='test', author_id=1, sub='test', ups=randint(1,20), downs=randint(1,5), post_type='url', author_type='mod')
    db.session.add(new_post)
    db.session.commit()
    new_post.created = new_post.created - timedelta(days=randint(0,8))
    new_post.permalink = config.URL + '/i/' + new_post.sub + '/' + str(new_post.id) + '/' + new_post.inurl_title +  '/'
    db.session.commit()
for i in range(50):
    title = fake.text()[:randint(10,200)]
    new_post = Post(title=title, inurl_title=convert_ied(title), self_text=pseudo_markup(fake.text(2000))[:randint(500,2000)],
        author='test', author_id=1, sub='test', ups=randint(1,20), downs=randint(1,5), post_type='self_post', author_type='mod')
    db.session.add(new_post)
    db.session.commit()
    new_post.created = new_post.created - timedelta(days=randint(0,8))
    new_post.permalink = config.URL + '/i/' + new_post.sub + '/' + str(new_post.id) + '/' + new_post.inurl_title +  '/'
    db.session.commit()

db.session.commit()

new_comment = Comment(post_id=1, sub_name='test', text='this is comment text', author='test', author_id=1, ups=randint(1,20), downs=randint(1,5),
                    author_type='mod')
db.session.add(new_comment)
db.session.commit()

post = db.session.query(Post).filter_by(id=1).first()
new_comment.permalink = post.permalink + str(new_comment.id)
db.session.commit()

new_comment = Comment(post_id=1, sub_name='test', text='this is a reply', author='test', author_id=1, parent_id=1, ups=randint(1,20),
                downs=randint(1,5), author_type='mod')
db.session.add(new_comment)
db.session.commit()

post = db.session.query(Post).filter_by(id=1).first()
new_comment.permalink = post.permalink + str(new_comment.id)
db.session.commit()

comments = list(Comment.query.all())

for i in range(200):
    if choice([x for x in range(3)]) == 0:
        pid = None
        level = None
    else:
        rancom = choice(comments)
        pid = rancom.id
        level = rancom.level + 1
    new_comment = Comment(post_id=1, sub_name='test', text=pseudo_markup(fake.text()[:randint(1,200)]),  author='test', author_id=1,
      parent_id=pid, level=level, ups=randint(1,20), downs=randint(1,5), author_type='mod')
    db.session.add(new_comment)
    db.session.commit()
    post = db.session.query(Post).filter_by(id=1).first()
    new_comment.permalink = post.permalink + str(new_comment.id)
    db.session.commit()    
    comments.append(new_comment)
new_message = Message(sent_to='a', sender='test', title='this is a title', text='this is text')
db.session.add(new_message)
db.session.commit()

new_message = Message(sent_to='a', sender='test', title='this is a title', text='this is text', in_reply_to=fp.permalink)
db.session.add(new_message)
db.session.commit()


db.session.commit()
