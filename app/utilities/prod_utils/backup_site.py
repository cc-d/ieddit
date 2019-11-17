import os
import sys
from datetime import datetime

# for prod server only

filename = str(datetime.utcnow()).split('.')[0]
filename = filename.replace(' ', '_')
filename = filename.replace(':', '-')

print(filename)

if os.path.isdir('/site_backups') is not True:
	os.system('mkdir /site_backups/')


os.chdir('../../../../')
print(os.getcwd())

os.system('mkdir /site_backups/' + filename)
print('copying all ieddit files to site_backups')
os.system('cp -r ieddit/ /site_backups/' + filename)
print('creating database backup')
os.system('sudo su postgres -c "pg_dump ieddit > ~/' + filename + '.sql"')
