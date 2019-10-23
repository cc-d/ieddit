import sys
import os
sys.path.insert(1,os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from ieddit.ieddit import *
from ieddit.models import *

posts = db.session.query(Post).all()
for p in posts:
	p.permalink = p.permalink.replace('/r/','/i/')
	db.session.add(p)
comments = db.session.query(Comment).all()
for c in comments:
	c.permalink = c.permalink.replace('/r/','/i/')
	db.session.add(c)
db.session.commit()
