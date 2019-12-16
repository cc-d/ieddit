"""
Main ieddit code.

TODO: split this up into different views, function groups, etc.
"""
from share import *
from sqlalchemy import func, or_, and_
import _thread

import requests
from bs4 import BeautifulSoup
import urllib.parse

abs_path = os.path.abspath(os.path.dirname(__file__))
os.chdir(abs_path)
app.static_folder = 'static'

@app.before_request
def before_request():
    g.cache_bust = cache_bust

    if app.debug:
        g.start = time.time()

    if 'blocked_subs' not in session:
        if 'username' in session:
            session['blocked_subs'] = get_blocked_subs(session['username'])
        else:
            session['blocked_subs'] = []

    request.is_mod = False

    try:
        # gunicorn uses a different dict value
        req_uri = request.environ['REQUEST_URI']
    except KeyError as e:
        req_uri = request.environ['RAW_URI']

    # if in a sub, modify request to reflect
    if len(req_uri) >= 3:
        if req_uri[:3] == '/i/':
            current_sub = re.findall(r'\/i\/([a-zA-Z0-9-_]*)', req_uri)
            if len(current_sub) == 1:
                current_sub = current_sub[0]
                if current_sub != 'all':
                    request.sub = normalize_sub(current_sub)
                    #request.in_nsfw_sub = is_sub_nsfw(request.sub)
                    if 'username' in session:
                        # if a user is a mod of this sub, it changes how we respond
                        # to requests rather significantly
                        if session['username'] in get_sub_mods(request.sub):
                            request.is_mod = True

                    request.sub_title = get_sub_title(request.sub)


    # last significant request URI


    if 'username' in session:
        session['blocked'] = get_blocked(session['username'])
        has_messages(session['username'])
    else:
        if 'blocked' not in session:
            session['blocked'] = {'comment_id':[], 'post_id':[], 'other_user':[], 'anon_user':[]}

@app.after_request
def apply_after(response):
    """
    while this makes locked transactions and the like
    easy to deal with, it's very important to remember
    that modify an exting attribute on an sqlalchemy object directly
    will cause the modified object to be comitted to db
    """

    if response.status_code == 500:
        db.session.rollback()

    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers['X-Content-Type-Options'] = 'nosniff'

    if config.CSP:
        response.headers['Content-Security-Policy'] = "default-src 'self' *.ieddit.com ieddit.com; img-src *; style-src" +\
        " 'self' 'unsafe-inline' *.ieddit.com ieddit.com; script-src 'self' 'unsafe-inline' *.ieddit.com ieddit.com;"

    if app.debug:
        if hasattr(g, 'start'):
            load_time = str(time.time() - g.start)
            print('\n[Load: %s]' % load_time)

    # gotta setup proper cache clearing :)
    if request.environ['REQUEST_METHOD'] == 'POST':
        cache.clear()

    response.cache_control.private = True
    response.cache_control.public = False

    if hasattr(request, 'sub'):
        session['last_sub'] = request.sub

    # last visited url which isn't a static file
    if request.method == 'GET':
        session['last_url'] = get_last_url(request.environ['RAW_URI'])

    return response

@app.teardown_request
def teardown_request(exception):
    """
    same as above, do not modify pre-existing attributes
    on sqlalchemy objects or the modified objects will be
    committed to the db
    """
    if exception:
        db.session.rollback()
    db.session.remove()

@app.errorhandler(Exception)
def handle_error(error):
    title = str(error)
    trace_back = traceback.format_exc()
    code = 500

    if isinstance(error, HTTPException):
        code = error.code
        description = error.description

    complete_error = str(request.method) + ' ' + str(request.url) + \
                     '\n' + title + '\n' + str(trace_back)

    if code >= 500:
        description = "{}" \
        .format(str(error)  or 'unknown error')

        logger.error(complete_error)

        if config.DISCORD_ENABLED:
            send_discord_msg(title=title, description=complete_error)

    return render_template("error.html", error=description, code=code), code

def not_banned(f):
    """
    this decorator handles site-wide banned users
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session and api is False:
            return redirect(url_for('login'))
        busers = db.session.query(Iuser).filter_by(banned=True).all()
        bnames = [a.username for a in busers]

        if api is False:
            if session['username'] in bnames:
                return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

def require_login(f):
    """
    this decorator forces a user to have an account
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session['username'] if 'username' in session else None
        if username is None:
            flash('please login to use this feature', 'danger')
            return get_last_url()
        return f(*args, **kwargs)
    return decorated_function


def send_email(etext=None, subject=None, to=None, from_domain=config.MAIL_FROM):
    """
    sends the recovery email
    """
    if config.MAIL_TYPE == 'mailgun':
        etext = '<html><head><body>' + etext + '</body></html>'
        r = requests.post(config.MG_URL + '/messages',
            auth=('api', config.MG_API_KEY),
            data={'from': 'no-reply <%s>' % (from_domain),
                'to': [to, from_domain], 'subject':subject, 'html':etext})
        return True

@app.route('/suggest_title')
@limiter.limit("5/minute")
def suggest_title(url=None):
    """
    real basic title suggestion, important to proxy this if
    you want to prevent ip leaks
    """
    url = request.args.get('u')
    url = urllib.parse.unquote(url)
    r = requests.get(url, proxies=config.PROXIES)
    if r.status_code == 200:
        try:
            soup = BeautifulSoup(r.text)
            title = soup.find('meta', property='og:title')
            if title != None:
                title = title.get('content', None)
                return title
            else:
                return soup.title.string
        except Exception as e:
            return ''
    return ''


##### Static Files #####

@app.route('/fonts/<file>')
def send_font(file=None, methods=['GET']):
    if file != None:
        if len(re.findall('^.*.*$', file)) != 1:
            return str(re.findall('^.*.*$'))
        else:
            return app.send_static_file(file)
    else:
        return abort(403)

@app.route('/sitemap.xml')
def sitemap():
    return app.send_static_file('sitemap.xml')

@app.route('/robots.txt')
def robotstxt():
    return app.send_static_file('robots.txt')

@app.route('/r/<sub>/', methods=['GET'])
def redirect_to_i(sub=None):
    sub = normalize_sub(sub)
    if sub is None:
        return abort(404)
    return redirect('/i/%s' % sub)

@limiter.limit(config.LOGIN_RATE_LIMIT)
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username is None or password is None:
            flash('Username or Password missing.', 'danger')
            return redirect(url_for('login'))

        if username == '' or password == '' or len(username) > 20 or len(password) > 100:
            flash('Username or Password empty or too long.', 'danger')
            return redirect(url_for('login'))

        username = normalize_username(username)
        if username is None:
            flash('user does not exist', 'danger')
            return redirect(url_for('login'))

        if db.session.query(db.session.query(Iuser)
                .filter_by(username=username)
                .exists()).scalar():
            login_user = db.session.query(Iuser).filter_by(username=username).first()
            hashed_pw = login_user.password
            if check_password_hash(hashed_pw, password):
                logout()
                [session.pop(key) for key in list(session.keys())]


                session['username'] = login_user.username
                session['user_id'] = login_user.id

                if login_user.admin:
                        session['admin'] = login_user.admin

                session['hide_sub_style'] = login_user.hide_sub_style

                if hasattr(login_user, 'anonymous'):
                    if login_user.anonymous:
                        session['anonymous'] = True

                if get_pgp_from_username(login_user.username):
                    session['pgp_enabled'] = True

                return redirect(url_for('index'), 302)

        flash('Username or Password incorrect.', 'danger')
        return redirect(url_for('login'), 302)

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect(url_for('index'), 302)

