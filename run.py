from sys import argv
from ieddit.ieddit import app

def main(port=80):
	app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
	try:
		port = int(argv[1])
		main(port)
	except:
		main()


