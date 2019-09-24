from ieddit import *

bp = Blueprint('mod', 'mod', url_prefix='/mod')

@bp.route('/hello/')
def hello():
	return 'h'

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
		db.session.delete(post)
		db.session.commit()
		cache.delete_memoized(get_subi)
		flash('post deleted')
		return redirect(sub_url)
	else:
		return 403