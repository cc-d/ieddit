from ieddit import *
import json

ubp = Blueprint('user', 'user', url_prefix='/user')

@ubp.route('/delete/post',  methods=['POST'])
def user_delete_post():
    if 'username' not in session:
        flash('not logged in', 'error')
        return redirect(url_for('login'))
    pid = request.form.get('post_id')
    post = db.session.query(Post).filter_by(id=pid).first()
    sub_url = config.URL + '/i/' + post.sub

    if post.author == session['username']:
        post.deleted = True
        db.session.commit()

        flash('post deleted', category='success')
        return redirect(sub_url)
    else:
        return '403'

@ubp.route('/delete/comment',  methods=['POST'])
def user_delete_comment():
    if 'username' not in session:
        flash('not logged in', 'error')
        return redirect(url_for('login'))
    cid = request.form.get('comment_id')
    comment = db.session.query(Comment).filter_by(id=cid).first()
    post = db.session.query(Post).filter_by(id=comment.post_id).first()

    if comment.author == session['username']:
        comment.deleted = True
        comment.removed_by = 'removed by author'
        db.session.commit()

        flash('post deleted', category='success')
        return redirect(post.get_permalink())
    else:
        return '403'

@ubp.route('/edit/<itype>/<iid>/', methods=['GET'])
def user_get_edit(itype, iid):
    if 'username' not in session:
        flash('not logged in', 'error')
        return redirect(url_for('login'))
    if itype == 'post':
        obj = db.session.query(Post).filter_by(id=iid).first()
        if hasattr(obj, 'self_text'):
            etext = obj.self_text
        else:
            return '403'
    elif itype == 'comment':
        obj = db.session.query(Comment).filter_by(id=iid).first()
        etext = obj.text
    else:
        return 'bad itype'

    if 'last_edit' in session:
        lastedit = session['last_edit']
    else:
        lastedit = None
    session['last_edit'] = None
    
    return render_template('edit.html', itype=itype, iid=iid, etext=etext, lastedit=lastedit)

@ubp.route('/edit',  methods=['POST'])
def user_edit_post():
    if 'username' not in session:
        flash('not logged in', 'error')
        return redirect(url_for('login'))
    itype = request.form.get('itype')
    iid = request.form.get('iid')
    etext = request.form.get('etext')

    session['last_edit'] = etext

    if len(etext) < 1 or len(etext) > 20000:
        return 'invalid edit length'


    if itype == 'post':
        obj = db.session.query(Post).filter_by(id=iid).first()
        if obj.self_text == None:
            return 'cannot edit this type of post'
    elif itype == 'comment':
        obj = db.session.query(Comment).filter_by(id=iid).first()
    else:
        return 'bad itype'

    if obj.author != session['username']:
        return '403'

    if hasattr(obj, 'self_text'):
        obj.self_text = etext
        obj.edited = True
        db.session.commit()
        
        flash('post edited', category='success')
        session['last_edit'] = None
        return redirect(obj.get_permalink())
    elif hasattr(obj, 'text'):
        obj.edited = True
        obj.text = etext
        db.session.commit()

        flash('comment edited', category='success')
        session['last_edit'] = None
        return redirect(obj.get_permalink())
    else:
        return '403'

@ubp.route('/nsfw',  methods=['POST'])
def user_marknsfw(pid=None):
    if 'username' not in session:
        flash('not logged in', 'danger')
        return redirect(url_for('login'))

    post_id = request.form.get('post_id')
    post = db.session.query(Post).filter_by(id=post_id).first()

    if session['username'] != post.author:
        return '403'

    post.nsfw = True
    flash('marked as nsfw')
    db.session.commit()
    
    return redirect(post.get_permalink())


@ubp.route('/darkmode', methods=['POST'])
def user_darkmode(username=None):
    if 'username' not in session:
        flash('not logged in', 'danger')
        return redirect(url_for('login'))

    if username is None:
        user = db.session.query(Iuser).filter_by(username=session['username']).first()

    action = request.form.get('action')

    if action == 'disable':    
        user.darkmode = False
        mode = 'light'
        session['darkmode'] = False
    elif action == 'enable':
        user.darkmode = True
        mode = 'dark'
        session['darkmode'] = True
    else:
        return 'bad action'

    flash('switched to %s mode' % mode, 'success')
    db.session.add(user)
    db.session.commit()
    
    return redirect('/u/' + user.username)

