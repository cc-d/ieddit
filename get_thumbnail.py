import requests
import base64
import sys
import config
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import urllib.parse
import time
from ieddit import db
from models import Post

def add_remote_image(url, tid):
	p = db.session.query(Post).filter_by(id=tid).first()
	p.remote_image_url = url
	db.session.add(p)
	db.session.commit()
	print('post has remote image %s %s', url, tid)

def create_thumbnail(r, tid):
	#r.raw.decode_content = rue

	b = BytesIO(r.content)
	im = Image.open(b)
	size = 128, 128
	im.thumbnail(size)
	#im.save('thumbnails/' + str(tid) + '.JPEG', 'JPEG')
	im.save('static/thumb-' + str(tid) + '.PNG', 'PNG')
	#r = requests.get('http://127.0.0.1/clear_cache')
	print(r.text)

def main():
	#url = 'https://imgur.com/a/LpH5UiD'
	#tid = 1
	c = False
	#tid = int(sys.argv[1])
	#url = urllib.parse.unquote(sys.argv[2])
	url = 'https://i.redd.it/8ex7on41uzq31.png'
	tid = 1
	r = requests.get(url, proxies=config.PROXIES,  allow_redirects=True)

	if r.headers['Content-Type'].split('/')[0] == 'image':
		#ext = r.headers['Content-Type'].split('/')[1]
		create_thumbnail(r, tid)
		add_remote_image(url, tid)
		c = True
	else:
		soup = BeautifulSoup(r.text)
		image = soup.find('meta', property='og:image')
		try:
			iurl = image.get('content', None)
			r = requests.get(iurl, proxies=config.PROXIES, allow_redirects=True)
			soup = BeautifulSoup(r.text)
			if r.headers['Content-Type'].split('/')[0] == 'image':
				#ext = r.headers['Content-Type'].split('/')[1]
				create_thumbnail(r, tid)
				add_remote_image(iurl, tid)

		except:
			try:
				icon_link = soup.find("link", rel="shortcut icon")
				r = requests.get(icon_link['href'], proxies=config.PROXIES,  allow_redirects=True)
				soup = BeautifulSoup(r.text)
				create_thumbnail(r, tid)
			except:
				i = soup.findall('img')
				guess = 0
				src = ''
				limit = 0
				for im in i:
					try:
						limit += 1
						if limit > 15:
							break
						try:
							height = int(im.attrs.get('height', None))
							width = int(im.attrs.get('width', None))
						except:
							height=1
							width=1
						isrc = im.attrs.get('src', None)
						if (height * width) > guess:
							src = isrc
							guess = height * width
					except:
						pass
				if src != '':
					r = requests.get(i['href'], proxies=config.PROXIES)
					create_thumbnail(r, tid)

if __name__ == '__main__':
	main()
