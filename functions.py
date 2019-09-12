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
	new_url = ''

	for c in url:
		if c in legal_chars:
			new_url += c
		elif c == ' ':
			new_url += '_'
		if len(url) >= 75:
			break

	if len(url) == 0:
		new_url = 'empty'

	return new_url