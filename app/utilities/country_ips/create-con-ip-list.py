import sys
syscode = sys.argv[1].upper()

with open('blocks-4.csv', 'r') as b:
    a = b.read().splitlines()
    a = [c.split(',') for c in a]

with open('codes.txt', 'r') as co:
    codes = co.read().splitlines()
    cd = {}
    for c in codes:
        cs = c.split()
        cd[cs[0]] = cs[1]
print(cd)
a = [c[0:2] for c in a]

aa = []

import ipaddress
'''
for b in a:
    print(b[0])
    try:
        for i in ipaddress.IPv4Network(b[0]):
            aa.append({i:b[1]})
    except Exception as e:
        print(e)
        pass
'''
wip = []
swip = []
for z in a:
    try:
        if cd[z[1]] == syscode:
            print(z, cd[z[1]])
            wip.append(z[0])
            short = '.'.join(z[0].split('.')[0:2])
            if short not in swip:
                swip.append(short)
    except:
        pass

with open(syscode[0:2] + '.txt', 'w') as s:
        s.write('\n'.join(wip))

with open(syscode[0:2] + '-2.txt', 'w') as s2:
        s2.write('\n'.join(swip))
