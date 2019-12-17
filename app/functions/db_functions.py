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

##### Useful jinja2 template functions #####
def set_language(lang=config.DEFAULT_LANGUAGE):
    """
    in future this will user geoip
    """
    session['language'] = lang
    return lang

def get_word(word, language=None, cap=None, cap_all=False):
    """
    multi language support
    """
    capitalize = cap

    if language is None:
        language = session['language']

    word = word.lower()
    language = language.lower()

    if word in LANG.keys():
        if language in LANG[word].keys():
            new_word = LANG[word][language]
            if cap_all:
                new_word = ' '.join(
                                [(x[0].upper() + x[1:]) for x in new_word.split()]
                                )
                return new_word

            elif capitalize is not None:
                new_word = list(new_word)
                for c in capitalize:
                    new_word[c] = new_word[c].upper()

                return ''.join(new_word)

            else:
                return new_word

    return word

app.jinja_env.globals.update(get_word=get_word)

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_style(sub=None):
    """
    returns sub style for a given sub
    """
    if sub is not None:
        sub = db.session.query(Sub).filter_by(name=normalize_sub(sub)).first()
        if sub is None:
            return abort(404)
        return sub.css
    return None

app.jinja_env.globals.update(get_style=get_style)

def param_replace(url_params, param_name, replace_with):
    """
    replaces a given param with a string and returns as param args
    """
    if url_params == '':
        return param_name + '=' + replace_with
    url_params = url_params.split('&')
    url_params = [param for param in url_params if param.split('=')[0] != param_name]
    url_params.append(param_name + '=' + replace_with)

    url_params = '&'.join(url_params)
    url_params = url_params.replace('?', '')

    if url_params == '':
        return ''

    return url_params

app.jinja_env.globals.update(param_replace=param_replace)

def param_destroy(url_params, param_name, params_only=False):
    """
    returns param args with a specific param removed
    """
    url_params = url_params.split('&')
    url_params = [param for param in url_params if param.split('=')[0] != param_name and param != '']

    url_params = '&'.join(url_params)

    if url_params == '':
        return ''

    if params_only:
        return url_params
    return '?' + url_params


app.jinja_env.globals.update(param_destroy=param_destroy)

def offset_url(url_params, url_type=None, params_only=False, offset_by=15):
    """
    returns creates the urls used in prev/next
    """
    current_offset = None
    url_params = url_params.split('&')
    for param in url_params:
        if param.split('=')[0] == 'offset':
            current_offset = int(param.split('=')[1])

    url_params = [param for param in url_params if param.split('=')[0] != 'offset' and param != '']

    if current_offset is None and url_type == 'next':
        url_params.append('offset=15')

    elif url_type == 'next':
        if current_offset is None:
            current_offset = 15
        else:
            current_offset = current_offset + 15
        url_params.append('offset=' + str(current_offset))

    elif url_type == 'prev':
        current_offset = current_offset - 15
        if current_offset > 0:
            url_params.append('offset=' + str(current_offset))

    elif url_type == 'explore':
        if current_offset is None:
            current_offset = 100
        else:
            current_offset = current_offset + 100
        url_params.append('offset=' + str(current_offset))

    elif url_type is None:
        if current_offset is None:
            current_offset = offset_by
        else:
            current_offset = current_offset + offset_by
        url_params.append('offset=' + str(current_offset))

    url_params = '&'.join(url_params)

    if url_params == '':
        return ''

    if params_only:
        return url_params
    return '?' + url_params

app.jinja_env.globals.update(offset_url=offset_url)


##### Sub Functions #####
@cache.memoize(config.DEFAULT_CACHE_TIME)
def is_sub_nsfw(sub):
    """
    returns a boolean if a sub obj is nsfw
    """
    s = db.session.query(Sub).filter_by(name=sub).first()
    if hasattr(s, 'nsfw'):
        if s.nsfw:
            return True
        return False
    return False

@cache.memoize(config.DEFAULT_CACHE_TIME)
def normalize_sub(sub, return_obj=False):
    """
    if a subname is incorrectly capitalized, correct it
    """
    subl = db.session.query(Sub). \
        filter(func.lower(Sub.name) == func.lower(sub)).first()

    if subl is not None:
        if not return_obj:
            return subl.name
        return sub
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

app.jinja_env.globals.update(get_sub_mods=get_sub_mods)

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

app.jinja_env.globals.update(get_sub_mods=get_sub_mods)

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_sub_title(sub):
    """
    this is mainly a function for caching purposes
    """
    sub = normalize_sub(sub)
    title = db.session.query(Sub.title).filter_by(name=sub).first()
    if title is not None:
        return title[0]
    return None

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_muted_subs():
    """
    this returns of lists of subs to not show in the main
    index page/all page due to spam or some TRULY horrible content
    """
    return [x.name for x in db.session.query(Sub).filter_by(muted=True).all()]

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_unique_sub_users(sub, today=False):
    """
    returns all users to ever participate in a sub
    """
    users = db.session.query(Post.author).filter_by(sub=sub). \
            distinct(Post.author).group_by(Post.author).all()
    users = [u[0] for u in users]

    comments = db.session.query(Comment.author).filter_by(sub_name=sub). \
            distinct(Comment.author).group_by(Comment.author).all()

    [users.append(c[0]) for c in comments if c[0] not in users]

    return users

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_explore_stats(sub, today=False):
    """
    stats used in explore
    """
    users = []

    posts = db.session.query(Post.id, Post.author_id).filter_by(sub=sub).all()
    [users.append(p[1]) for p in posts if p[1] not in users]

    comments = db.session.query(Comment.id, Comment.author_id).filter_by(sub_name=sub).all()
    [users.append(c[1]) for c in comments if c[1] not in users]

    return (sub, len(users), len(posts), len(comments))

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_explore_subs(offset=0, limit=50):
    """
    one of the best current targets for optimization
    """
    subs = db.session.query(Sub).outerjoin(Comment). \
            group_by(Sub).order_by(func.count(Comment.sub_name).desc()). \
            limit(limit).offset(offset).all()

    for s in subs:
        s.stats = get_explore_stats(s.name) 

    return subs

