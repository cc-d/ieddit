from share import *
import uuid

users = db.session.query(Iuser).all()
for u in users:
    u.anon_id = str(uuid.uuid4())
    db.session.add(u)
    db.session.commit()
    print(u, u.anon_id)
