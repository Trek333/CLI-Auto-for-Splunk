import os
import sys
import json
import logging
import time
import errno
import pdb
#pdb.set_trace()

os.environ['SPLUNK_HOME'] = '/opt/splunk'
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Setup logging
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

#pdb.set_trace()
fargs = {'tpw': '', u'spw': u'pass1', u'cmdtype': u'CLI', u'cmd': u'ls | less', 'tuser': '', u'suser': u'root', u'nodelist': u'nl1.csv'}
sargs = {u'user': u'admin', u'authtoken': u'oFisl32bn70u0n6rJ5lhHiD^y9xL8rBJ_VbyV0_hQmr7NRLT_XVzqVFNaF6lEJpUZNiV56IJ27EHw5g5_R8wYsTishIP6fKvsQwD88e5HR591gHFywF6m0nbBnl0dN'}
cargs = {u'User-Agent': u'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', u'Content-Type': u'application/x-www-form-urlencoded; charset=UTF-8', u'Content-Length': u'105', u'X-Requested-With': u'XMLHttpRequest', u'Connection': u'keep-alive', u'Origin': u'https://192.168.209.128', u'Accept': u'text/javascript, text/html, application/xml, text/xml, */*', u'X-Splunk-Form-Key': u'15032468160448811592', u'Accept-Language': u'en-US,en;q=0.9', u'Accept-Encoding': u'gzip, deflate, br', u'Host': u'192.168.209.128', u'Cookie': u'mintjs%3Auuid=24049646-c5e2-4b96-813b-40e1cd1ec8c4; splunkd_443=oFisl32bn70u0n6rJ5lhHiD^y9xL8rBJ_VbyV0_hQmr7NRLT_XVzqVFNaF6lEJpUZNiV56IJ27EHw5g5_R8wYsTishIP6fKvsQwD88e5HR591gHFywF6m0nbBnl0dN; splunkweb_csrf_token_443=15032468160448811592; session_id_443=4222f839dd46c01681c4660707f79d2e36b3b8d2'}

ppid = os.getpid()

# Create configuration
objcfg = configconf(fargs, sargs, ppid)
if objcfg.status != 'Success':
    logging.debug('Error, creating configconf object, err = ' + str(objcfg.status))
    sys.exit(1)

# If getconfig unsuccessful, log errmsg and exit script
gc = objcfg.getconfig(False)
if gc != 'Success':
    logging.debug('Error, getconfig function, err = ' + str(gc))
    sys.exit(1)

logging.debug('endpoint: objcfg.hosts[0] = ' + str(objcfg.hosts[0]))

binding_service = binding.connect(token=sargs['authtoken'])
client_service = client.connect(token=sargs['authtoken'])
sk = cliauto_kvstore(binding_service)

#def __init__(self, fargs, sargs, cargs, ppid, sk, binding_service, client_service, objcfg):
sc = sshcom(fargs, sargs, cargs, ppid, sk, binding_service, client_service, objcfg)
r = sc.hb_tester()
print ('os.environ[PYTHONHTTPSVERIFY] = ' + str(os.environ['PYTHONHTTPSVERIFY']))
print ("sc.status = " + str(sc.status))
print ("r = " + str(r))

