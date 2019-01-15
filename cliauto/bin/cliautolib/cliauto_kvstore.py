from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import re
import json
import logging
from logging.config import fileConfig
import time

# Append directory of this file to the Python path (sys.path) to be able to import cliauto libs
if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

class cliauto_kvstore(object):

    def __init__(self, service):


        # Processing the request
        try:
            self.status = "Failure"
            logging.info('Creating cliauto_kvstore...')
            self.service = service
            self.status = "Success"

        except Exception as err:
            logging.error('Error, Creating cliauto_kvstore, err = ' + str(err))
            self.status = 'Error, Creating cliauto_kvstore, err = ' + str(err)


    def service(self):
        return self.service

    def status(self):
        return self.status

    def delete_item(self, path):

        try:
            logging.debug('Started delete_item')
            response = self.service.request(path, method='DELETE')
            body = response.body.read()

            if body == '':
                return 'Success'
            else:
                return 'Else'

        except Exception as err:
            logging.error('Error, delete_item function, err = ' + str(err))
            return 'Error, delete_item function, err = ' + str(err)

    def get_item(self, path):

        try:
            logging.debug('Starting get_item...')
            response = self.service.request(path, method='GET')
            body = response.body.read()

            root = json.loads(body)
            return ['Success', root]

        except Exception as err:
            logging.error('Error, get_item function, err = ' + str(err))
            return ['Error, get_item function, err = ' + str(err), []]

    def get_items(self, path):

        try:
            logging.debug('Starting get_items...')
            response = self.service.request(path, method='GET')
            body = response.body.read()

            root = json.loads(body)
            return ['Success', root]

        except Exception as err:
            logging.error('Error, get_items function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return ['Error, get_items function, err = ' + str(err), []]

    def insert_item(self, path, reqbody):

        try:
            header = [('Content-Type', 'application/json')]
            response = self.service.request(path, method='POST', headers=header, body=reqbody)
            resbody = response.body.read()

            root = json.loads(resbody)
            return ['Success', root]

        except Exception as err:
            logging.error('Error, insert_item function, err = ' + str(err))
            return ['Error, insert_item function, err = ' + str(err), []]

    #fields_list = _key, PID, Status, Timestamp, StartTime, EndTime, CommandType, Command, SessionUser, ScriptUser, TargetUser, NodeList, CustomSumFields
    def create_insert_request_body(self, fargs, sargs, ppid, hostcount, index, source, sourcetype, kv_cmd_string, status, CustomSumFields):
        try:

            epoch_now = str(int(time.time() *1000))
            reqbody = '{ "Status": "' + status + '", "PID": "' + str(ppid) + '", "Timestamp": "' + epoch_now + \
                      '", "StartTime": "' + epoch_now + '", "CommandType": "' + fargs['cmdtype'] + '", "Command": "' + kv_cmd_string + \
                      '", "SessionUser": "' + sargs['user'] + '", "ScriptUser": "' + fargs['suser'] + '", "TargetUser": "' + 'na' + \
                      '", "NodeList": "' + fargs['nodelist'] + '", "HostCount": "' + str(hostcount) + '", "index": "' + index + '", "source": "' + source + \
                      '", "sourcetype": "' + sourcetype + '", "CustomSumFields": "' + CustomSumFields + '" }'
            return ['Success', reqbody]

        except Exception as err:
            logging.error('Error, create_insert_request_body method, err = ' + str(err))
            return ['Error, create_insert_request_body method, err = ' + str(err), '']

    def update_item(self, path, reqbody):

        try:

            header = [('Content-Type', 'application/json')]
            response = self.service.request(path, method='POST', headers=header, body=reqbody)
            resbody = response.body.read()

            root = json.loads(resbody)
            return ['Success', root]

        except Exception as err:
            logging.error('Error, update_item function, err = ' + str(err))
            return ['Error, update_item function, err = ' + str(err), []]

    def create_pid_update_request_body(self, item, ppid, status, setEndTime):
        try:

            epoch_now = str(int(time.time() *1000))

            # All fields of the KVStore item must be included in the http request body or the fields will be updated with no values or empty values
            reqbody = '{ "PID": "' + str(ppid) + '", "Status": "' + status

            try:
                reqbody = reqbody + '", "Timestamp": "' + epoch_now
            except:
                pass
            try:
                reqbody = reqbody + '", "StartTime": "' + str(item['StartTime'])
            except:
                pass
            try:
                if setEndTime:
                    reqbody = reqbody + '", "EndTime": "' + epoch_now
                else:
                    reqbody = reqbody + '", "EndTime": "' + str(item['EndTime'])
            except:
                pass
            try:
                reqbody = reqbody + '", "CommandType": "' + item['CommandType']
            except:
                pass
            try:
                reqbody = reqbody + '", "Command": "' + item['Command']
            except:
                pass
            try:
                reqbody = reqbody + '", "SessionUser": "' + item['SessionUser']
            except:
                pass
            try:
                reqbody = reqbody + '", "ScriptUser": "' + item['ScriptUser']
            except:
                pass
            try:
                reqbody = reqbody + '", "TargetUser": "' + item['TargetUser']
            except:
                pass
            try:
                reqbody = reqbody + '", "NodeList": "' + item['NodeList']
            except:
                pass
            try:
                reqbody = reqbody + '", "HostCount": "' + str(item['HostCount'])
            except:
                pass
            try:
                reqbody = reqbody + '", "index": "' + item['index']
            except:
                pass
            try:
                reqbody = reqbody + '", "source": "' + item['source']
            except:
                pass
            try:
                reqbody = reqbody + '", "sourcetype": "' + item['sourcetype']
            except:
                pass
            try:
                reqbody = reqbody + '", "CustomSumFields": "' + item['CustomSumFields']
            except:
                pass

            reqbody = reqbody + '" }'
            return ['Success', reqbody]

        except Exception as err:
            logging.error('Error, create_pid_update_request_body method, err = ' + str(err))
            return ['Error, create_pid_update_request_body method, err = ' + str(err), '']
