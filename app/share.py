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

from flask import Flask, render_template, request, redirect, flash, url_for, Blueprint, g, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, exists
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from flask_caching import Cache
from flask_session import Session
from flask_session_captcha import FlaskSessionCaptcha
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr
from jinja2 import escape, Markup

import requests

from sqlalchemy.orm import load_only
import traceback

from email.mime.text import MIMEText

from models import *

from functions.functions import *

from sqlalchemy.orm import load_only

app = Flask(__name__)
app.config.from_object('config')
cache = Cache(app, config={'CACHE_TYPE': config.CACHE_TYPE})

logger = logging.getLogger(__name__)


if (config.SENTRY_ENABLED):
    import sentry_sdk
    from sentry_sdk.integrations.flask import \
        FlaskIntegration

    sentry_sdk.init(
        config.SENTRY_DSN,
        integrations=[FlaskIntegration()]
    )

if config.DISCORD_ENABLED:
    from utilities.discord_logger import *

db = SQLAlchemy(app)
db.session.rollback()

Session(app)
captcha = FlaskSessionCaptcha(app)

limiter = Limiter(
    app,
    key_func=get_ipaddr,
    default_limits=config.LIMITER_DEFAULTS
)

#cache.clear()

cache_bust = '?' + str(time.time()).split('.')[0]