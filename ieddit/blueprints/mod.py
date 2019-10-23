from ieddit import *
from jinja2 import escape
import json

bp = Blueprint('mod', 'mod', url_prefix='/mod')

def mod_action(username, action, url, sub):
	new_action = Mod_action(username=username, action=action, url=url, sub=sub)
	db.session.add(new_action)
	db.session.commit()

@bp.route('/delete/post',  methods=['POST'])
def mod_delete_post():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))
	pid = request.form.get('post_id')
	post = db.session.query(Post).filter_by(id=pid).first()
	sub_url = config.URL + '/i/' + post.sub
	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(post.sub)).exists()).scalar()
	if is_mod:
		#db.session.delete(post)
		msg = 'deleted'
		if post.deleted == True:
			post.deleted = False
			msg = 'undeleted'
		else:
			post.deleted = True
		mod_action(session['username'], msg, post.get_permalink(), post.sub)
		db.session.commit()

		flash('post %s' % msg, category='success')
		return redirect(sub_url)
	else:
		return '403'

@bp.route('/delete/comment', methods=['POST'])
def mod_delete_comment():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))
	cid = request.form.get('comment_id')
	comment = db.session.query(Comment).filter_by(id=cid).first()
	post = db.session.query(Post).filter_by(id=comment.post_id).first()

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(post.sub)).exists()).scalar()
	if is_mod:
		comment.deleted = True
		mod_action(session['username'], 'delete', comment.get_permalink(), comment.sub_name)
		db.session.commit()

		flash('comment deleted', category='success')
		return redirect(post.get_permalink())		
	else:
		return '403'

@bp.route('/sticky/post', methods=['POST'])
def mod_sticky_post():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	pid = request.form.get('post_id')
	post = db.session.query(Post).filter_by(id=pid).first()

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(post.sub)).exists()).scalar()
	if is_mod:
		old_sticky = db.session.query(Post).filter_by(sub=post.sub, stickied=True).all()
		for s in old_sticky:
			s.stickied = False
			db.session.commit()	
			mod_action(session['username'], 'unstickied', post.get_permalink(), post.sub)

		post.stickied = True
		db.session.commit()

		mod_action(session['username'], 'stickied', post.get_permalink(), post.sub)
		flash('stickied post', category='success')
		return redirect(config.URL + '/i/' + post.sub)
	else:
		return '403'


@bp.route('/unsticky/post', methods=['POST'])
def mod_unsticky_post():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	pid = request.form.get('post_id')
	post = db.session.query(Post).filter_by(id=pid).first()

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(post.sub)).exists()).scalar()
	if is_mod:
		mod_action(session['username'], 'unstickied', post.get_permalink(), post.sub)
		post.stickied = False
		db.session.commit()

		
		flash('unstickied post', category='success')
		return redirect(config.URL + '/i/' + post.sub)
	else:
		return '403'

@bp.route('/lock/post', methods=['POST'])
def mod_lock_post():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	pid = request.form.get('post_id')
	post = db.session.query(Post).filter_by(id=pid).first()

	if post.locked == False:
		action = 'lock'
	else:
		action = 'unlock'

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(post.sub)).exists()).scalar()
	if is_mod:
		if action == 'lock':
			mod_action(session['username'], 'locked', post.get_permalink(), post.sub)
			post.locked = True
			flash('locked post', category='success')
		elif action == 'unlock':
			mod_action(session['username'], 'unlocked', post.get_permalink(), post.sub)
			post.locked = False
			flash('unlocked post', category='success')

		db.session.commit()

		return redirect(post.get_permalink())
	else:
		return '403'


@bp.route('/ban', methods=['POST'])
def mod_ban_user():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	dropdown = request.form.get('post_id')
	if dropdown != None:
		if dropdown.find('|') != -1:
			params = dropdown.split('|')
			iid = params[1]
			itype = params[2]
		else:
			iid = request.form.get('iid')
			itype = request.form.get('itype')
	else:
			iid = request.form.get('iid')
			itype = request.form.get('itype')

	is_mod = True

	if is_mod:
		if itype == 'post':
			obj = db.session.query(Post).filter_by(id=iid).first()
		elif itype == 'comment':
			obj = db.session.query(Comment).filter_by(id=iid).first()
		
		if obj.anonymous:
			anon = True
		else:
			anon = False

		if hasattr(obj, 'sub_name'):
			is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(obj.sub_name)).exists()).scalar()
			if is_mod == False:
				if 'admin' in session:
					is_mod = True
			if is_mod != True:
				return '403'
			new_ban = Ban(sub=obj.sub_name, username=obj.author, anonymous=anon)
			sub = obj.sub_name
			db.session.add(new_ban)
		else:
			is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(obj.sub)).exists()).scalar()
			if is_mod == False:
				if 'admin' in session:
					is_mod = True
			if is_mod != True:
				return '403'
			new_ban = Ban(sub=obj.sub, username=obj.author, anonymous=anon)
			sub = obj.sub
			db.session.add(new_ban)

		mod_action(session['username'], 'ban', obj.get_permalink(), sub)

		db.session.commit()

		flash('banned ' + obj.author + ' from ' + sub, category='success')
		return redirect(config.URL + '/i/' + sub)
	else:
		return '403'

