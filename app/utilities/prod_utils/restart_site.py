import os
import sys

# only used for prod site

print('restarting site')
aux = os.popen("ps aux").read().splitlines()
for line in aux:
	if line.find('website python3 run.py') != -1:
		pid = line.split()[1]

print(pid)

os.system('kill -9 %s' % pid)

os.chdir('..')
os.chdir('..')

os.system('screen -dmS website python3 run.py 8000')

print('site restarted')
