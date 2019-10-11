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
	sub_url = config.URL + '/r/' + post.sub

	if post.author == session['username']:
		post.deleted = True
		db.session.commit()
		cache.delete_memoized(get_subi)
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
		db.session.commit()
		cache.delete_memoized(get_subi)
		flash('post deleted', category='success')
		return redirect(post.permalink)
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

	if config.CAPTCHA_ENABLE:
		if request.form.get('captcha') == '':
			flash('no captcha', 'danger')
			return redirect('/user/edit/%s/%s/' % (itype, iid))
		if captcha.validate() == False:
			flash('invalid captcha', 'danger')
			return redirect('/user/edit/%s/%s/' % (itype, iid))
#		if 'rate_limit' in session and config.RATE_LIMIT == True:
#			rl = session['rate_limit'] - time.time()
#			if rl > 0:
#				flash('rate limited, try again in %s seconds' % str(rl))
#				return redirect('/user/edit/%s/%s/' % (itype, iid))

	if itype == 'post':
		obj = db.session.query(Post).filter_by(id=iid).first()
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
		cache.clear()
		flash('post edited', category='succes')
		session['last_edit'] = None
		return redirect(obj.permalink)
	elif hasattr(obj, 'text'):
		obj.edited = True
		obj.text = etext
		db.session.commit()
		cache.delete_memoized(c_get_comments)
		flash('comment edited', category='succes')
		session['last_edit'] = None
		return redirect(obj.permalink)
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
	cache.clear()
	return redirect(post.permalink)


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
	cache.clear()
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
	cache.clear()
	return redirect('/u/' + user.username)

@ubp.route('/reset_password/', methods=['GET'])
def reset_page():
	return render_template('reset_password.html')

@limiter.limit(['5 per hour'])
@ubp.route('/password_reset', methods=['POST', 'GET'])
def password_reset(email=None):
	if request.method == 'POST':
		if config.CAPTCHA_ENABLE:
			if request.form.get('captcha') == '':
				flash('no captcha', 'danger')
				return redirect('/user/reset_password/')

			if captcha.validate() == False:
				flash('invalid captcha', 'danger')
				return redirect('/user/reset_password/')

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
		return render_template('new_reset_password.html', reset=reset, username=r.username)

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
	#generate_password_hash(password)

	r.valid = False
	user = db.session.query(Iuser).filter_by(username=username).first()

	user.password = generate_password_hash(password)
	db.session.add(user)
	db.session.add(r)
	db.session.commit()

	flash('successfully reset password for %s' % username, 'success')
	return redirect('/login/')

@ubp.route('/preferences/', methods=['GET'])
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

		hss = request.form.get('hide_sub_style')

		if user.hide_sub_style == True:
			if hss == None:
				user.hide_sub_style = False
		elif user.hide_sub_style == False:
			if hss != None:
				user.hide_sub_style = True
				
		session['hide_sub_style'] = user.hide_sub_style

		db.session.add(user)
		db.session.commit()
		flash('successfully updated settings', 'success')
		return redirect('/user/preferences/')
	else:
		flash('incorrect current password', 'danger')
		return redirect('/user/preferences/')









