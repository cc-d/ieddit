legal_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'

def verify_username(username):
	if len(username) > 20 or len(username) < 1:
		return False
	for c in username:
		if c not in legal_chars:
			return False
	return True