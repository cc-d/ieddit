from ieddit import *
import json

bp = Blueprint('mod', 'mod', url_prefix='/mod')

@bp.route('/actions/')
def hello():
	a = ''
	actions = db.session.query(Mod_action).all()
	for act in actions:
		a += '<br>'.join(['Mod ' + act.username, 'Action ' + act.action, 'Permalink ' + act.url])
		a += '<br><br>'
	return a

def mod_action(username, action, url):
	new_action = Mod_action(username=username, action=action, url=url)
	db.session.add(new_action)
	db.session.commit()

@bp.route('/delete/post/',  methods=['POST'])
def delete_post():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))
	pid = request.form.get('post_id')
	post = db.session.query(Post).filter_by(id=pid).first()
	sub_url = config.URL + '/r/' + post.sub
	if session['admin']:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub_name.like(post.sub)).exists()).scalar()
	if is_mod:
		#db.session.delete(post)
		post.deleted = True
		mod_action(session['username'], 'delete', post.permalink)
		db.session.commit()
		cache.delete_memoized(get_subi)
		flash('post deleted', category='success')
		return redirect(sub_url)
	else:
		return 403

@bp.route('/delete/comment/', methods=['POST'])
def delete_comment():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))
	cid = request.form.get('comment_id')
	comment = db.session.query(Comment).filter_by(id=cid).first()
	post = db.session.query(Post).filter_by(id=comment.post_id).first()

	if session['admin']:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub_name.like(post.sub)).exists()).scalar()
	if is_mod:
		comment.deleted = True
		mod_action(session['username'], 'delete', comment.permalink)
		db.session.commit()
		cache.delete_memoized(c_get_comments)
		cache.clear()
		flash('comment deleted', category='success')
		return redirect(post.permalink)		
	else:
		return 403

@bp.route('/sticky/post/', methods=['POST'])
def sticky_post():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	pid = request.form.get('post_id')
	post = db.session.query(Post).filter_by(id=pid).first()

	if session['admin']:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub_name.like(post.sub)).exists()).scalar()
	if is_mod:
		old_sticky = db.session.query(Post).filter_by(sub=post.sub, stickied=True).all()
		for s in old_sticky:
			s.stickied = False
			db.session.commit()	
			mod_action(session['username'], 'unstickied', post.permalink)

		post.stickied = True
		db.session.commit()
		cache.delete_memoized(get_subi)
		cache.clear()
		mod_action(session['username'], 'stickied', post.permalink)
		flash('stickied post', category='success')
		return redirect(config.URL + '/r/' + post.sub)
	else:
		return 403


@bp.route('/unsticky/post/', methods=['POST'])
def unsticky_post():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	pid = request.form.get('post_id')
	post = db.session.query(Post).filter_by(id=pid).first()

	if session['admin']:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub_name.like(post.sub)).exists()).scalar()
	if is_mod:
		mod_action(session['username'], 'unstickied', post.permalink)
		post.stickied = False
		db.session.commit()
		cache.delete_memoized(get_subi)
		cache.clear()
		flash('unstickied post', category='success')
		return redirect(config.URL + '/r/' + post.sub)
	else:
		return 403

@bp.route('/lock/post', methods=['POST'])
def lock_post():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))

	pid = request.form.get('post_id')
	post = db.session.query(Post).filter_by(id=pid).first()

	if post.locked == False:
		action = 'lock'
	else:
		action = 'unlock'

	if session['admin']:
		is_mod = True
	else:
		is_mod = db.session.query(db.session.query(Moderator).filter(Moderator.username.like(session['username']),
					Moderator.sub_name.like(post.sub)).exists()).scalar()
	if is_mod:
		if action == 'lock':
			mod_action(session['username'], 'unstickied', post.permalink)
			post.locked = True
		elif action == 'unlock':
			mod_action(session['username'], 'unlocked', post.permalink)
			post.locked = False

		db.session.commit()
		cache.delete_memoized(get_subi)
		cache.clear()
		flash('locked post', category='success')
		return redirect(config.URL + '/r/' + post.sub)
	else:
		return 403

