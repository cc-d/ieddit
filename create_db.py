from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from ieddit import db
from models import *
db.create_all()
db.session.commit()
