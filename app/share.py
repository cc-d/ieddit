"""
This provides easy global inheritance for various imports/objects
"""
from datetime import timedelta, datetime
import logging
import time
import re
import config
import base64
import os
import urllib.parse
from functools import wraps

from flask import Flask, render_template, request, redirect, flash, url_for, Blueprint, g, abort, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, exists
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr
from jinja2 import escape, Markup

import requests

from sqlalchemy.orm import load_only
import traceback

from email.mime.text import MIMEText

import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/functions/')
sys.path.append('.')

from utilities.discord_logger import *

logger = logging.getLogger('ieddit.py')

from functions.functions import *

from sqlalchemy.orm import load_only

app = Flask(__name__)
app.config.from_object('config')
cache = Cache(app, config={'CACHE_TYPE': config.CACHE_TYPE})


if (config.SENTRY_ENABLED):
    import sentry_sdk
    from sentry_sdk.integrations.flask import \
        FlaskIntegration

    sentry_sdk.init(
        config.SENTRY_DSN,
        integrations=[FlaskIntegration()]
    )


db = SQLAlchemy(app)
db.session.rollback()

from models import *

from db_functions import *


limiter = Limiter(
    app,
    key_func=get_ipaddr,
    default_limits=config.LIMITER_DEFAULTS
)

#cache.clear()

cache_bust = '?' + str(time.time()).split('.')[0]
