from __future__ import absolute_import
import sys, os
os.environ['PYTHONHTTPSVERIFY'] = '0'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import splunklib.client as client
import pdb
import time
try:
    from utils import *
except ImportError:
    raise Exception("Add the SDK repository to your PYTHONPATH to run the examples "
                    "(e.g., export PYTHONPATH=~/splunk-sdk-python.")

fargs = {'tpw': '', u'spw': u'spw2', u'cmdtype': u'CLI', u'cmd': u'uptime', 'tuser': '', u'suser': u'su2', u'nodelist': u'nl2'}
sargs = {u'user': u'admin', u'authtoken': u'if48vkdKFf1I7^j9IsL4beaU2KjmSh6eOnWqcHU9_OLWEczUqZPoyvzzm7NPvozIp0qSQKCEZnYZkNo6gt2oCOHw5BCC6ZzNUSSo8D9CcOJMx2aOy2i2Wr3K'}

service = client.connect(token=sargs['authtoken'])
cn = service.indexes["main"].attach(host='127.0.0.1', source='source', sourcetype='sourcetype')
data = 'total 8\r\n-rw-------. 1 root root 1575 Sep 19 09:24 anaconda-ks.cfg\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Desktop\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Documents\r\ndrwxr-xr-x. 4 root root  199 Sep 19 12:02 Downloads\r\n-rw-r--r--. 1 root root 1623 Sep 19 09:27 initial-setup-ks.cfg\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Music\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Pictures\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Public\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Templates\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Videos\r\n'
data = 'drwxr-xr-x. 2 root root    6 Sep 19 09:28 Desktop\r\n'
data = 'drwxr-xr-x.2rootroot6Sep1909:28Desktop\r\n'
data = 'drwxr-xr-x. 2 root root6 Sep 19 09:28 Desktop\r\n'
data = 'drwxr-xr-x. 2 root root    6 Sep 19 09:28 Desktop\r\n'
data = '2 root root    6 Sep 19 09:28 Desktop\r\n'
data = 'drwxr-xr-x. 2 root root    6 Sep 19 0928 Desktop\r\n'
#data = 'test2\r\ntest2\r\n'
#data = 'test 3\r\ntest 3\r\n'
data = 'test:4\r\ntest 4\r\n'
data = 'test 5:5\r\ntest 5\r\n'
data = 'test 09:28\r\ntest 6\r\n'
data = 'test 9:28\r\ntest 7\r\n'
#data = '***SPLUNK*** pid=123 record_num=1\r\ntest1\r\ntest 1\r\n'
data = '***SPLUNK*** host=123\r\ntest1\r\ntest 1\r\n'
data = '1 : 2 : 3,4\r\n5,6,7,8\r\n'
data = "May 11 10:40:48 scrooge disk-health-nurse[26783]: [ID 702911 user.error] m:SY-mon-full-500 c:H : partition health measures for /var did not suffice - still using 96% of partition space"
data="2018-09-21 14:52:18,716 Started write_attach"
data="2018-09-21 14:52:18,715 pid=1|cliautofieldsep|str(type(r)) = <type 'int'>"
data="2018-09-21 15:10:18,716 total 8\r\n-rw-------. 1 root root 1575 Sep 19 09:24 anaconda-ks.cfg\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Desktop\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Documents\r\ndrwxr-xr-x. 4 root root  199 Sep 19 12:02 Downloads\r\n-rw-r--r--. 1 root root 1623 Sep 19 09:27 initial-setup-ks.cfg\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Music\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Pictures\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Public\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Templates\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Videos\r\n"

current_time = time.localtime()
data = time.strftime('%Y-%m-%d %H:%M:%S,%03d', current_time) + ' ' + data

print data

lines = data.split('\r\n')
print(lines)

#pdb.set_trace()
#s = client.connect(token=sargs['authtoken'])
#index = s.indexes['main']
#with index.attached_socket(sourcetype='sourcetype', source='source') as sock:
    #sock.send('Test event\r\n')
    #sock.send(data)

for line in lines:
    line = line.rstrip('\r\n')
    if len(line) == 0: break
    #line = line + ' - '
    #line = line.encode(encoding='UTF-8',errors='strict')
    print line
    r = cn.write(line)
    print str(r)
    time.sleep(0.1)
cn.close()
