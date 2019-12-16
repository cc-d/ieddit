import os
import sys
from datetime import datetime

# for prod server only

install_dir = '/home/ccarterdev/i2/ieddit/'
postgres_dir = '/var/lib/postgresql/'

a = os.popen('whoami').read().strip()
if a != 'root':
    print('not running as root user')
    sys.exit()

filename = str(datetime.utcnow()).split('.')[0]
filename = filename.replace(' ', '_')
filename = filename.replace(':', '-')

print(filename)

if os.path.isdir('/site_backups') is not True:
    print('/site_backups/ not found, creating')
    os.system('mkdir /site_backups/')

if os.popen('stat /site_backups').read().splitlines()[3].split()[1].split('/')[1][:-1] != 'drwx------':
    os.system('chmod -R 700 /site_backups/')

os.chdir(install_dir +'..')
print(os.getcwd())

print('copying all ieddit files to /site_backups/%s' % filename)
os.system('cp -r ieddit/ /site_backups/' + filename)

print('creating database backup')
os.system('su postgres -c "pg_dump ieddit > ~/' + filename + '.sql"')

#/home/ccarterdev
print('moving database backup to site backup dir')

print('postgres dir ' + postgres_dir)

os.system('mv ' + postgres_dir + filename + '.sql /site_backups/' + filename + '/')

print('zipping newly crated backup dir')
os.system('zip -r /site_backups/' + filename + '.zip /site_backups/' + filename + '/*')

print(os.popen('ls -la /site_backups').read())
print('deleted leftover dir')
os.system('rm -rf /site_backups/' + filename)
print(os.popen('ls -la /site_backups').read())

print('completed')
