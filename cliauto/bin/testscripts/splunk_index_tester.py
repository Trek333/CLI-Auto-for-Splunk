import os
import sys
import json
import logging
import time
import errno
import pdb
#pdb.set_trace()

# Setup logging
os.environ['SPLUNK_HOME'] = '/opt/splunk'
os.environ['PYTHONHTTPSVERIFY'] = '0'
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logging.basicConfig(format='%(asctime)s %(message)s', filename=logfile,level=logging.DEBUG)

# Append directory of this file to the Python path to be able to import cliauto libs
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
sys.path = ['/opt/splunk/etc/apps/cliauto/bin/cliautolib'] + sys.path
sys.path = ['/opt/splunk/lib/python2.7/site-packages/splunk/persistconn'] + sys.path
print str(sys.path)

# Import cliauto and Splunk SDK libs
import splunklib.client as client
import splunklib.binding as binding
from cliautolib.cliauto_index import cliauto_index
from cliautolib.cliauto_kvstore import cliauto_kvstore

def get_any_item(items):
    for item in items:
        return item

fargs = {'tpw': '', u'spw': u'spw2', u'cmdtype': u'CLI', u'cmd': u'uptime', 'tuser': '', u'suser': u'su2', u'nodelist': u'nl2'}
sargs = {u'user': u'admin', u'authtoken': u'S6A1zabz^k4vP1jZB9RaVvDQXITZmjMos4b7YMPME3JDc7lwr9prD9qvqfhhZM6WW2AQaJgA356o_PFfmhfKIsLd0BeOnaXSbl9SCk30NysExL1ZgRIRZorHPNfX'}
cur_parallel_ssh_results = {}
cur_parallel_ssh_results['127.0.0.1'] = {'resultstatus': 'Test', 'iteration': 1, 'host': 'Splunk_Training', 'ip_address': '127.0.0.1', 'result': 'test', 'resultraw': 'total 8\r\n-rw-------. 1 root root 1575 Sep 19 09:24 anaconda-ks.cfg\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Desktop\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Documents\r\ndrwxr-xr-x. 4 root root  199 Sep 19 12:02 Downloads\r\n-rw-r--r--. 1 root root 1623 Sep 19 09:27 initial-setup-ks.cfg\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Music\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Pictures\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Public\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Templates\r\ndrwxr-xr-x. 2 root root    6 Sep 19 09:28 Videos\r\n'}

print str(type(cur_parallel_ssh_results))
print (str(type(cur_parallel_ssh_results['127.0.0.1'])))
print("cur_parallel_ssh_results[host] = " + str(cur_parallel_ssh_results['127.0.0.1']))

pdb.set_trace()
serviceb = binding.connect(token=sargs['authtoken'])
sk = cliauto_kvstore(serviceb)
gk = sk.get_items("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection")
print ("gk[0] = " + str(gk[0]))
#print ("gk[1] = " + str(gk[1]))
item = get_any_item(gk[1])

data = str(cur_parallel_ssh_results['127.0.0.1']['result'])
#data = "test1"
print("data = " + str(data))
service = client.connect(token=sargs['authtoken'])
pdb.set_trace()
#ci = cliauto_index(service, "main", sargs)
ci = cliauto_index(service, "main")
if ci.status != "Success":
    print("Unable to create cliauto_index to write results to index")

#cw = ci.write_attach("127.0.0.1", "ssh", "cliauto", "1", data)
cw = ci.write_submit(cur_parallel_ssh_results['127.0.0.1'], "cliauto", "cliauto_ssh", item)
if cw != "Success":
    print("Unable to write results to index, host = 127.0.0.1")
