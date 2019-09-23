DEBUG = True
#DATABASE_URI = 'sqlite:///test.db'
#SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
DATABASE_URI = 'postgres://test:test@localhost:5432/ieddit'
SQLALCHEMY_DATABASE_URI = 'postgres://test:test@localhost:5432/ieddit'
# This will be unique every time create_db.py is ran when testing
# to force clear sessions
SECRET_KEY = 'not-a-real-key-|r|ZBDtFtSf6q|r|'
URL = 'http://dev.ieddit.com'
SQLALCHEMY_TRACK_MODIFICATIONS = False
#SESSION_COOKIE_SAMESITE='Lax'
