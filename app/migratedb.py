import sys
sys.path.append('..')
sys.path.append('.')
#import os
#os.chdir('..')

from models import *


posts = db.session.query(Post).all()
for p in posts:
    #p.permalink = p.permalink.replace('/r/','/i/')
    p.permalink = p.permalink.replace(config.URL, + '/i/', '')
    db.session.add(p)
comments = db.session.query(Comment).all()
for c in comments:
    #c.permalink = c.permalink.replace('/r/','/i/')
    c.permalink = c.permalink.replace(config.URL, + '/i/', '')
    db.session.add(c)
db.session.commit()
