from ieddit import *
import json

ubp = Blueprint('user', 'user', url_prefix='/user')

@ubp.route('/delete/post/',  methods=['POST'])
def delete_post():
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
		return 403

@ubp.route('/delete/comment/',  methods=['POST'])
def delete_comment():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))
	cid = request.form.get('comment_id')
	comment = db.session.query(Post).filter_by(id=cid).first()
	post = db.session.query(Post).filter_by(id=comment.parent_id).first()

	if comment.author == session['username']:
		comment.deleted = True
		db.session.commit()
		cache.delete_memoized(get_subi)
		flash('post deleted', category='success')
		return redirect(post.permalink)
	else:
		return 403


@ubp.route('/edit/<itype>/<iid>/', methods=['GET'])
def get_edit(itype, iid):
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))
	if itype == 'post':
		obj = db.session.query(Post).filter_by(id=iid).first()
		if hasattr(obj, 'self_text'):
			etext = obj.self_text
		else:
			return 403
	elif itype == 'comment':
		obj = db.session.query(Comment).filter_by(id=iid).first()
		etext = obj.text
	else:
		return 'bad itype'
	return render_template('edit.html', itype=itype, iid=iid, etext=etext)

@ubp.route('/edit',  methods=['POST'])
def edit_post():
	if 'username' not in session:
		flash('not logged in', 'error')
		return redirect(url_for('login'))
	itype = request.form.get('itype')
	iid = request.form.get('iid')
	etext = request.form.get('etext')

	if len(etext) < 1 or len(etext) > 20000:
		return 'invalid edit length'

	if config.CAPTCHA_ENABLE:
		if captcha.validate() == False:
			flash('invalid captcha', 'danger')
			return redirect('/user/edit/%s/%s/' % (itype, iid))
		if 'rate_limit' in session and config.RATE_LIMIT == True:
			rl = session['rate_limit'] - time.time()
			if rl > 0:
				flash('rate limited, try again in %s seconds' % str(rl))
				if 'last_url' in session:
					return redirect('/user/edit/%s/%s/' % (itype, iid))
				return redirect('/')

	if itype == 'post':
		obj = db.session.query(Post).filter_by(id=iid).first()
	elif itype == 'comment':
		obj = db.session.query(Comment).filter_by(id=iid).first()
	else:
		return 'bad itype'

	if obj.author != session['username']:
		return 403

	if hasattr(obj, 'self_text'):
		obj.self_text = etext
		obj.edited = True
		db.session.commit()
		cache.clear()
		flash('post edited', category='success')
		return redirect(obj.permalink)
	elif hasattr(obj, 'text'):
		obj.edited = True
		obj.text = etext
		db.session.commit()
		cache.delete_memoized(c_get_comments)
		flash('comment edited', category='success')
		return redirect(obj.permalink)
	else:
		return 403