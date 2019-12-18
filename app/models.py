import sys
import urllib

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, session, request
from datetime import datetime, timedelta
from sqlalchemy import orm, func

from flask_caching import Cache

sys.path.append('functions/')

from share import *
import config

# easier for cross compability reasons than actual uuid type
def gen_anon_id():
    import uuid
    return str(uuid.uuid4())

# iuser instead of user to avoid conflicting namespace with postgresql
class Iuser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(75), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    admin = db.Column(db.Boolean, default=False, nullable=False)
    banned = db.Column(db.Boolean, default=False, nullable=False)
    anonymous = db.Column(db.Boolean, default=False, nullable=False)
    darkmode = db.Column(db.Boolean, default=False, nullable=False)
    hide_sub_style = db.Column(db.Boolean, default=False, nullable=False)
    pgp = db.Column(db.Boolean, default=False, nullable=False)
    always_override = db.Column(db.Boolean, default=False, nullable=False)
    anon_id = db.Column(db.String(255), default=gen_anon_id, nullable=True)
    language = db.Column(db.String(10), default=config.DEFAULT_LANGUAGE, nullable=True)
    hide_sub_language = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return '<Iuser %r>' % self.username

class Sub(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    created_by = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    rules = db.Column(db.String(20000), nullable=True, default=None)
    title = db.Column(db.String(1000), nullable=True, default=None)
    nsfw = db.Column(db.Boolean, default=False, nullable=False)
    css = db.Column(db.String(20000), default=None)
    muted = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(10), default=config.DEFAULT_LANGUAGE, nullable=True)

    def __repr__(self):
        return '<Sub %r>' % self.name

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    url = db.Column(db.String(2000), nullable=True)
    self_text = db.Column(db.String(20000), nullable=True)
    post_type = db.Column(db.String(15), nullable=False)
    title = db.Column(db.String(400), nullable=False)
    ups = db.Column(db.Integer, default=0, nullable=False)
    downs = db.Column(db.Integer, default=0, nullable=False)
    inurl_title = db.Column(db.String(75), nullable=False)
    author = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)
    author_type = db.Column(db.String(20), default='user', nullable=False)
    sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    permalink = db.Column(db.String(2000), nullable=True)
    stickied = db.Column(db.Boolean, default=False, nullable=False)
    locked = db.Column(db.Boolean, default=False, nullable=False)
    anonymous = db.Column(db.Boolean, default=False, nullable=False)
    edited = db.Column(db.Boolean, default=False, nullable=False)
    locked = db.Column(db.Boolean, default=False, nullable=False)
    nsfw = db.Column(db.Boolean, default=False, nullable=False)
    remote_image_url = db.Column(db.String(2000), default=None, nullable=True)
    override = db.Column(db.Boolean, default=False, nullable=False)
    announcement = db.Column(db.Boolean, default=False, nullable=False)

    def get_permalink(self):
        return config.URL + config.SUB_PREFIX + str(urllib.parse.urlparse(self.permalink).path)

    def get_has_voted(self, user_id):
        return db.session.query(Vote).filter_by(post_id=self.id, user_id=user_id).first()

    def get_score(self):
        return (self.ups - self.downs)

    def __repr__(self):
        return '<Post %r>' % self.id

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    text = db.Column(db.String(20000), nullable=False)
    ups = db.Column(db.Integer, default=0, nullable=False)
    downs = db.Column(db.Integer, default=0, nullable=False)
    author = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)
    author_type = db.Column(db.String(20), default='user', nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    level = db.Column(db.Integer, default=0, nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    sub_name = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
    deleted = db.Column(db.Boolean, default=False, unique=False)
    permalink = db.Column(db.String(2000), nullable=True)
    anonymous = db.Column(db.Boolean, default=False, nullable=False)
    edited = db.Column(db.Boolean, default=False, nullable=False)
    override = db.Column(db.Boolean, default=False, nullable=False)
    removed_by = db.Column(db.String(30), default=None)

    def get_permalink(self):
        return config.URL + config.SUB_PREFIX + str(urllib.parse.urlparse(self.permalink).path)

    def get_children(self, show_deleted=True):
        if show_deleted is False:
            return db.session.query(Comment).filter_by(parent_id=self.id, deleted=False)
        return db.session.query(Comment).filter_by(parent_id=self.id)

    def get_score(self):
        return int(self.ups) - int(self.downs)

    def __repr__(self):
        return '<Comment %r>' % self.id

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    vote = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return '<Vote %r>' % self.id

class Moderator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
    sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
    rank = db.Column(db.Integer, default=0, nullable=False, autoincrement=True)

    def __repr__(self):
        return '<Moderator %r>' % self.id

class Mod_action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=False, nullable=False)
    action = db.Column(db.String(20), unique=False, nullable=False)
    url = db.Column(db.String(2000), unique=False, nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)

    def __repr__(self):
        return '<Mod_action %r>' % self.id

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(400), unique=False, nullable=False)
    text = db.Column(db.String(40000), unique=False, nullable=False)
    read = db.Column(db.Boolean, default=False, nullable=False)
    sent_to = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
    sender = db.Column(db.String(20), db.ForeignKey('iuser.username'), default=None, nullable=True)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    in_reply_to = db.Column(db.String(400), default=None, nullable=True)
    anonymous = db.Column(db.Boolean, default=False, nullable=False)
    sender_type = db.Column(db.String(20), default='user', nullable=False)
    encrypted = db.Column(db.Boolean, default=False, nullable=False)
    encrypted_key_id = db.Column(db.Integer, db.ForeignKey('pgp.id'), default=None, nullable=True)

    def __repr__(self):
        return '<Message %r>' % self.id

class Ban(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
    username = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
    anonymous = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return '<Ban %r>' % self.id

class Sub_block(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sub = db.Column(db.String(30), db.ForeignKey('sub.name'), nullable=False)
    username = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)

    def __repr__(self):
        return '<Sub_block %r>' % self.id

class Password_reset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)    
    rankey = db.Column(db.String(50), unique=False, nullable=False)
    valid = db.Column(db.Boolean, default=True, nullable=False)
    expires = db.Column(db.DateTime)

    def __repr__(self):
        return '<Password_reset %r>' % self.id


class Pgp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
    pubkey = db.Column(db.String(20000), nullable=False)
    privkey = db.Column(db.String(20000), nullable=False)

    def __repr__(self):
        return '<Pgp %r>' % self.id


class Hidden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    username = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
    other_user = db.Column(db.Integer, db.ForeignKey('iuser.id'), nullable=True)
    anonymous = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Hidden %r>' % self.id

class Api_key(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('iuser.username'), nullable=False)
    key = db.Column(db.String(20000), nullable=False)

    def __repr__(self):
        return '<Api_key %r>' % self.id


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