@limiter.limit(config.REGISTER_RATE_LIMIT)
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if 'username' in session:
            flash('already logged in', 'danger')
            return redirect('/')

        if username is None or password is None:
            flash('username or password missing', 'danger')
            return redirect(url_for('login'))

        if verify_username(username):
            if db.session.query(db.session.query(Iuser).filter(func.lower(Iuser.username) == func.lower(username)).exists()).scalar():
                flash('username exists', 'danger')
                return redirect(url_for('login'))
        else:
            flash('invalid username', 'danger')
            return redirect(url_for('login'))

        if len(password) > 100 or len(password) < 1:
            flash('password length invalid', 'danger')
            return redirect(url_for('login'))

        if email != None and email != '':
            if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                flash('invalid email', 'danger')
                return redirect(url_for('login'))

        new_user = Iuser(username=username, email=email,
            password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        logout()
        session['username'] = new_user.username
        session['user_id'] = new_user.id

        return redirect(config.URL, 302)

@app.route('/')
def index():
    return subi(subi='all', nsfw=False)

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_subi(subi, user_id=None, view_user_id=None, posts_only=False, deleted=False,
             offset=0, limit=15, nsfw=True, d=None, s=None, api=False):
    """
    this is one of the horrific functions i will be rewriting next
    """
    if offset is None:
        offset = 0
    offset = int(offset)

    muted_subs = False

    if d == 'hour':
        ago = datetime.now() - timedelta(hours=1)
    elif d == 'day':
        ago = datetime.now() - timedelta(hours=24)
    elif d == 'week':
        ago = datetime.now() - timedelta(days=7)
    elif d == 'month':
        ago = datetime.now() - timedelta(days=31)
    elif d == 'year':
        ago = datetime.now() - timedelta(days=365)
    else:
        ago = datetime.now() - timedelta(days=9999)

    if subi != 'all':
        subname = db.session.query(Sub).filter(func.lower(Sub.name) == subi.lower()).first()
        if subname == None:
            return pretty_json({'error':'sub does not exist'})
        subi = subname.name
        posts = db.session.query(Post).filter_by(sub=subi, deleted=False).filter(Post.created > ago)
    elif user_id != None:
        muted_subs = get_muted_subs()
        posts = db.session.query(Post).filter_by(author_id=user_id, deleted=False).filter(Post.created > ago)
    else:
        muted_subs = get_muted_subs()
        posts = db.session.query(Post).filter_by(deleted=False).filter(Post.created > ago)

    request.is_more_content = False
    if posts.count() >= limit:
        request.is_more_content = True

    if s == 'top':
        posts = posts.order_by((Post.ups - Post.downs).desc())
        posts = posts.all()
    elif s == 'new':
        posts = posts.order_by((Post.created).desc())
        posts = posts.all()
    else:
        posts = posts.all()
        for p in posts:
            p.hot = hot(p.ups, p.downs, p.created)
        posts.sort(key=lambda x: x.hot, reverse=True)
    
    posts = [post for post in posts if post.created > ago]


    if muted_subs:
        posts = [c for c in posts if c.sub not in muted_subs]

    if nsfw == False:
        posts = [p for p in posts if p.nsfw == False]

    more = False
    pc = len(posts)
    if pc > limit:
        more = True

    if api is False:
        if 'blocked_subs' in session and 'username' in session:
            posts = [c for c in posts if c.sub not in session['blocked_subs']]

        if 'blocked' in session:
            posts = [post for post in posts if post.id not in session['blocked']['post_id']]
            posts = hide_blocked(posts)

    posts = posts[offset:offset+limit]

    stid = False
    for p in posts:
        if p.stickied == True:
            stid = p.id

    if subi != 'all':
        if stid:
            posts = [post for post in posts if post.id != stid]

    if subi != 'all':
        sticky = db.session.query(Post).filter(func.lower(Post.sub) == subi.lower(), Post.stickied == True).first()
        if sticky:
            if 'blocked_subs' in session and api is False:
                if sticky.sub in session['blocked_subs']:
                    pass
                else:
                    posts.insert(0, sticky)
            else:
                posts.insert(0, sticky)

    p = []
    for post in posts:
        if is_sub_nsfw(post.sub):
            post.sub_nsfw = True
        else:
            post.sub_nsfw = False

        if hasattr(post, 'text'):
            post.new_text = pseudo_markup(post.text)
        if thumb_exists(post.id):
            post.thumbnail = 'thumbnails/thumb-' + str(post.id) + '.PNG'

        if post.url != None:
            youtube_url = get_youtube_embed_url(post.url)
            if youtube_url:
                post.video = youtube_url

        post.mods = get_sub_mods(post.sub)
        post.created_ago = time_ago(post.created)
        if subi != 'all':
            post.site_url = config.URL + '/i/' + subi + '/' + str(post.id) + '/' + post.inurl_title
        post.remote_url_parsed = post_url_parse(post.url)
        post.comment_count = db.session.query(Comment).filter_by(post_id=post.id).count()

        if 'username' in session and api is False:
            v = post.get_has_voted(session['user_id'])
            if v != None:
                post.has_voted = str(v.vote)

            if is_mod_of(session['username'], post.sub):
                post.is_mod = True

        if api:
            comments = db.session.query(Comment).filter_by(post_id=post.id, deleted=False).all()
            post.comments = [sqla_to_dict(c) for c in comments]

        p.append(post)

    if api is True:
        p = [sqla_to_dict(post, include_attrs=['comments']) for post in p]

        return pretty_json(p)

    return p

@app.route('/i/<subi>/')
def subi(subi, user_id=None, posts_only=False, offset=0,
        limit=15, nsfw=True, s=None, d=None):
    offset = request.args.get('offset')
    d = request.args.get('d')
    s = request.args.get('s')

    subi = normalize_sub(subi)
    if subi is None:
        return abort(404)

    # ensure caching does not cache another user's post view
    view_user_id = None
    if 'user_id' in session:
        view_user_id = session['user_id']

    sub_posts = get_subi(subi=subi, view_user_id=view_user_id,
                        posts_only=posts_only, deleted=False, user_id=user_id,
                        offset=offset, limit=15, d=d, s=s, nsfw=nsfw)

    if isinstance(sub_posts, bool):
        return []

    if type(sub_posts) == dict:
        if 'error' in sub_posts.keys():
            flash(sub_posts['error'], 'danger')
            return redirect('/')

    for p in sub_posts:
        if hasattr(p, 'self_text'):
            if p.self_text != None:
                p.new_self_text = pseudo_markup(p.self_text)

    if posts_only:
        return sub_posts

    sub_stats = get_top_stats(subi)
    if subi == 'all' and nsfw == True:
        is_all = True
    else:
        is_all = False

    return render_template('sub.html', posts=sub_posts, url=config.URL, sub_stats=sub_stats, is_all=is_all)


@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_cached_children(comment, show_deleted=True):
    return comment.get_children(show_deleted=show_deleted)

@cache.memoize(config.DEFAULT_CACHE_TIME)
def recursive_children(comment=None, current_depth=0, max_depth=8, show_deleted=True):
    found_children = []
    found_children.append(comment)

    children = comment.get_children(show_deleted=show_deleted).all()

    while len(children) > 0 and current_depth < max_depth :
        for c in children:
            if c not in found_children:
                found_children.append(c)
                c2 = c.get_children(show_deleted=show_deleted).all()
                if c2 != None:
                    [children.append(c3) for c3 in c2]
            ex = [x for x in children if x != c]
        children = ex
        current_depth += 1

    return found_children

@cache.memoize(config.DEFAULT_CACHE_TIME)
def c_get_comments(sub=None, post_id=None, inurl_title=None, comment_id=False, sort_by=None, comments_only=False, user_id=None, cache_for=None):
    post = None
    parent_comment = None
    if not comments_only:
        if post_id != None:
            post = db.session.query(Post).filter_by(id=post_id).first()
            post.mods = get_sub_mods(post.sub)
            post.comment_count = db.session.query(Comment).filter_by(post_id=post.id).count()
            post.created_ago = time_ago(post.created)
            post.remote_url_parsed = post_url_parse(post.url)

            if is_sub_nsfw(post.sub):
                post.sub_nsfw = True
            else:
                post.sub_nsfw = False

            if hasattr(post, 'text'):
                post.new_text = pseudo_markup(post.text)
            if thumb_exists(post.id):
                post.thumbnail = 'thumbnails/thumb-' + str(post.id) + '.PNG'
            elif hasattr(post, 'url'):
                post.thumbnail = 'globe.png'


            if hasattr(post, 'self_text'):
                if post.self_text != None:
                    post.new_self_text = pseudo_markup(post.self_text)

            if post.url != None:
                youtube_url = get_youtube_embed_url(post.url)
                if youtube_url:
                    post.video = youtube_url
        else:
            post = None

        if 'user_id' in session:
            post.has_voted = post.get_has_voted(session['user_id'])
            if post.has_voted != None:
                post.has_voted = str(post.has_voted.vote)

        if comment_id == None:
            comments = db.session.query(Comment).filter_by(post_id=post_id).all()
            show_blocked = False

        else:
            comments = []
            parent_comment = db.session.query(Comment).filter_by(id=comment_id).first()
            show_blocked = False

            # if direct link, just show it
            if parent_comment.id in session['blocked']['comment_id'] or \
                parent_comment.author_id in session['blocked']['other_user']:

                flash('you are viewing a comment you have blocked', 'danger')
                show_blocked = True

            comments = recursive_children(comment=parent_comment)

    else:
        comments = db.session.query(Comment).filter(Comment.author_id == user_id,
        Comment.deleted == deleted).order_by(Comment.created.desc()).all()
        show_blocked = False

    if 'blocked_subs' in session and 'username' in session:
        comments = [c for c in comments if c.sub_name not in session['blocked_subs']]

    if 'blocked' in session and show_blocked != True and 'username' in session:
        comments = [c for c in comments if c.id not in session['blocked']['comment_id']]
        comments = hide_blocked(comments)

    for c in comments:
        c.score = (c.ups - c.downs)
        c.new_text = pseudo_markup(c.text)
        c.mods = get_sub_mods(c.sub_name)
        c.created_ago = time_ago(c.created)
        if 'user_id' in session:
            c.has_voted = db.session.query(Vote).filter_by(comment_id=c.id, user_id=session['user_id']).first()
            if c.has_voted != None:
                c.has_voted = c.has_voted.vote

    return comments, post, parent_comment

@app.route('/i/<sub>/<post_id>/<inurl_title>/<comment_id>/')
@app.route('/i/<sub>/<post_id>/<inurl_title>/')
def get_comments(sub=None, post_id=None, inurl_title=None, comment_id=None, sort_by=None, comments_only=False, user_id=None):
    if sub == None or post_id == None or inurl_title == None:
        if not comments_only:
            return 'badlink'

    sub = normalize_sub(sub)
    if sub is None:
        abort(404)

    
    try:
        post_id = int(post_id)
        p = db.session.query(Post).filter_by(id=post_id).first()
        if p is None:
            abort(404)
        if comment_id is not None:
            try:
                comment_id = int(comment_id)
                c = db.session.query(Comment).filter_by(id=comment_id).first()
                if c is None:
                    abort(404)
            except ValueError:
                abort(404)
    except ValueError:
        abort(404)


    is_parent = False if comment_id is None else True

    if 'user_id' in session:
        cache_for = session['user_id']
    else:
        cache_for = None

    comments, post, parent_comment = c_get_comments(sub=sub, post_id=post_id, inurl_title=inurl_title,
                                                    comment_id=comment_id, sort_by=sort_by, comments_only=comments_only, 
                                                    user_id=user_id, cache_for=cache_for)

    if post is not None and 'username' in session:
        post.is_mod = True if (is_mod_of(session['username'], post.sub)) else None

    if comments_only:
        return comments

    if not comment_id:
        tree = create_id_tree(comments)
    else:
        tree = create_id_tree(comments, parent_id=comment_id)

    tree = comment_structure(comments, tree)

    last = '%s/i/%s/%s/%s/' % (config.URL, sub, post_id, post.inurl_title)

    if comment_id is not False and comment_id is None:
        last = last + str(comment_id)

    session['last_return_url'] = last

    return render_template('comments.html', comments=comments, post_id=post_id,
                        post_url='%s/i/%s/%s/%s/' % (config.URL, sub, post_id, post.inurl_title),
                        post=post, tree=tree, parent_comment=parent_comment, is_parent=is_parent,
                        config=config)

@cache.memoize(config.DEFAULT_CACHE_TIME)
def list_of_child_comments(comment_id, sort_by=None):
    """
    need to entirely rewrite how comments are handled once everything else is complete
    this sort of recursion KILLS performance, especially when combined with the already
    terrible comment_structure function.
    """
    comments = {}
    current_comments = []
    if sort_by == 'new':
        start = db.session.query(Comment).filter(Comment.parent_id == comment_id, Comment.deleted == False)\
                    .order_by((Comment.created).asc()).all()
    else:
        start = db.session.query(Comment).filter(Comment.parent_id == comment_id, Comment.deleted == False)\
                    .order_by((Comment.ups - Comment.downs).desc()).all()

    for c in start:
        current_comments.append(c.id)
        comments[c.id] = c

    while len(current_comments) > 0:
        for current_c in current_comments:
            if sort_by == 'new':
                get_comments = db.session.query(Comment).filter(Comment.parent_id == current_c)\
                    .order_by((Comment.created).asc()).all()
            else:
                get_comments = db.session.query(Comment).filter(Comment.parent_id == current_c)\
                    .order_by((Comment.ups - Comment.downs).desc()).all()
            for c in get_comments:
                current_comments.append(c.id)
                comments[c.id] = c
            current_comments.remove(current_c)
    return comments

@app.route('/create', methods=['POST', 'GET'])
@not_banned
@limiter.limit(config.SUB_RATE_LIMIT)
def create_sub():
    if request.method == 'POST':
        subname = request.form.get('subname')
        if subname.lower() == 'all':
            flash('reserved name')
            return redirect(url_for('create_sub'))

        if subname != None and verify_subname(subname) and 'username' in session:
            if len(subname) > 30 or len(subname) < 1:
                return 'invalid length'

            already = db.session.query(Sub).filter(func.lower(Sub.name) == subname.lower()).first()
            if already != None:
                flash('sub already exists', 'danger')
                return redirect('/create')

            title = request.form.get('title')
            new_sub = Sub(name=escape(subname), created_by=session['username'], created_by_id=session['user_id'], title=escape(title))
            db.session.add(new_sub)
            db.session.commit()
            new_mod = Moderator(username=new_sub.created_by, sub=new_sub.name)
            db.session.add(new_mod)
            db.session.commit()

            flash('You have created a new sub! Mod actions are under the "info" tab.', 'success')
            return redirect(config.URL + '/i/' + subname, 302)

        if verify_subname(subname) == False:
            flash('Invalid sub name. Valid Characters are A-Z 0-9 - _ ')
            return(redirect(config.URL + '/create'))
        return 'invalid'
    elif request.method == 'GET':
        if 'username' not in session:
            flash('please log in to create subs', 'danger')
            return redirect(url_for('login'))
        return render_template('create.html')

@app.route('/u/<username>/', methods=['GET'])
def view_user(username):
    username = normalize_username(username)
    vuser = db.session.query(Iuser).filter(func.lower(Iuser.username) == func.lower(username)).first()

    if vuser is None:
        abort(404)

    mod_of = db.session.query(Moderator).filter_by(username=vuser.username).all()
    mods = {}

    for s in mod_of:
        mods[s.sub] = s.rank
    vuser.mods = mods

    posts = recent_user_posts(user=vuser)
    comments = recent_user_comments(user=vuser)

    for p in posts:
        p.created_ago = time_ago(p.created)
        p.comment_count = db.session.query(Comment).filter_by(post_id=p.id).count()
        p.mods = get_sub_mods(p.sub)
        if 'user_id' in session:
            v = p.get_has_voted(session['user_id'])
            if v != None:
                p.has_voted = str(v.vote)
        if p.self_text != None:
            p.new_self_text = pseudo_markup(p.self_text)

        p.remote_url_parsed = post_url_parse(p.url)

        if hasattr(p, 'text'):
            p.new_text = pseudo_markup(p.text)
        if thumb_exists(p.id):
            p.thumbnail = 'thumbnails/thumb-' + str(p.id) + '.PNG'

    comments_with_posts = []

    for c in comments:
        c.mods = get_sub_mods(c.sub_name)
        cpost = db.session.query(Post).filter_by(id=c.post_id).first()
        comments_with_posts.append((c, cpost))

        c.new_text = pseudo_markup(c.text)
        c.created_ago = time_ago(c.created)
        if 'user_id' in session:
            c.has_voted = db.session.query(Vote).filter_by(comment_id=c.id, user_id=session['user_id']).first()
            if c.has_voted != None:
                c.has_voted = c.has_voted.vote

    vuser.karma = get_user_karma(username)

    return render_template('user.html', vuser=vuser, posts=posts, url=config.URL, comments_with_posts=comments_with_posts, userpage=True)

@limiter.limit('25 per minute')
@app.route('/vote', methods=['GET', 'POST'])
def vote(post_id=None, comment_id=None, vote=None, user_id=None):
    if request.method == 'POST':
        if post_id == None:
            post_id = request.form.get('post_id')
        if comment_id == None:
            comment_id = request.form.get('comment_id')
        if vote == None:
            vote = request.form.get('vote')
        else:
            vote = str(vote)

        if 'username' not in session or 'user_id' not in session:
            return 'not logged in'
        elif user_id == None:
            user_id = session['user_id']
            username = session['username']

        if comment_id != None and post_id != None:
            return 'cannot vote for 2 objects'

        if comment_id == None and post_id == None:
            return 'no vote object'

        if vote not in ['1', '-1', '0']:
            return 'invalid vote amount'

        vote = int(vote)

        invert_vote = False
        if post_id != None:
            last_vote = db.session.query(Vote).filter_by(user_id=user_id, post_id=post_id).first()
            if last_vote != None:
                if last_vote.vote == vote:
                    return 'already voted'
                else:
                    invert_vote = True

        elif comment_id != None:
            last_vote = db.session.query(Vote).filter_by(user_id=user_id, comment_id=comment_id).first()
            if last_vote != None:
                if last_vote.vote == vote:
                    return 'already voted'
                else:
                    invert_vote = True

        if vote == 0 and last_vote == None:
            return 'never voted'

        if vote == 0:
            if last_vote.post_id is not None or last_vote.comment_id is not None:
                if last_vote.post_id is not None:
                    vpost = db.session.query(Post).filter_by(id=last_vote.post_id).first()
                elif last_vote.comment_id is not None:
                    vpost = db.session.query(Comment).filter_by(id=last_vote.comment_id).first()

                if last_vote.vote == 1:
                    vpost.ups -= 1
                elif last_vote.vote == -1:
                    vpost.downs -= 1

            score = str(vpost.ups - vpost.downs)

            db.session.delete(last_vote)
            db.session.commit()

            return score

        if last_vote == None:
            new_vote = Vote(user_id=user_id, vote=vote, comment_id=comment_id, post_id=post_id)
            db.session.add(new_vote)
            db.session.commit()


        elif invert_vote:
            if last_vote.vote == 1:
                last_vote.vote = -1
            else:
                last_vote.vote = 1
        db.session.commit()

        if comment_id != None:
            vcom = db.session.query(Comment).filter_by(id=comment_id).first()
        elif post_id != None:
            vcom = db.session.query(Post).filter_by(id=post_id).first()

        if vote == 1:
            if not invert_vote:
                vcom.ups += 1
            else:
                vcom.ups += 1
                vcom.downs -= 1

        elif vote == -1:
            if not invert_vote:
                vcom.downs += 1
            else:
                vcom.downs += 1
                vcom.ups -= 1

        db.session.commit()

        return str(vcom.ups - vcom.downs)
    elif request.method == 'GET':
        return 'get'

@app.route('/create_post', methods=['POST', 'GET'])
@limiter.limit(config.POST_RATE_LIMIT)
@not_banned
def create_post(api=False, *args, **kwargs):
    if 'previous_post_form' not in session and not api:
        session['previous_post_form'] = None

    if request.method == 'POST' or api:
        if api:
            username = request.headers['ieddit-username']
            user_id = db.session.query(Iuser).filter_by(username=username).first().id
            title = kwargs['title']
            url = kwargs['url']
            subname = kwargs['sub']
            self_post_text = kwargs['self_post_text']
        else:
            username = session['username']
            user_id = session['user_id']
            title = request.form.get('title')
            url = request.form.get('url')
            subname = request.form.get('sub')
            self_post_text = request.form.get('self_post_text')

        if url is None and len(self_post_text) < 1:
            flash('you must include either text or a URL', 'danger')
            return redirect('/create_post')
        if api is False:
            session['previous_post_form'] = {'title':title, 'url':url, 'sub':subname, 'self_post_text':self_post_text}

        if subname is not None:
            sub_obj = db.session.query(Sub).filter(func.lower(Sub.name) == func.lower(subname)).first()
            if sub_obj is None:
                flash('invalid sub', 'danger')
                return redirect('/create_post')
        else:
            flash('did not include a sub', 'danger')
            return redirect('/create_post')

        if sub_obj is None:
            flash('that sub does not exist', 'danger')
            return redirect('/create_post')

        nsfw = True if sub_obj.nsfw else False

        anonymous = request.form.get('anonymous')

        anonymous = True if anonymous is not None else False

        if len(self_post_text) > 0:
            post_type = 'self_post'
        elif len(url) > 0:
            post_type = 'url'
        else:
            flash('invalid post type, not url or self', 'danger')
            return redirect(url_for('create_post'))

        if api is False:
            if title is None or 'username' not in session or 'user_id' not in session:
                flash('invalid post, no title/username/uid', 'danger')
                return redirect(url_for('create_post'))

        if len(title) > 400 or len(title) < 1 or len(sub_obj.name) > 30 or len(sub_obj.name) < 1:
            flash('invalid title/sub length', 'danger')
            return redirect(url_for('create_post'))

        deleted = True if sub_obj.name in get_banned_subs(username) else False

        override = False if request.form.get('override') is None else True

        if post_type == 'url':
            if len(url) > 2000 or len(url) < 1:
                flash('invalid url length', 'danger')
                return redirect(url_for('create_post'))

            prot = re.findall('^https?:\/\/', url)
            if len(prot) != 1:
                url = 'https://' + url
            new_post = Post(url=url, title=title, inurl_title=convert_ied(title), author=username,
                        author_id=user_id, sub=sub_obj.name, post_type=post_type, anonymous=anonymous, nsfw=nsfw,
                        deleted=deleted, override=override)

        elif post_type == 'self_post':
            if len(self_post_text) > 20000 or len(self_post_text) < 1:
                flash('invalid self post length', 'danger')
                return redirect(url_for('create_post'))

            new_post = Post(self_text=self_post_text, title=title, inurl_title=convert_ied(title),
                author=username, author_id=user_id, sub=sub_obj.name, post_type=post_type, anonymous=anonymous, nsfw=nsfw,
                deleted=deleted, override=override)

        db.session.add(new_post)
        db.session.commit()

        # Forget why this was done this way.
        if post_type == 'url':
            _thread.start_new_thread(os.system, ('python3 utilities/get_thumbnail.py %s "%s"' % (str(new_post.id), urllib.parse.quote(url)),))

        new_post.permalink = config.URL + '/i/' + new_post.sub + '/' + str(new_post.id) + '/' + new_post.inurl_title +  '/'

        if is_admin(username) and anonymous is False:
            new_post.author_type = 'admin'
        elif is_mod(new_post, username) and anonymous is False:
            new_post.author_type = 'mod'

        db.session.commit()

        url = new_post.permalink

        new_vote = Vote(post_id=new_post.id, vote=1, user_id=user_id, comment_id=None)
        db.session.add(new_vote)

        new_post.ups += 1

        db.session.add(new_post)
        db.session.commit()

        if 'previous_post_form' in session and api is False:
            session['previous_post_form'] = None

        if api:
            return sqla_to_dict(new_post)

        return redirect(url)

    if request.method == 'GET' and not api:
        if 'username' not in session:
            flash('please log in to create new posts', 'danger')
            return redirect(url_for('login'))
        else:
            username = session['username']

        if request.referrer:
            subref = re.findall(r'\/i\/([a-zA-z0-9-_]*)', request.referrer)

        sppf = session['previous_post_form']
        session['previous_post_form'] = None

        return render_template('create-post.html', sppf=sppf)

@app.route('/get_sub_list', methods=['GET'])
def get_sub_list():
    '''
    gets sub suggestion dropdown when creating a new post    
    '''
    subs = get_explore_subs(limit=30)

    sublinks = ['<a class="dropdown-item sublist-dropdown"' + \
                ' href="javascript:setSub(\'%s\')">/i/%s</a>' % (s.name, s.name) 
                for s in subs]

    return '\n'.join(sublinks)


@limiter.limit(config.COMMENT_RATE_LIMIT)
@app.route('/create_comment', methods=['POST'])
@not_banned
def create_comment(api=False, *args, **kwargs):
    text = request.form.get('comment_text')
    post_id = request.form.get('post_id')
    post_url = request.form.get('post_url')
    parent_id = request.form.get('parent_id')
    sub_name = request.form.get('sub_name')
    anonymous = request.form.get('anonymous')
    override = request.form.get('override')

    if api:
        username = request.headers['ieddit-username']
        user_id = db.session.query(Iuser).filter_by(username=username).first().id
        parent_type = kwargs['parent_type']
        parent_id = kwargs['parent_id']
        anonymous = kwargs['anonymous']
        override = kwargs['override']

        if parent_type == 'comment':
            post_obj = get_post_from_comment_id(parent_id)
        else:
            post_obj = db.session.query(Post).filter_by(id=parent_id).first()
            parent_id = None

        post_id = post_obj.id
        sub_name = post_obj.sub
        text = kwargs['text']
    else:
        username = session['username']
        user_id = session['user_id']

    if anonymous != None:
        anonymous = True
    else:
        anonymous = False

    if parent_id == '':
        parent_id = None

    if post_url != None and api is False:
        if post_url_parse(post_url) != post_url_parse(config.URL):
            flash('bad origin url', 'danger')
            return redirect(request.referrer or '/')

    if 'username' not in session and api is False:
        flash('not logged in', 'danger')
        return redirect(post_url)

    elif text == None or post_id == None or sub_name == None:
        flash('bad comment', 'danger')
        if api is False:
            return redirect(post_url)

    if parent_id != None:
        level = (db.session.query(Comment).filter_by(id=parent_id).first().level) + 1
    else:
        level = None

    post = db.session.query(Post).filter_by(id=post_id).first()
    if post.locked == True and api is False:
        flash('post is locked', 'danger')
        return redirect(post.get_permalink())

    deleted = False

    sub = normalize_sub(sub_name)
    if sub in get_banned_subs(username):
        deleted = True

    sub_name = sub

    if override != None:
        override = True
    else:
        override = False


    if is_admin(username) and anonymous is False:
        author_type = 'admin'
    elif is_mod(post.sub, username) and anonymous is False:
        author_type = 'mod'
    elif is_mod_of(username, sub_name):
        author_type = 'mod'
    else:
        author_type = 'user'



    new_comment = Comment(post_id=post_id, sub_name=sub_name, text=text,
        author=username, author_id=user_id, parent_id=parent_id, level=level,
        anonymous=anonymous, deleted=deleted, override=override, author_type=author_type)

    db.session.add(new_comment)
    db.session.commit()

    new_comment.permalink = post.get_permalink() +  str(new_comment.id)

    db.session.add(new_comment)
    db.session.commit()

    new_vote = Vote(comment_id=new_comment.id, vote=1, user_id=user_id, post_id=None)
    db.session.add(new_vote)

    new_comment.ups += 1
    db.session.add(new_comment)

    db.session.commit()

    sender = new_comment.author


    if new_comment.parent_id and not deleted:
        cparent = db.session.query(Comment).filter_by(id=new_comment.parent_id).first()
        if cparent.author != username:
            new_message = Message(title='comment reply', text=new_comment.text, sender=sender, sender_type=new_comment.author_type,
                sent_to=cparent.author, in_reply_to=new_comment.permalink, anonymous=anonymous)
            db.session.add(new_message)
            db.session.commit()
    else:
        if not deleted:
            if post.author != username:
                new_message = Message(title='comment reply', text=new_comment.text, sender=sender, sender_type=new_comment.author_type,
                    sent_to=post.author, in_reply_to=post.get_permalink(), anonymous=anonymous)
                db.session.add(new_message)
                db.session.commit()

    flash('created new comment', 'success')

    if api:
        return sqla_to_dict(new_comment)
    return redirect(post_url, 302)

def send_message(title=None, text=None, sent_to=None, sender=None, in_reply_to=None, encrypted=False, encrypted_key_id=None):
    new_message = Message(title=title, text=text, sent_to=sent_to, sender=sender,
        in_reply_to=in_reply_to, encrypted=encrypted, encrypted_key_id=encrypted_key_id)
    db.session.add(new_message)
    db.session.commit()


@app.route('/u/<username>/messages/', methods=['GET'])
def user_messages(username=None, offset=0):
    if 'username' not in session or username == None:
        flash('not logged in', 'danger')
        return redirect(url_for('login'))
    else:
        if session['username'] != username:
            flash('you are not that user', 'danger')
            return redirect('/')
        else:
            has_encrypted = False

            our_messages = db.session.query(Message) \
            .filter(
                    or_(
                        and_(Message.sent_to == username,
                            Message.read),
                        and_(Message.sender == username,
                            Message.in_reply_to is None),
                        )
                    )

            unread = db.session.query(Message).filter_by(sent_to=username, read=False) \
                    .order_by((Message.created).desc()).all()

            if request.args.get('offset') is not None:
                offset = int(request.args.get('offset'))

            our_messages = our_messages.order_by(
                                (Message.created).desc()
                                ).offset(offset).limit(26).all()

            if len(our_messages) >= 26:
                our_messages = our_messages[:-1]
                request.show_more_messages = True
            else:
                request.show_more_messages = False

            our_messages = [x for x in our_messages if x.sender is not None]

            unread = [x for x in unread if x.sender is not None]

            new_messages = False
            for r in unread:
                r.read = True
                r.was_unread = True
                new_messages = True

            # list preservs order
            our_messages = unread + our_messages

            for message in our_messages:
                message.sender_id = int(normalize_username(message.sender, dbuser=True).id)
                if message.sender == session['username']:
                    message.show_name = session['username']
                    message.is_sent = True
                    if message.encrypted:
                        message.new_text = '<p style="color: green;">ENCRYPTED</p>'
                else:
                    message.show_name = message.sender

            our_messages = [m for m in our_messages if m.sender_id not in session['blocked']['other_user']]

            for message in our_messages:
                if message.encrypted == False:
                    message.new_text = pseudo_markup(message.text)
                else:
                    message.sender_pgp = get_pgp_from_username(message.sender)
                    message.new_text = pseudo_markup(message.text, escape_only=True)

                message.created_ago = time_ago(message.created)

                if message.in_reply_to != None:
                    message.ppath = message.in_reply_to.replace(config.URL, '')

                if message.anonymous is False and message.sender is not None:
                    karma = get_user_karma(message.sender)
                    karma = int(karma['post'] + karma['comment'])
                    message.user_stats = karma
                    # if we wanted the # displayed to be # of messages sent
                    #message.user_stats = get_message_count(message.sender)

                if message.encrypted is True:
                    has_encrypted = True

                if message.in_reply_to is None:
                    message.message_type = 'message'
                else:
                    message.message_type = 'comment'

            session['unread_messages'] = None

            db.session.commit()

            if 'pgp_enabled' in session:
                self_pgp = get_pgp_from_username(session['username'])
            else:
                self_pgp = False

            return render_template('messages.html', messages=our_messages, has_encrypted=has_encrypted, self_pgp=self_pgp,
                new_messages=new_messages)

@app.route('/u/<username>/messages/reply/<mid>', methods=['GET'])
def reply_message(username=None, mid=None):
    if 'username' not in session or username is None:
        flash('not logged in', 'danger')
        return redirect(url_for('login'))

    if session['username'] != username:
        flash('you are not that user', 'danger')
        return redirect('/')

    message = db.session.query(Message).filter_by(sent_to=username, id=mid).first()
    if message is None:
        flash('invalid message id', 'danger')
        return redirect('/')

    message.new_text = pseudo_markup(message.text)
    if hasattr(message, 'in_reply_to'):
        if message.in_reply_to is not None:
            message.ppath = message.in_reply_to.replace(config.URL, '')

    message.created_ago = time_ago(message.created)

    message.new_title = message.title
    if len(message.title) >= 4:
        if message.title[0:4] != 'RE: ':
            message.new_title = 'RE: ' + message.title
    else:
        message.new_title = 'RE: ' + message.title

    message.user_stats = get_message_count(message.sender)

    return render_template('message-reply.html', message=message, sendto=False,
                            self_pgp=get_pgp_from_username(session['username']),
                             other_pgp=get_pgp_from_username(message.sender), 
                             other_user=get_user_from_username(username))


def sendmsg(title=None, text=None, sender=None, sent_to=None, encrypted=False, encrypted_key_id=None, in_reply_to=None):
    new_message = Message(title=title, text=text, sender=sender, in_reply_to=in_reply_to, sent_to=sent_to, encrypted=encrypted,
        encrypted_key_id=encrypted_key_id)
    db.session.add(new_message)
    db.session.commit()

@limiter.limit(config.MESSAGE_RATE_LIMIT)
@app.route('/message/', methods=['GET', 'POST'])
@app.route('/message/<username>', methods=['GET', 'POST'])
def msg(username=None):
    if 'username' not in session:
        flash('not logged in', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        text = request.form.get('message_text')
        title = request.form.get('message_title')
        sent_to = request.form.get('sent_to')
        encrypted = request.form.get('msgencrypted')
        encrypted_key_id = request.form.get('key_id')

        if encrypted == 'true':
            encrypted = True
            encrypted_key_id = encrypted_key_id
        else:
            encrypted = False
            encrypted_key_id = None

        if encrypted_key_id == '':
            encrypted_key_id = None

        if sent_to == None:
            sent_to = username

        if len(text) > 20000 or len(title) > 200:
            flash('text/title too long')
            return redirect('/message/')

        if str(sent_to) == 'None':
            flash('this user is not valid', 'danger')
            return redirect('/message/')

        sender = session['username']

        sendmsg(title=title, text=text, sender=session['username'], sent_to=sent_to, encrypted=encrypted,
            encrypted_key_id=encrypted_key_id)

        flash('sent message', category='success')
        return redirect(url_for('msg'))

    if request.method == 'GET':
        if username != None:
            if len(str(username)) < 1:
                flash('invalid username')
                return redirect('/')
        if request.referrer:
            ru = re.findall('\/i\/([a-zA-z0-9-_]*)', request.referrer)
            if ru != None:
                if len(ru) == 1:
                    if len(ru[0]) > 0:
                        username = ru[0]
        return render_template('message-reply.html', sendto=username, message=None, other_pgp=get_pgp_from_username(username),
                                other_user=get_user_from_username(username), self_pgp=get_pgp_from_username(session['username']))

@app.route('/i/<sub>/mods/', methods=['GET'])
def view_mod_log(sub=None, limit=10):
    sub = normalize_sub(sub)
    modactions = db.session.query(Mod_action).filter_by(sub=sub)
    
    if request.url[-4:] != '?all':
        modactions = modactions.limit(limit)
    modactions = modactions.all()

    return render_template('mod/mod-log.html', modactions=modactions)

@app.route('/i/<sub>/actions/', methods=['GET'])
def subactions(sub=None):
    sub = normalize_sub(sub)
    modactions = db.session.query(Mod_action).filter_by(sub=sub).all()
    if type(modactions) != None:
        modactions = [m for m in modactions]
    return render_template('mod/mod-log.html', modactions=modactions)


@app.route('/i/<sub>/mods/banned/', methods=['GET'])
def bannedusers(sub=None):
    sub = normalize_sub(sub)
    banned = db.session.query(Ban).filter_by(sub=sub).all()

    return render_template('mod/mod-banned.html', banned=banned)

@app.route('/i/<sub>/mods/add/', methods=['GET'])
def addmod(sub=None):
    sub = normalize_sub(sub)
    if hasattr(request, 'is_mod'):
        if request.is_mod:
            return render_template('mod/mod-add.html')
    return abort(403)

@app.route('/i/<sub>/mods/remove/', methods=['GET'])
def removemod(sub=None):
    sub = normalize_sub(sub)
    if hasattr(request, 'is_mod'):
        if request.is_mod:
            return render_template('mod/mod-banned.html')
    return abort(403)

@app.route('/i/<sub>/info/', methods=['GET'])
def description(sub=None):
    """
    This is the first function I have rewrote in the mods section.
    A lot of this code is terrible, and is my next priority. After this weekend.
    """
    sub = normalize_sub(sub)
    sub = db.session.query(Sub).filter_by(name=sub).first()

    # if we enable markup for sub descriptions
    #sub.markup_rules = pseudo_markup(sub.rules, all_newlines=False, escape_only=True)
    #sub.edit_rules = pseudo_markup(sub.rules, escape_only=True, replace_newlines=False, all_newlines=False)

    sub.markup_rules = sub.rules
    sub.edit_rules = sub.rules

    return render_template('mod/mod-info.html', sub=sub)

@app.route('/i/<sub>/settings/', methods=['GET'])
def settings(sub=None):
    if request.is_mod:
        return render_template('mod/mod-settings.html', sub=sub)
    return abort(403)

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_blocked_subs(username=None):
    subs = db.session.query(Sub_block).filter_by(username=session['username']).all()
    if subs != None:
        return [s.sub for s in subs]
    else:
        return []

@app.route('/i/<sub>/block', methods=['POST'])
def blocksub(sub=None):
    if 'username' not in session:
        flash('not logged in', 'error')
        return redirect(url_for('login'))
    if sub == None:
        return abort(500)

    blocks = db.session.query(Sub_block).filter_by(username=session['username']).all()
    if blocks != None:
        bsubs = [b.sub for b in blocks]
    else:
        bsubs = []

    #cache.clear()

    if blocks == None or sub not in bsubs:
        session['blocked_subs'].append(sub)
        new_block = Sub_block(username=session['username'], sub=sub)
        db.session.add(new_block)
        db.session.commit()
        bsubs.append(sub)
        flash('unsubscribed from %s' % sub, 'success')
    else:
        dblock = db.session.query(Sub_block).filter_by(username=session['username'], sub=sub).first()
        db.session.delete(dblock)
        db.session.commit()
        bsubs = [b for b in bsubs if b != sub]
        flash('subscribed to %s' % sub, 'success')

    session['blocked_subs'] = bsubs

    return redirect('/i/%s/' % sub)


@app.route('/explore/', methods=['GET'])
def explore():
    offset = request.args.get('offset')
    #limit = request.args.get('limit')

    subs = get_explore_subs(limit=101, offset=offset)

    if len(subs) >= 101:
        request.show_more_subs = True
        subs = subs[:-1]
    else:
        request.show_more_subs = False

    for s in subs:
        # if we enable markup in sub descriptions
        #s.new_rules = pseudo_markup(s.rules, escape_only=True, all_newlines=False)
        s.new_rules = s.rules

    return render_template('explore.html', subs=subs)

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    key = request.form.get('key')
    if key == config.API_OPER_KEY:
        cache.clear()
        return json.dumps({'status':'success'})
    return json.dumps({'status':'error'})

@app.route('/about/', methods=['GET'])
@app.route('/readme/', methods=['GET'])
@app.route('/news/2019/10/21/ieddit-beta-release/', methods=['GET'])
def about():
    from markdown import markdown
    with open('../README.md') as r:
        return render_template('about.html', about=markdown(r.read()))

@app.route('/changelog/', methods=['GET'])
def changelog():
    commits = requests.get('https://api.github.com/repos/civicsoft/ieddit/commits').json()
    return render_template('changelog.html', commits=commits, time_ago=time_ago, strptime=datetime.strptime)

@app.route('/comments/', methods=['GET'])
@app.route('/i/<sub>/comments/', methods=['GET'])
def subcomments(sub=None, offset=0, limit=15, s=None, d=None, nsfw=False, api=False, comments_only=False):
    # code is copy pasted from user page... the post stuff can probably be gotten rid of.
    # the username stuff can be gotten rid of too
    mods = {}

    offset = request.args.get('offset')
    if offset == None:
        offset = 0

    offset = int(offset)

    s = request.args.get('s')
    if s is None:
        s = 'new'

    d = request.args.get('d')

    muted_subs = False

    if sub == 'all':
        nsfw = True
        posts = subi('all', posts_only=True, nsfw=True)
        muted_subs = get_muted_subs()
        posts = [p for p in posts if p.sub not in muted_subs]
    elif sub != None:
        subobj = db.session.query(Sub).filter_by(name=sub).first()
        if subobj.muted or subobj.nsfw:
            nsfw = True
        posts = subi(sub, posts_only=True)
    else:
        posts = subi('all', posts_only=True, nsfw=False)
        muted_subs = get_muted_subs()
        posts = [p for p in posts if p.sub not in muted_subs]

    posts = posts[offset:offset+limit]

    for p in posts:
        p.mods = get_sub_mods(p.sub)

    comments_with_posts = []

    if d == 'hour':
        ago = datetime.now() - timedelta(hours=1)
    elif d == 'day':
        ago = datetime.now() - timedelta(hours=24)
    elif d == 'week':
        ago = datetime.now() - timedelta(days=7)
    elif d == 'month':
        ago = datetime.now() - timedelta(days=31)
    elif d == 'year':
        ago = datetime.now() - timedelta(days=365)
    else:
        ago = datetime.now() - timedelta(days=9999)

    if sub is None:
        nsfw = False
        sub = 'all'

    if sub == 'all':
        if nsfw:
            comments = db.session.query(Comment).filter(Comment.created > ago)
        else:
            sfw_subs = [n.name for n in db.session.query(Sub).filter_by(nsfw=False).all()]
            comments = db.session.query(Comment).filter(Comment.created > ago)
            comments = comments.filter(Comment.sub_name.in_(sfw_subs))
    else:
        comments = db.session.query(Comment).filter_by(sub_name=normalize_sub(sub)).filter(Comment.created > ago)

    comments = comments.filter_by(deleted=False).filter(Comment.created > ago)

    if comments.count() >= limit:
        request.is_more_content = True

    if s == 'top':
        comments = comments.order_by((Comment.ups - Comment.downs).desc())
        comments = comments.offset(offset).limit(limit).all()
    elif s == 'new':
        comments = comments.order_by((Comment.created).desc())
        comments = comments.offset(offset).limit(limit).all()
    else:
        comments = comments.offset(offset).limit(limit).all()

    comments = [c for c in comments if c.id not in session['blocked']['comment_id']]

    if muted_subs:
        comments = [c for c in comments if c.sub_name not in muted_subs]

    comments = hide_blocked(comments)

    nsfw_subs = []
    sfw_subs = []

    if nsfw == False:
        for c in comments:
            if c.sub_name not in nsfw_subs and c.sub_name not in sfw_subs:
                comsub = db.session.query(Sub).filter_by(name=c.sub_name).first()
                if comsub.nsfw == True:
                    nsfw_subs.append(comsub.name)
                else:
                    sfw_subs.append(comsub.name)

    if nsfw == False:
        comments = [c for c in comments if c.sub_name not in nsfw_subs]

    for c in comments:
        c.new_text = pseudo_markup(c.text)
        c.mods = get_sub_mods(c.sub_name)
        cpost = db.session.query(Post).filter_by(id=c.post_id).first()
        comments_with_posts.append((c, cpost))
        c.hot = hot(c.ups, c.downs, c.created)
        c.created_ago = time_ago(c.created)

        if 'user_id' in session:
            c.has_voted = db.session.query(Vote).filter_by(comment_id=c.id, user_id=session['user_id']).first()
            if c.has_voted != None:
                c.has_voted = c.has_voted.vote

    if s == 'hot':
            comments.sort(key=lambda x: x.hot, reverse=True)

    if api:
        comments = [sqla_to_dict(comment) for comment in comments]

        return pretty_json(comments)

    return render_template('recent-comments.html', posts=posts, url=config.URL, comments_with_posts=comments_with_posts, no_posts=True)

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_posts_and_comments(subi=None, day=False, load=None):
    """
    how many users have voted/commented/posted to a given sub
    """
    filter_today = datetime.now() - timedelta(days=1)
    subi = normalize_sub(subi)

    if subi == None or subi == 'all':
        posts = db.session.query(Post)
        comments = db.session.query(Comment)
    else:
        posts = db.session.query(Post).filter(Post.sub == subi)
        comments = db.session.query(Comment).filter(Comment.sub_name == subi)

    if day:
        posts = posts.filter(Post.created >= filter_today)
        comments = comments.filter(Comment.created >= filter_today)

    if load != None:
        posts = posts.options(load_only('author'))
        comments = comments.options(load_only('author'))


    hidden_subs = [s.name for s in db.session.query(Sub).filter_by(muted=True).all()]

    posts = [p for p in posts.all() if p.sub not in hidden_subs]
    comments = [c for c in comments.all() if c.sub_name not in hidden_subs]

    return posts, comments

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_top_stats(subi=None):
    t = time.time()
    votes = []
    users = []
    filter_today = datetime.now() - timedelta(days=1)

    posts, comments = get_posts_and_comments(subi=subi, day=True)

    for p in posts:
        if p.author not in users:
            users.append(p.author)
        [votes.append(v) for v in db.session.query(Vote).filter_by(post_id=p.id).all()]

    for c in comments:
        if c.author not in users:
            users.append(c.author)
        [votes.append(v) for v in db.session.query(Vote).filter_by(comment_id=c.id).all()]

    for v in votes:
        user = get_user_from_id(v.user_id)
        if user.username not in users:
            users.append(user.username)

    return {'active_users':len(users), 'posts_today':len(posts)}



@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_stats(subi=None):
    if subi == None:
        votes = db.session.query(Vote).all()
        posts = db.session.query(Post).all()
        comments = db.session.query(Comment).all()
        users = db.session.query(Iuser).all()
        bans = db.session.query(Ban).count()
        messages = db.session.query(Message).count()
        mod_actions = db.session.query(Mod_action).count()
        subs = db.session.query(Sub).count()
        subscripts = 0
    else:
        posts = db.session.query(Post).filter_by(sub=subi).all()
        comments = db.session.query(Comment).filter_by(sub_name=subi).all()
        bans = db.session.query(Ban).filter_by(sub=subi).count()
        mod_actions = db.session.query(Mod_action).filter_by(sub=subi).count()
        users = []
        votes = []
        for v in posts:
            [votes.append(vv) for vv in db.session.query(Vote).filter_by(post_id=v.id).all()]
            [users.append(vv) for vv in db.session.query(Iuser).filter_by(username=v.author).all()]
        for v in comments:
            [votes.append(vv) for vv in db.session.query(Vote).filter_by(comment_id=v.id).all()]
            [users.append(vv) for vv in db.session.query(Iuser).filter_by(username=v.author).all()]
        users_blocked = [n.username for n in db.session.query(Sub_block).filter_by(sub=subi).all()]
        subscripts = len([u for u in db.session.query(Iuser) if u.username not in users_blocked])
        messages = 0
        subs = 0

    daycoms = [c for c in comments if ((datetime.now() - c.created).total_seconds()) < 86400]


    dayusers = []

    for uu in daycoms:
        if uu.author not in dayusers:
            dayusers.append(uu.author)

    dayposts = [p for p in posts if ((datetime.now() - p.created).total_seconds()) < 86400]

    for uuu in dayposts:
        if uuu.author not in dayusers:
            dayusers.append(uuu.author)

    dayvotes = []

    for vvv in votes:
        if hasattr(vvv, 'created'):
            if((datetime.utcnow() - vvv.created).total_seconds()) < 86400:
                dayvotes.append(vvv)

    for vz in dayvotes:
        new_user = db.session.query(Iuser).filter(Iuser.id == vz.user_id).first()
        if hasattr(new_user, 'username'):
            if new_user.username not in dayusers:
                dayusers.append(new_user.username)

    users = len(users)
    daycoms = len(daycoms)
    dayposts = len(dayposts)
    dayvotes = len(dayvotes)
    dayusers = len(dayusers)

    # requires user be on linux, and have log file in this location, so this is
    # only set to try to be calculated on the ieddit prod/dev server. it makes
    # assumptions that cannot be made for any user on a different setup
    if config.URL == 'https://ieddit.com' or config.URL == 'http://dev.ieddit.com' and subi == None:
        try:
            fline = str(os.popen('head -n 1 /var/log/nginx/access.log').read()).split(' ')[3][1:]
            lline = str(os.popen('tail -n 1 /var/log/nginx/access.log').read()).split(' ')[3][1:]

            fline = datetime.strptime(fline, '%d/%b/%Y:%H:%M:%S')
            lline = datetime.strptime(lline, '%d/%b/%Y:%H:%M:%S')

            timediff = lline - fline

            timediff = ' total requests in past %s hours' % str(timediff.total_seconds() / 60 / 24)

            lc = str(os.popen('wc -l /var/log/nginx/access.log').read()).split(' ')[0]

            timediff = lc + timediff

            uptime = (time.time() - int(cache_bust[1:])) / 60 / 60
        except Exception as e:
            print(e)
            timediff, uptime = False, False
    else:
        timediff, uptime = False, False


    return (len(posts), len(comments), users, bans, messages, mod_actions, subs, len(votes), daycoms, dayposts, dayvotes, dayusers,
        timediff, uptime, subscripts)

@app.route('/i/<subi>/stats/', methods=['GET'])
@app.route('/stats/', methods=['GET'])
def stats(subi=None):
    (posts, comments, users, bans, messages, mod_actions, subs, votes, daycoms, dayposts, dayvotes,
        dayusers, timediff, uptime, subscripts) = get_stats(subi=subi)

    if 'admin' in session:
        debug = str(vars(request))
    else:
        debug = False

    return render_template('stats.html', posts=posts, dayposts=dayposts, comments=comments, daycoms=daycoms,
        users=users, bans=bans, messages=messages, mod_actions=mod_actions, subs=subs, votes=votes, dayvotes=dayvotes,
        dayusers=dayusers, timediff=timediff, uptime=uptime, debug=debug, subi=subi, subscripts=subscripts)

from blueprints import mod
app.register_blueprint(mod.bp)

from blueprints import user
app.register_blueprint(user.ubp)

from blueprints import admin
app.register_blueprint(admin.abp)

from blueprints import api
app.register_blueprint(api.bp)
