import urllib.parse
legal_chars = '01234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'

def verify_username(username):
	if len(username) > 20 or len(username) < 1:
		return False
	for c in username:
		if c not in legal_chars:
			return False
	return True

def verify_subname(subname):
	if len(subname) > 30 or len(subname) < 1:
		return False
	for c in subname:
		if c not in legal_chars:
			return False
	return True

def convert_ied(url):
	url = url.lower()
	url = url.replace(' ', '_')
	url = urllib.parse.quote(url)[:75]

	return url

def nested_keys(comments, tree):
	paths = {0:['tree']}
	depth = 0
	safety = 50
	while len(comments) > 0:
		paths[depth+1] = []
		tkeys = []
		if depth == 0:
			for z in tree.keys():
				paths[1].append('tree[' + str(z) + ']')
				comments = [a for a in comments if a.id != z]
		else:
			for p in paths[depth-1]:
				for com in [c for c in comments]:
					try:
						print(str(vars(com)))
						eval(p + '[' + str(com.parent_id )+ ']')[com.id] = {}
						comments.remove(com)
					except KeyError as e:
						print(e)

		depth += 1
		if depth == safety:
			break
	return tree

def create_comment_tree(comments):
	tree = {}
	for i in [c for c in comments if c.parent_id == None]:
		tree[i.id] = {}
		comments.remove(i)

	tree=nested_keys(comments, tree)

			
	return tree