@bp.route('/unban', methods=['POST'])
def mod_unban_user():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	username = request.form.get('username')
	username = normalize_username(username)
	ban_id = request.form.get('ban_id')
	sub = request.form.get('sub')

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(sub)).exists()).scalar()
	if is_mod:
		uban = db.session.query(Ban).filter_by(id=ban_id, sub=sub)
		uban.delete()
		db.session.commit()
		
		mod_action(session['username'], 'unban', username, sub)
		flash('unbanned ' + username, 'success')
		return redirect('/i/' + sub + '/mods/banned/')

@bp.route('/add', methods=['POST'])
def mod_addmod():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	username = request.form.get('username')
	sub = request.form.get('sub')

	username = db.session.query(Iuser).filter(func.lower(Iuser.username) == func.lower(username)).first()
	username = username.username
	if db.session.query(Moderator).filter(func.lower(Moderator.username) == func.lower(username), Moderator.sub == sub).first() != None:
		flash('Mod already added', 'error')
		return redirect('/i/%s/mods/' % sub)

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(sub)).exists()).scalar()
	if is_mod:
		mods = db.session.query(Moderator).filter_by(sub=sub).all()
		rank = 0
		if mods != None:
			for x in mods:
				if x.rank > rank:
					rank = x.rank

		new_mod = Moderator(sub=sub, username=username, rank=rank)
		db.session.add(new_mod)
		db.session.commit()

		flash('new moderator ' + username, 'success')
		return redirect('/i/' + sub + '/mods/')
	else:
		return '403'

@bp.route('/remove', methods=['POST'])
def mod_removemod():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	username = normalize_username(request.form.get('username'))
	sub = request.form.get('sub')
	if not username:
		flash ('invalid username', 'error')
		return redirect('/i/' + sub + '/mods/')

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(sub)).exists()).scalar()
	if is_mod:
		sub = normalize_sub(sub)
		delmod = db.session.query(Moderator).filter_by(username=username, sub=sub).first()
		you = db.session.query(Moderator).filter_by(username=session['username'], sub=sub).first()

		if delmod.rank < you.rank:
			flash('cannot delete mod of higher rank')
			return redirect('/i/' + sub + '/mods/')

		db.session.query(Moderator).filter_by(username=delmod.username, sub=sub).delete()
		db.	session.commit()
		
		flash('deleted mod')
		return redirect('/i/' + sub + '/mods/')

@bp.route('/edit/description', methods=['POST'])
def mod_editrules():
	sub = request.form.get('sub')
	rtext = escape(request.form.get('rtext'))
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	if len(rtext) < 1 or len(rtext) > 20000:
		return 'invalid rules text lngth'

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(sub)).exists()).scalar()
	if is_mod:
		desc = db.session.query(Sub).filter_by(name=sub).first()
		desc.rules = rtext
		db.session.add(desc)
		db.session.commit()
		
		flash('successfully updated description')
		return(redirect('/i/' + sub + '/info/'))
	else:
		return '403'

@bp.route('/nsfw',  methods=['POST'])
def mod_marknsfw():
	if 'username' not in session:
		flash('not logged in', 'danger')
		return redirect(url_for('login'))

	post_id = request.form.get('post_id')
	post = db.session.query(Post).filter_by(id=post_id).first()


	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(post.sub)).exists()).scalar()
	if is_mod:
		post.nsfw = True
		flash('marked as nsfw')
		db.session.commit()
		
		return redirect(post.get_permalink())
	return '403'

@bp.route('/title', methods=['POST'])
def mod_title():
	sub = request.form.get('sub')
	title = request.form.get('title')
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	if len(title) > 1000:
		return 'invalid title lngth'
	elif len(title) == 0:
		title = None

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(sub)).exists()).scalar()
	if is_mod:
		desc = db.session.query(Sub).filter_by(name=sub).first()
		desc.title = title
		db.session.add(desc)
		db.session.commit()
		flash('successfully updated title')
		
		return(redirect('/i/' + sub + '/info/'))
	else:
		return '403'

@bp.route('/settings', methods=['POST'])
def mod_settings():
	sub = request.form.get('sub')
	subr = normalize_sub(sub)
	marknsfw = 	request.form.get('marknsfw')
	newcss = request.form.get('newcss')

	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	if 'admin' in session:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub.like(sub)).exists()).scalar()
	if is_mod:
		sub = db.session.query(Sub).filter_by(name=sub).first()

		if marknsfw:
			if request.form.get('alsoposts'):
				for p in db.session.query(Post).filter_by(sub=subr):
					p.nsfw = True
				db.session.commit()
			sub.nsfw = True
		else:
			if request.form.get('alsoposts'):
				for p in db.session.query(Post).filter_by(sub=subr):
					p.nsfw = False
				db.session.commit()
			sub.nsfw = False

		if newcss != None:
			if len(newcss) < 20000:
				sub.css = newcss

		db.session.add(sub)
		db.session.commit()
		flash('successfully updated settings', 'success')
		
		return(redirect('/i/' + sub.name + '/info/'))
	else:
		return '403'
