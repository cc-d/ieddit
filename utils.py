from hashlib import md5
from flask import request


def get_md5_user_agent():
    return md5(str(request.user_agent).encode('utf-8')).hexdigest()