@ubp.route('/anonymous', methods=['POST'])
def user_uanonymous(username=None):
    if 'username' not in session:
        flash('not logged in', 'danger')
        return redirect(url_for('login'))

    if username is None:
        user = db.session.query(Iuser).filter_by(username=session['username']).first()

    action = request.form.get('action')

    if action == 'disable':    
        user.anonymous = False
        session['anonymous'] = False
    elif action == 'enable':
        user.anonymous = True
        session['anonymous'] = True
    else:
        return 'bad action'

    flash('toggled anonymous', 'success')
    db.session.add(user)
    db.session.commit()
    
    return redirect('/u/' + user.username)

@ubp.route('/reset_password/', methods=['GET'])
def reset_page():
    return render_template('reset-password.html')

@limiter.limit(config.RECOVERY_EMAIL_RATE_LIMIT)
@ubp.route('/password_reset', methods=['POST', 'GET'])
def password_reset(email=None):
    if request.method == 'POST':

        email = request.form.get('email')
        if email == None:
            flash('no email', 'danger')
            return redirect('/user/reset_password/')
        user = db.session.query(Iuser).filter_by(email=email).first()
        if user == None:
            flash('no user with email', 'danger')
            return redirect('/user/reset_password/')
        key = rstring(30)
        new_reset = Password_reset(username=user.username, rankey=key, expires=datetime.utcnow() + timedelta(hours=1))

        link = config.URL + '/user/password_reset?reset=' + key
        etext = 'Please visit this link to reset your password: <a href="%s/user/password_reset?reset=%s">LINK</a>' % (config.URL, key)

        e = send_email(etext=etext, subject='Password Reset', to=email)

        if e == True:
            db.session.add(new_reset)
            db.session.commit()
            
            flash('password recovery email sent', 'success')
            return redirect('/user/reset_password/')

    if request.method == 'GET':
        reset = request.args.get('reset')
        r = db.session.query(Password_reset).filter_by(rankey=reset).first()
        if r == None:
            return 'invalid link'
        return render_template('new-reset-password.html', reset=reset, username=r.username)

@ubp.route('/new_reset_password', methods=['POST'])
def new_reset_password():
    password = request.form.get('password')
    reset = request.form.get('reset')
    username = request.form.get('username')

    if len(password) < 1:
        return 'no password'

    r = db.session.query(Password_reset).filter_by(rankey=reset).first()
    if r == None or r.valid == False:
        return 'invalid key or key expired'

    r.valid = False
    user = db.session.query(Iuser).filter_by(username=username).first()

    user.password = generate_password_hash(password)
    db.session.add(user)
    db.session.add(r)
    db.session.commit()

    flash('successfully reset password for %s' % username, 'success')
    return redirect('/login/')

@ubp.route('/preferences/', methods=['GET'])
@require_login
def user_preferences():
    if 'username' not in session:
        flash('not logged in', 'danger')
        return redirect('/login/')

    user = db.session.query(Iuser).filter_by(username=session['username']).first()

    return render_template('preferences.html', user=user)

