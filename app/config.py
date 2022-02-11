DEBUG = True

SUB_PREFIX = '/i/'

# Database Name
DATABASE = 'ieddit'

# PostgreSQL
PG_USER = 'test'
PG_PASSWORD = 'test'
PG_HOST = 'localhost'

DB_TYPE = 'sqlite'
USE_RECREATE = True

if DB_TYPE == 'sqlite':
    DATABASE_URI = 'sqlite:///{0}.db'.format(PG_USER)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{0}.db'.format(PG_USER)

elif DB_TYPE == 'postgres':
    DATABASE_URI = 'postgres://{0}:{1}@{2}:5432/{3}'.format(PG_USER, PG_PASSWORD, PG_HOST, DATABASE)
    SQLALCHEMY_DATABASE_URI = 'postgres://{0}:{1}@{2}:5432/{3}'.format(PG_USER, PG_PASSWORD, PG_HOST, DATABASE)

# This will be unique every time create_db.py is ran when testing
# to force clear sessions
SECRET_KEY = 'not-a-real-key-|r|Xuu4433Coj|r|'

# Change this to your local URL. IE http://127.0.0.1
URL = 'http://dev.ieddit.com'

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Contet-security
CSP = False
SESSION_COOKIE_SAMESITE='Lax'

CACHE_TYPE = 'simple'
DEFAULT_CACHE_TIME = 600

# Specific rate limit times in seconds
SUB_RATE_LIMIT = '3 per second; 3 per minute'
COMMENT_RATE_LIMIT = '3 per second; 5 per minute'
POST_RATE_LIMIT = '3 per second; 5 per minute'
MESSAGE_RATE_LIMIT = '3 per second; 10 per minute'
REGISTER_RATE_LIMIT = '3 per second; 5 per minute'
LOGIN_RATE_LIMIT = '3 per second; 25 per minute'
RECOVERY_EMAIL_RATE_LIMIT = '3 per second; 5 per hour'

LIMITER_DEFAULTS = ['600 per minute']

USE_PROXIES = False

MAIL_TYPE = 'mailgun'
MAIL_FROM = 'no-reply@ieddit.com'
if MAIL_TYPE == 'mailgun':
    MG_API_KEY = 'notarealkey'
    MG_URL = 'https://api.mailgun.net/v3/ieddit.com'

if USE_PROXIES:
    with open('proxies.txt', 'r') as p:
        proxy = p.read().strip()
        PROXIES = {'http':'http://' + proxy, 'https':'https://' + proxy}
else:
    PROXIES = None

PHEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}

# Sentry settings. your_dsn should be something like https://hashstring@sentry.io/appno. You can get one by registering at sentry.io
SENTRY_ENABLED = False
SENTRY_DSN = 'your_dsn'

DISCORD_ENABLED = False
DISCORD_URL = ''

# For any api functions which only site operator should be able to use
API_OPER_KEY = 'not-a-real-key'

DOWNVOTE_COLOR = 'deepskyblue'
UPVOTE_COLOR = 'orange'

AVG_DOWN_COLOR = '#66c5e5'
AVG_UP_COLOR = '#e5b866'

DEFAULT_LANGUAGE = 'en'
LANGUAGES = ['en', 'fr', 'es']

# Values for default admin/test user after creating a test database
# for a freshly created local dev deployment
TEST_ADMIN_USERNAME = 'admin'
TEST_ADMIN_PASSWORD = 'admin'
TEST_ADMIN_EMAIL = 'admin@admin.com'

TEST_USER_USERNAME = 'test'
TEST_USER_PASSWORD = 'test'
TEST_USER_EMAIL = 'test@test.com'