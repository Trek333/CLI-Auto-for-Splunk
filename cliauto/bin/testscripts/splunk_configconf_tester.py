import os
import sys
import json
import logging
import time
import errno
import pdb
pdb.set_trace()

# Setup logging
os.environ['SPLUNK_HOME'] = '/opt/splunk'
os.environ['PYTHONHTTPSVERIFY'] = '0'
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logging.basicConfig(format='%(asctime)s %(message)s', filename=logfile,level=logging.DEBUG)

# Append directory of this file to the Python path to be able to import cliauto libs
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Import cliauto and Splunk SDK libs
from cliautolib.cliauto_configconf import configconf

fargs = {'tpw': '', u'spw': u'spw2', u'cmdtype': u'CLI', u'cmd': u'uptime', 'tuser': '', u'suser': u'tu2', u'nodelist': u'nl3.csv'}
sargs = {u'user': u'admin', u'authtoken': u'LyEqIbn7VEZ2lL4eIYW^gYMI46_NYM5dM^SD^fkB_1Rmn5b7zToIBGO3Po25wTKYQonELW058iU2uCePDWm7d4YPXGeAGPoogEBXP9U046UdrH2JET0GSEmGkhOTkJVn^Hg'}
cc = configconf(fargs, sargs, os.getpid())
print str(cc)
gc = cc.getconfig()
print str(gc)

