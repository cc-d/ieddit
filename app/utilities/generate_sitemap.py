import os, sys
abspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, abspath) 
os.chdir(abspath)

from ieddit import *
from html import escape

def gl(loc, lastmod=None, changefreq=None, priority=None):
    if loc != None:
        l = '<loc>%s</loc>' % escape(loc)
    else:
        l = ''
    if changefreq == None:
        c = ''
    else:
        c = '<changefreq>%s</changefreq>' % changefreq

    if priority == None:
        p = ''
    else:
        p = '<priority>%s</priority>' % priority


    return '<url>%s%s%s</url>' % (l, c, p)

def main():
    links = [gl(config.URL, priority=1)]
    links.append(gl(config.URL + '/?hot', priority=1))
    links.append(gl(config.URL + '/?top', priority=1))
    links.append(gl(config.URL + '/?new', priority=1))
    links.append(gl(config.URL + '/comments/', priority=1))
    links.append(gl(config.URL + '/about/', priority=1))
    links.append(gl(config.URL + '/create', priority=1))
    links.append(gl(config.URL + '/create_posts', priority=1))
    links.append(gl(config.URL + '/explore/', priority=1))
    links.append(gl(config.URL + '/stats/', priority=0.9))

    subs = db.session.query(Sub).all()
    for s in subs:
        links.append(gl(config.URL + '/i/' + s.name + '/', priority=0.9))

    posts = db.session.query(Post).all()
    for post in posts:
        links.append(gl(post.permalink, priority=0.8))

    users = db.session.query(Iuser).all()
    for user in users:
        links.append(gl(config.URL + '/u/' + user.username + '/', priority=0.7))

    with open('static/sitemap.xml', 'w') as s:
        w = '<?xml version="1.0" encoding="UTF-8"?>\n'
        w += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        w += '\n'.join(links)
        w += '\n</urlset>'
        s.write(w)

if __name__ == '__main__':
    main()
