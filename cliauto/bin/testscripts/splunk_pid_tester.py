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
from cliautolib.cliauto_pid import pid

fargs = {'tpw': '', u'spw': u'spw2', u'cmdtype': u'CLI', u'cmd': u'uptime', 'tuser': '', u'suser': u'su2', u'nodelist': u'nl2'}
sargs = {u'user': u'admin', u'authtoken': u'B0P8^L_7W9wpMSLaDNKniAgDtML0IMpNwz53N5QChWT6UQt3pc3nH167FU5fuktCxiYthORU8ZIufYa4qsUYN6h7F9RdlrqU8O32BWsmv076YGrXeFI0UrR'}
p = pid(fargs, sargs, os.getpid())

print ("p.response = " + str(p.response))

