import os
import sys
import json
import logging
from logging.config import fileConfig
import time
import errno
from datetime import datetime
import pdb
#pdb.set_trace()

# Setup logging
os.environ['SPLUNK_HOME'] = '/opt/splunk'
os.environ['PYTHONHTTPSVERIFY'] = '0'
#logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
#logging.basicConfig(format='%(asctime)s %(message)s', filename=logfile,level=logging.DEBUG)
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

# Append directory of this file to the Python path to be able to import cliauto libs
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Import cliauto and Splunk SDK libs
from cliautolib.cliauto_kvstore import cliauto_kvstore
import splunklib.binding as binding

def create_insert_request_body(fargs, sargs, status):
    try:

        pdb.set_trace()
        pattern = '%d.%m.%Y %H:%M:%S'
        dt = str(datetime.now().strftime(pattern))
        epoch_now = str(int(time.mktime(time.strptime(dt, pattern)))*1000)

        reqbody = '{ "Status": "' + status + '", "NodeList": "' + fargs['nodelist'] + '", "TargetUser": "' + fargs['tuser'] + '", "Timestamp": "' + epoch_now + '", "PID": "45548", "SessionUser": "' + sargs['user'] + '", "CommandType": "' + fargs['cmdtype'] + '", "Command": "' + fargs['var1'] + '", "ScriptUser": "' + fargs['suser'] + '" }'
        return ['Success', reqbody]

    except Exception as err:
        return ['Error, create_insert_request_body method, err = ' + str(err), '']

def create_update_request_body(fargs, sargs, status):
    try:

        pdb.set_trace()
        pattern = '%d.%m.%Y %H:%M:%S'
        dt = str(datetime.now().strftime(pattern))
        epoch_now = str(int(time.mktime(time.strptime(dt, pattern)))*1000)

        # All fields of the KVStore item must be included in the http request body or the fields will be updated with no values or empty values
        reqbody = '{ "Status": "' + status + '", "NodeList": "' + fargs['nodelist'] + '", "TargetUser": "' + fargs['tuser'] + '", "Timestamp": "' + epoch_now + '", "PID": "45548", "SessionUser": "' + sargs['user'] + '", "CommandType": "' + fargs['cmdtype'] + '", "Command": "' + fargs['var1'] + '", "ScriptUser": "' + fargs['suser'] + '" }'
        #reqbody = '{ "Status": "' + status + '", "Timestamp": "' + epoch_now + '" }'
        return ['Success', reqbody]

    except Exception as err:
        return ['Error, create_insert_request_body method, err = ' + str(err), '']


fargs = {'tpw': '', u'spw': u'spw2', u'cmdtype': u'CLI', u'var1': u'uptime', 'tuser': '', u'suser': u'tu2', u'nodelist': u'nl2'}
sargs = {u'user': u'admin', u'authtoken': u'GiX61cQzRvZdBeYZsC3UsM3v95dl7PvXPXximuRDe86zzy6c5BGj3Y6M9VjARvuShzuQl3jyvUDGT3Pl6iebBngDBH5Idvw4RFqGc91E_60_JkG1mwar_b4d^jKZxe7cdH22n8VY^o0'}
pattern = '%d.%m.%Y %H:%M:%S'
date_time = str(datetime.now().strftime(pattern))
epoch = int(time.mktime(time.strptime(date_time, pattern)))
print date_time
print epoch
pdb.set_trace()
service = binding.connect(token=sargs['authtoken'])
sk = cliauto_kvstore(service)
#gk = sk.get_items("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection")
#gk = sk.get_items("/servicesNS/nobody/cliauto/data/lookup-table-files/sw1.csv")
gk = sk.get_items("/servicesNS/nobody/cliauto/storage/collections/config")
print ("gk[0] = " + str(gk[0]))
print ("gk[1] = " + str(gk[1]))
pids = gk[1]
print(str(pids))
for item in pids:
    if item['Status'] == 'Busy':
        print('Hi')
#print (sys.path)

#cirb = create_insert_request_body(fargs, sargs, 'Busy')
#if cirb[0] == 'Success':
#    req_body = cirb[1]
#    pdb.set_trace()
#    gk = sk.insert_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection", req_body)
#    print gk
#else:
#    print cirb

st = gk[1][0]['StartTime']
key = gk[1][0]['_key']
ppid = os.getpid()
curb = sk.create_pid_update_request_body(fargs, sargs, ppid, 'Test2', st)
if curb[0] == 'Success':
    req_body = curb[1]
    pdb.set_trace()
    ui = sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + key, req_body)
    print ui

