from ieddit import *
import json

bp = Blueprint('mod', 'mod', url_prefix='/mod')

@bp.route('/actions/')
def hello():
	a = ''
	actions = db.session.query(Mod_action).all()
	for act in actions:
		a += str(vars(act)) + '\n\n'
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
		flash('comment deleted', category='success')
		return redirect(post.permalink)		
	else:
		return 403