@ubp.route('/update_preferences', methods=['POST'])
def user_update_preferences():
    if 'username' not in session:
        flash('not logged in', 'danger')
        return redirect('/login/')    

    user = db.session.query(Iuser).filter_by(username=session['username']).first()

    lang = request.form.get('language-select')
    if lang is not None and len(lang) > 0:
        lang = lang.lower()
        if lang in config.LANGUAGES:
            user.language = lang

    session['language'] = user.language

    hsl = request.form.get('hide_sub_language')
    if user.hide_sub_language is True:
        if hsl is None:
            user.hide_sub_language = False
    elif user.hide_sub_language is False:
        if hsl is not None:
            user.hide_sub_language = True
    session['hide_sub_language'] = user.hide_sub_language

    # preferences a user can update without a password here
    hss = request.form.get('hide_sub_style')
    if user.hide_sub_style is True:
        if hss is None:
            user.hide_sub_style = False
    elif user.hide_sub_style is False:
        if hss is not None:
            user.hide_sub_style = True

    session['hide_sub_style'] = user.hide_sub_style

    always_override = request.form.get('always_override')
    if user.always_override is True:
        if always_override is None:
            user.always_override = False
    elif user.always_override is False:
        if always_override is not None:
            user.always_override = True
          
    session['always_override'] = user.always_override

    always_anonymous = request.form.get('always_anonymous')
    if user.anonymous is True:
        if always_anonymous is None:
            user.anonymous = False
    elif user.anonymous is False:
        if always_anonymous is not None:
            user.anonymous = True
          
    session['anonymous'] = user.anonymous

    checkbox_only = request.form.get('checkbox_only')

    if checkbox_only != None:
        db.session.add(user)
        db.session.commit()

        flash('successfully updated preferences', 'success')
        return redirect('/user/preferences/')

    new_email = request.form.get('new_email')
    new_password = request.form.get('new_password')
    con_new_password = request.form.get('con_new_password')

    cur_password = request.form.get('cur_password')

    update_email, update_password = False, False

    if cur_password == None or cur_password == '':
        flash('enter current password', 'danger')
        return redirect('/user/preferences/')

    if new_email != None and new_email != '':
        if len(new_email.split('@')) != 2:
            flash('invalid email format', 'danger')
            return redirect('/user/preferences/')
        else:
            if len((new_email.split('@')[1]).split('.')) < 2:
                flash('invalid email format', 'danger')
                return redirect('/user/preferences/')
            else:
                if len(new_email) < 75:
                    update_email = True
                else:
                    flash('email too long', 'danger')
                    return redirect('/user/preferences/')

    if new_password != None and new_password != '':
        if new_password == con_new_password:
            if len(new_password) > 0 and len(new_password) < 200:
                update_password = True
            else:
                flash('invalid password length', 'danger')
                return redirect('/user/preferences/')
        else:
            flash('passwords do not match', 'danger')
            return redirect('/user/preferences/')

    hashed_pw = user.password
    if check_password_hash(hashed_pw, cur_password):
        if update_email:
            user.email = new_email
        if update_password:
            user.password = generate_password_hash(new_password)

        db.session.add(user)
        db.session.commit()

        

        flash('successfully updated settings', 'success')
        return redirect('/user/preferences/')
    else:
        flash('incorrect current password', 'danger')
        return redirect('/user/preferences/')


@ubp.route('/pgp/', methods=['GET'])
def user_pgp():
    if 'username' not in session:
        flash('not logged in', 'danger')
        return redirect('/login/')
    user = db.session.query(Iuser).filter_by(username=session['username']).first()
    pgp = db.session.query(Pgp).filter_by(username=session['username']).first()

    return render_template('pgp.html', user=user, pgp=pgp)

@ubp.route('/addpgp', methods=['POST'])
def user_add_pgp():
    if 'username' not in session:
        flash('not logged in', 'danger')
        return redirect('/login/')
    user = db.session.query(Iuser).filter_by(username=session['username']).first()

    if user == None:
        return 'invalid user'

    pgp = db.session.query(Pgp).filter_by(username=session['username']).first()

    if pgp != None:
        db.session.delete(pgp)
        db.session.commit()

    privkey = request.form.get('privkey')
    pubkey = request.form.get('pubkey')

    if privkey == None or privkey == '' or pubkey == None or pubkey == '':
        flash('pubkey or privkey empty', 'danger')
        return redirect('/user/pgp/')

    new_pgp = Pgp(username=user.username, privkey=privkey, pubkey=pubkey)
    db.session.add(new_pgp)
    db.session.commit()

    session['pgp_enabled'] = True

    

    flash('updated pgp key', 'success')
    return redirect('/u/' + user.username)

@ubp.route('/hide', methods=['POST'])
def hide_obj():
    post_id = None
    comment_id = None
    other_user = None

    if 'username' not in session:
        return 'you must be logged in to hide content'

    d = json.loads(request.form.get('d'))
    for k in d.keys():
        if k == 'post_id':
            post_id = d[k]
        elif k == 'comment_id':
            comment_id = d[k]
        elif k == 'other_user':
            other_user = d[k]

    if 'username' in session:
        new_hidden = Hidden(post_id=post_id, comment_id=comment_id, username=session['username'],
                            other_user=other_user, anonymous=False)
        db.session.add(new_hidden)
        db.session.commit()

    if 'blocked' not in session:
        session['blocked'] = {'comment_id':[], 'post_id':[], 'other_user':[], 'anon_user':[]}

    d = {'post_id':post_id, 'comment_id':comment_id, 'other_user':other_user, 'anon_user':None}

    for i in d.keys():
        if d[i] != None:
            d[i] = int(d[i])
            if d[i] not in session['blocked'][i]:
                session['blocked'][i].append(d[i])

    session['blocked'] = get_blocked(session['username'])
    return 'ok'

