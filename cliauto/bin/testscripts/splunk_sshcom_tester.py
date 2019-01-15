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
from cliautolib.cliauto_sshcom import sshcom
from cliauto_configconf import configconf
from cliautolib.cliauto_kvstore import cliauto_kvstore
import splunklib.binding as binding
import splunklib.client as client

fargs = {'tpw': '', u'spw': u'pass1', u'cmdtype': u'CLI', u'cmd': u'ls | less', 'tuser': '', u'suser': u'root', u'nodelist': u'nl1.csv'}
sargs = {u'user': u'admin', u'authtoken': u'TV9Y7tmzNilhL^4vWPmhR6HRMRHjmIvw3tSIlJEceDc2r0OW8bMqrIOtx1R2jA3jYD1uGGWQSZkEOWLr1yLNhXlKz^rCXdLOm2ExNKnEMAMpc3kJpI3YOyqpcV9k3LUtMKgO'}

ppid = os.getpid()
# Create configuration
objcfg = configconf(fargs, sargs, ppid)
if objcfg.status != 'Success':
    logging.debug('Error, creating pid object, err = ' + str(objcfg.status))
gc = objcfg.getconfig()

#pdb.set_trace()

# If getconfig unsuccessful, log errmsg and exit script
if gc != 'Success':
    logging.debug('Error, getconfig function, err = ' + str(gc))
    sys.exit(1)

logging.debug('endpoint: objcfg.hosts[0] = ' + str(objcfg.hosts[0]))


binding_service = binding.connect(token=sargs['authtoken'])
client_service = client.connect(token=sargs['authtoken'])
sk = cliauto_kvstore(binding_service)

sc = sshcom(fargs, sargs, ppid, sk, binding_service, client_service, objcfg)
r = sc.process_cmd()
print ("sc.response = " + str(sc.response))

