import requests
from datetime import datetime
import sys

a = datetime.now()
z = int(sys.argv[1])
for i in range(z):
        r = requests.get('http://localhost')
print(datetime.now() - a)
