"""
The purpose of this module is mainly to
contain general functions that query the
db in some way, as much should be migrated
as possible from ieddit.py
"""
import sys
import os
import config
from share import *
from functions import *

##### Sub Functions #####
@cache.memoize(config.DEFAULT_CACHE_TIME)
def is_sub_nsfw(sub):
    """
    returns a boolean if a sub obj is nsfw
    """
    s = db.session.query(Sub).filter_by(name=sub).first()
    if s.nsfw:
        return True
    return False


@cache.memoize(config.DEFAULT_CACHE_TIME)
def normalize_sub(sub):
    """
    if a subname is incorrectly capitalized, correct it
    """
    subl = db.session.query(Sub). \
        filter(func.lower(Sub.name) == func.lower(sub)).first()
    if subl != None:
        return subl.name
    return sub


@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_sub_mods(sub, admin=True):
    """
    returns the list of mods in a given sub
    the optional admin kwarg just also includes admins
    as mods for simplicty sake
    """
    mod_subs = db.session.query(Moderator).filter_by(sub=sub).all()
    if admin == False:
        return [m.username for m in mod_subs]
    admins = db.session.query(Iuser).filter_by(admin=True).all()
    for a in admins:
        mod_subs.append(a)
    return [m.username for m in mod_subs]


##### Username Functions #####
@cache.memoize(config.DEFAULT_CACHE_TIME)
def normalize_username(username, dbuser=False):
    """
    returns a capitalization corrected username normally,
    if dbuser=true is passed, it will return the entire
    user object
    """
    if username is None:
        return False
    username = db.session.query(Iuser) \
    .filter(func.lower(Iuser.username) == func.lower(username)).first()
    if username is not None:
        if dbuser:
            return username
        return username.username
    return False
    

@cache.memoize(config.DEFAULT_CACHE_TIME)
def is_admin(username):
    """
    returns bool if user is admin or not
    """
    if db.session.query(db.session.query(Iuser) \
        .filter_by(admin=True, username=username).exists()).scalar():
        return True
    return False


@cache.memoize(config.DEFAULT_CACHE_TIME)
def is_mod_of(username, sub):
    """
    returns bool if user is mod of a sub
    """
    mods = get_sub_mods(sub)
    username = normalize_username(username)
    if username in [m for m in mods]:
        return True
    return False


@cache.memoize(config.DEFAULT_CACHE_TIME)
def is_mod(obj, username):
    """
    sees if a username is a mod of a post/comment
    the order of args here should be changed
    """
    username = normalize_username(username)
    if hasattr(obj, 'inurl_title'):
        if is_mod_of(username, obj.sub):
            return True

    elif hasattr(obj, 'parent_id'):
        if is_mod_of(username, obj.sub_name):
            return True

    return False

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_post_from_comment_id(cid):
    """
    returns post id from a given comment id
    """
    pid = db.session.query(Comment).filter_by(id=cid).first().post_id
    return db.session.query(Post).filter_by(id=pid).first()

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_user_id_from_username(username):
    return db.session.query(Iuser.id).filter_by(username=username).first()[0]

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_user_karma(username):
    """
    returns a dict with a user's post/comment karma
    """
    username = normalize_username(username)
    user_id = get_user_id_from_username(username)

    user_post_ids = db.session.query(Post.id).filter_by(author_id=user_id, anonymous=False).all()
    user_comment_ids = db.session.query(Comment.id).filter_by(author_id=user_id, anonymous=False).all()

    karma = {'post':0, 'comment':0}


    for pid in user_post_ids:
        try:
            karma['post'] += db.session.query(Vote.vote).filter_by(post_id=pid[0]).first()[0]
        except TypeError:
            pass
    for cid in user_comment_ids:
        try:
            karma['comment'] += db.session.query(Vote.vote).filter_by(comment_id=cid[0]).first()[0]
        except TypeError:
            pass

    return karma

