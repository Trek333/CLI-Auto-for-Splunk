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

# Import cliauto and Splunk SDK libs
import splunklib.results as results
import splunklib.client as client
from cliautolib.cliauto_search import cliauto_search

fargs = {'tpw': '', u'spw': u'spw2', u'cmdtype': u'CLI', u'cmd': u'uptime', 'tuser': '', u'suser': u'su2', u'nodelist': u'nl2'}
sargs = {u'user': u'admin', u'authtoken': u'b2I3zWU6ih74qpmft8oZiTiI0vgvAJSRtNAUnKAdGSS3SKbZBRhdmAe4o3FXJ4so1pJJvXG3Ja1kcZQ8hPCSLPlkDpk5C8wNMa9wihPKbqz4^Y3lX^LuO9RbShEGxiIz^N'}

service = client.connect(token=sargs['authtoken'],app='cliauto')

#searchlist = {'args': ['| inputlookup cliauto_pid_lookup'], 'kwargs': {'username': 'admin', 'password': 'pass1', 'host': 'localhost', 'version': '6.6.3', 'scheme': 'https', 'port': '8089'}}
#searchlist = {'args': ['| inputlookup cliauto_pid_lookup'], 'kwargs': {}}


searchlist = {'args': ['| inputlookup sw1_keep_private_no_read_write.csv'], 'kwargs': {}}
print searchlist
s = cliauto_search(service, searchlist)
print ("s.search_parse_status = " + str(s.search_parse_status))
pids = s.search_sync()
print(str(pids))
#print(str(s.results))
reader = results.ResultsReader(s.results)
a = []
for item in reader:
    a.append(item)
    print(item)
print "Results are a preview: %s" % reader.is_preview
#pdb.set_trace()
# It appears that ResultsReader destroys input
#reader = results.ResultsReader(s.results)
#for item in reader:
#    print(item)
#print "Results are a preview: %s" % reader.is_preview


