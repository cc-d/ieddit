import requests
import base64
import sys
import config
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import urllib.parse

def create_thumbnail(r, tid):
	#r.raw.decode_content = True
	b = BytesIO(r.content)
	im = Image.open(b)
	size = 128, 128
	im.thumbnail(size)
	#im.save('thumbnails/' + str(tid) + '.JPEG', 'JPEG')
	im.save('static/thumb-' + str(tid) + '.JPEG', 'JPEG')

def main():
	#url = 'https://imgur.com/a/LpH5UiD'
	#tid = 1

	tid = int(sys.argv[1])
	url = urllib.parse.unquote(sys.argv[2])

	r = requests.get(url, proxies=config.PROXIES)
	if r.headers['Content-Type'].split('/')[0] == 'image':
		#ext = r.headers['Content-Type'].split('/')[1]
		create_thumbnail(r, tid)
	else:
		soup = BeautifulSoup(r.text)
		image = soup.find('meta', property='og:image')
		iurl = image.get('content', None)
		r = requests.get(iurl)
		if r.headers['Content-Type'].split('/')[0] == 'image':
			#ext = r.headers['Content-Type'].split('/')[1]
			create_thumbnail(r, tid)

if __name__ == '__main__':
	main()