@ubp.route('/block_user', methods=['POST'])
@require_login
def block_user_from_content():
    post_id = request.form.get('post_id')
    comment_id = request.form.get('comment_id')

    if post_id is not None:
        p = db.session.query(Post).filter_by(id=post_id).first()
        if p.anonymous:
            block_id = db.session.query(Iuser.anon_id). \
                                    filter_by(id=p.author_id).first()[0]
        else:
            block_id = db.session.query(Iuser.id). \
                                    filter_by(id=p.author_id).first()[0]

    elif comment_id is not None:
        p = db.session.query(Comment).filter_by(id=comment_id).first()
        if p.anonymous:
            block_id = db.session.query(Iuser.anon_id). \
                                    filter_by(id=p.author_id).first()[0]
        else:
            block_id = db.session.query(Iuser.id). \
                                    filter_by(id=p.author_id).first()[0]

    if 'blocked' not in session:
        session['blocked'] = {'comment_id':[], 'post_id':[], 'other_user':[], 'anon_user':[]}

    if 'username' in session:
        new_hidden = Hidden(post_id=None, comment_id=None, username=session['username'],
                            other_user=block_id, anonymous=p.anonymous)
        db.session.add(new_hidden)
        db.session.commit()

    if p.anonymous:
        session['blocked']['anon_user'].append(block_id)
    else:
        session['blocked']['other_user'].append(block_id)

    flash('blocked %s' % (block_id), 'success')
    return app.make_response(('ok', 200))

@ubp.route('/show', methods=['POST'])
@require_login
def show_obj():
    post_id = None
    comment_id = None
    other_user = None
    anonymous = False

    d = json.loads(request.form.get('d'))

    for k in d.keys():
        if k == 'post_id':
            post_id = d[k]
            itype = 'post_id'
            iid = d[k]
        elif k == 'comment_id':
            comment_id = d[k]
            itype = 'comment_id'
            iid = d[k]
        elif k == 'other_user':
            other_user = d[k]
            itype = 'other_user'
            iid = d[k]
        elif k == 'anon_user':
            anonymous = True
            other_user = d[k]
            itype = 'anon_user'
            iid = d[k]

    iid = iid.strip()

    if 'username' in session:
        hid = db.session.query(Hidden).filter_by(post_id=post_id, comment_id=comment_id, other_user=other_user, anonymous=anonymous).delete()
        db.session.commit()

        if not anonymous:
            session['blocked'][itype].pop(session['blocked'][itype].index(int(iid)))
        else:
            session['blocked'][itype].pop(session['blocked'][itype].index(iid))
        session['blocked'] = get_blocked(session['username'])
    else:
        session['blocked'][itype].pop(session['blocked'][itype].index(int(iid)))

    return 'ok'

@cache.memoize(config.DEFAULT_CACHE_TIME)
def get_total_blocked():
    uids, pids, cids = [], [], []

    for u in session['blocked']['other_user']:
        u2 = db.session.query(Iuser).filter_by(id=u).first()
        if u2 is None:
            continue

        u2.created_ago = time_ago(u2.created)
        u2.type = 'user'
        u2.key = 'other_user'
        u2.permalink = config.URL + '/u/' + u2.username
        u2.anonymous = False
        uids.append(u2)

    for u in session['blocked']['anon_user']:
        u2 = db.session.query(Iuser).filter_by(anon_id=u).first()
        if u2 is None:
            continue

        u2.created_ago = time_ago(u2.created)
        u2.type = 'user'
        u2.key = 'anon_user'
        u2.permalink = config.URL + '/u/' + 'Anonymous'
        u2.anonymous = True
        u2.anon_id = u2.anon_id.strip()
        uids.append(u2)

    for p in session['blocked']['post_id']:
        p2 = db.session.query(Post).filter_by(id=int(p)).first()
        if p2 is None:
            continue
        p2.created_ago = time_ago(p2.created)
        p2.type = 'post'
        p2.key = 'post_id'
        pids.append(p2)

    for c in session['blocked']['comment_id']:
        c2 = db.session.query(Comment).filter_by(id=int(c)).first()
        if c2 is None:
            continue
        c2.created_ago = time_ago(c2.created)
        c2.type = 'comment'
        c2.key = 'comment_id'
        cids.append(c2)

    blocked = uids + pids + cids
    blocked.sort(key=lambda x: x.created, reverse=True)

    return blocked

@ubp.route('/blocked/', methods=['GET'])
def show_blocked():
    return render_template('blocked.html', blocked=get_total_blocked())
