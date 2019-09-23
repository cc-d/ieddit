from flask import Flask, render_template, session, request, redirect, flash, url_for, Blueprint
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, exists

from werkzeug.security import generate_password_hash, check_password_hash
import re
import config

from models import *
from functions import *

bp = Blueprint('mod', 'mod', url_prefix='/mod')

@bp.route('/hello/')
def hello():
	return 'todo'