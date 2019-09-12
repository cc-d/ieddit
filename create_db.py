from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from ieddit import db
from models import *

db.create_all()
db.session.commit()

new_user = User(username='test', email='test@test.com'=,
	password=generate_password_hash('test'))
db.session.add(new_user)