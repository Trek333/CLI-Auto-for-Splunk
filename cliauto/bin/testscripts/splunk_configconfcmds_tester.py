import os
import sys
import json
import logging
import time
import errno
import pdb
import xml.dom.minidom
#pdb.set_trace()

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
sargs = {u'user': u'admin', u'authtoken': u'YJuajwMFxdeV7bwAWZ81OHR^R2O6P_vGihbdnd_ux^y3q6dWBGMbf_3mGoBLiBZmKNm^3qQImbpJ^Y^NuxRaLnKMDzJzr_r8Ni9HC^bmfWDQUxERmTBLUlXSBFDl9QUH'}
cc = configconf(fargs, sargs, os.getpid())
print str(cc)
gcc = cc.getconfigcmds()
#print str(gcc[1][0])
#print str(type(gcc[1][0]))
stanzas= []
for key in gcc[1]:
    print key.getAttribute('name')
    k = key.childNodes[0].nodeValue
    print str(k)
    #stanzas.append(str(k))