##### Username Functions #####
@cache.memoize(config.DEFAULT_CACHE_TIME)
def normalize_username(username, dbuser=False):
    """
    returns a capitalization corrected username normally,
    if dbuser=true is passed, it will return the entire
    user object
    """
    if username is None:
        return None

    username = db.session.query(Iuser). \
                filter(func.lower(Iuser.username) == func.lower(username)).first()

    if username is not None:
        if dbuser:
            return username
        return username.username
    return None


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
def user_id_from_username(username):
    """
    returns just the id of an user
    """
    return db.session.query(Iuser.id).filter_by(username=username).first()[0]

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_user_karma(username):
    """
    returns a dict with a user's post/comment karma
    """
    username = normalize_username(username)
    user_id = user_id_from_username(username)

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

@cache.memoize(config.DEFAULT_CACHE_TIME)
def has_messages(username):
    """
    checks to see if this username has any unread messages
    """
    if 'username' in session:
        messages = db.session.query(Message).filter_by(sent_to=username, read=False).all()


        for m in range(len(messages)):
            messages[m].sender_id = user_id_from_username(messages[m].sender)

        messages = [m for m in messages if m.sender_id not in session['blocked']['other_user']]
        messages = len(messages)

        if messages is not None:
            if messages > 0:
                session['unread_messages'] = messages
                return True
        else:
            session['unread_messages'] = None
    return False

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_banned_subs(username):
    username = normalize_username(username)
    """
    returns a list of banned subs for a username
    """
    subs = db.session.query(Ban).filter_by(username=username).all()
    banned = []
    for s in subs:
        banned.append(s.sub)
    return banned

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_blocked(username=None):
    """
    returns a dict of comments/posts/users this username has blocked
    """
    
    if username is not None:
        username = normalize_username(username)

    bdict = {'comment_id':[], 'post_id':[], 'other_user':[], 'anon_user':[]}
    if username is None:
        return bdict

    blocked = db.session.query(Hidden).filter_by(username=username).all()

    if blocked == []:
        return bdict

    for b in blocked:
        if b.comment_id is not None:
            i = db.session.query(Comment.id).filter_by(id=b.comment_id).first()
            if i is not None:
                if i[0] not in bdict['post_id']:
                    bdict['comment_id'].append(i[0])

        elif b.post_id is not None:
            i = db.session.query(Post.id).filter_by(id=b.post_id).first()
            if i is not None:
                if i[0] not in bdict['post_id']:
                    bdict['post_id'].append(i[0])

        elif b.other_user is not None:
            if b.anonymous:
                i = db.session.query(Iuser.anon_id).filter_by(anon_id=b.other_user).first()
            else:
                i = db.session.query(Iuser.id).filter_by(id=b.other_user).first()
            if i is not None:
                if b.anonymous is not True:
                    if i[0] not in bdict['other_user']:
                        bdict['other_user'].append(i[0])
                else:
                    if i[0] not in bdict['anon_user']:
                        bdict['anon_user'].append(i[0])

    return bdict


@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_pgp_from_username(username):
    """
    returns a pgp object for a username
    """
    u = normalize_username(username)

    pgp = db.session.query(Pgp).filter_by(username=normalize_username(username)).first()

    if pgp != None:
        return pgp
    return None


@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_user_from_username(username):
    """
    returns an user object given a username
    """
    return normalize_username(username, dbuser=True)


@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_user_from_id(uid):
    """
    returns user object from just an id
    """
    return db.session.query(Iuser).filter_by(id=uid).first()


@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_message_count(username):
    """
    returns user message counts, planningj on adding this
    somewhere in the message ui
    """
    username = normalize_username(username)
    return db.session.query(Message.id).filter_by(sender=username).count()

@cache.memoize(config.DEFAULT_CACHE_TIME)
def recent_user_comments(user, limit=15, deleted=False):
    """
    returns x recent comments for a user, works both with obj and just name
    """
    if isinstance(user, str):
        aid = normalize_username(username, dbuser=True)
        aid = aid.id
    else:
        aid = user.id

    coms = db.session.query(Comment).filter_by(author_id=aid, deleted=deleted). \
                                    order_by(Comment.created.desc()).limit(limit).all()
    return coms


@cache.memoize(config.DEFAULT_CACHE_TIME)
def recent_user_posts(user, limit=15, deleted=False):
    """
    returns x recent posts for a user, works both with obj and just name
    """
    if isinstance(user, str):
        aid = normalize_username(username, dbuser=True)
        aid = aid.id
    else:
        aid = user.id

    posts = db.session.query(Post).filter_by(author_id=aid, deleted=deleted). \
                                    order_by(Post.created.desc()).limit(limit).all()

    return posts



##### Post/Comment Functions #####

@cache.memoize(config.DEFAULT_CACHE_TIME)
def hide_blocked(obj):
    """
    prevents blocked users from also being blocked
    on their anonymous/non-anonymous posts to avoid
    de-anonymization
    """
    show = []
    if 'username' not in session:
        return obj
    session['blocked'] = get_blocked(session['username'])

    for o in obj:
        user = get_user_from_id(o.author_id)
        if o.anonymous:
            if user.anon_id not in session['blocked']['anon_user']:
                show.append(o)
        else:
            if user.id not in session['blocked']['other_user']:
                show.append(o)

    return show
