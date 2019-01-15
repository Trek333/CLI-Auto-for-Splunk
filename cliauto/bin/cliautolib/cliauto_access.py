from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import re
import json
import logging
from logging.config import fileConfig
import time
from collections import OrderedDict
import xml.dom.minidom

# Append directory of this file to the Python path (sys.path) to be able to import cliauto libs
if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import splunklib.binding as binding

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

class cliauto_access(object):

    def __init__(self, sargs):


        # Processing the request
        try:
            self.status = "Failure"
            logging.info('Creating cliauto_access...')
            self.sargs = sargs
            self.service = binding.connect(token=self.sargs['authtoken'])
            logging.debug('self.service = ' + str(self.service))
            self.status = "Success"

        except Exception as err:
            logging.error('Error, Creating cliauto_access, err = ' + str(err))
            self.status = 'Error, Creating cliauto_access, err = ' + str(err)


    def service(self):
        return self.service

    def sargs(self):
        return self.sargs

    def status(self):
        return self.status

    def get_user_capabilities(self, path):

        try:
            logging.info('Starting get_user_capabilities...')
            capabilities = []
            response = self.service.request(path, method='GET')
            body = response.body.read()
            dom=xml.dom.minidom.parseString(body)
            keys=dom.getElementsByTagName('s:key')
            for key in keys:
                if key.getAttribute('name') == 'capabilities': 
                    capabilitykeys=key.getElementsByTagName('s:item')
                    for capabilitykey in capabilitykeys:
                        capabilities.append(str(capabilitykey.childNodes[0].nodeValue))

            logging.debug('capabilities = ' +str(capabilities))

            return ['Success', capabilities]

        except Exception as err:
            logging.error('Error, get_user_capabilities function, err = ' + str(err))
            return ['Error, get_user_capabilities function, err = ' + str(err), []]
