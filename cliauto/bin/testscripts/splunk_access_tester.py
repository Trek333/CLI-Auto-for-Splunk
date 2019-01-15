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
from cliautolib.cliauto_access import cliauto_access
import splunklib.binding as binding

fargs = {'tpw': '', u'spw': u'spw2', u'cmdtype': u'CLI', u'cmd': u'uptime', 'tuser': '', u'suser': u'tu2', u'nodelist': u'nl3.csv'}
sargs = {u'user': u'admin', u'authtoken': u'D8cXOHoNW3JQZ1crnkapGuU7SNyQ8D9TGoFpCikE2riJtnJ_Rh7mLLWQ7lKOX9tuZLpT^cGozhEMFKC3bQPuzdufL7svYIc6^Cb6YCqCnJx7v5xoDhLCk8hvVR0jwT4qKemw5xJiFJC'}
#pdb.set_trace()

#binding_service = binding.connect(token=sargs['authtoken'])
ca = cliauto_access(sargs)
guc = ca.get_user_capabilities('/services/authentication/users/' + str(sargs['user']))

print str(guc)
