from __future__ import absolute_import
from __future__ import print_function

import os
import re
import sys
import json
import logging
from logging.config import fileConfig
import time
from splunk.persistconn.application import PersistentServerConnectionApplication

# Append directory of this file to the Python path (sys.path) to be able to import cliauto libs
if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Import cliauto endpoint lib
from cliautolib.cliauto_endpoint import endpoint

# For Splunk on MS Windows (possible future use)
if sys.platform == "win32":
    import msvcrt
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

class cliautoHandler(PersistentServerConnectionApplication):

    def __init__(self, command_line, command_arg):
        PersistentServerConnectionApplication.__init__(self)
        pass

    def handle(self, in_string):

        # Create endpoint object and return response
        try:

            logging.info('Starting cliautoHandler.handle method...')
            ppid = os.getpid()

            # Log parent pid
            logging.info('cliautoHandler.handle method: Parent pid:' + str(ppid))

            oep = endpoint(in_string, ppid)
            return oep.response

        except Exception as err:
            logging.error('Error, Create endpoint object and return response; err = ' + str(err))
            return json.dumps({ 'payload': 'Error, Create endpoint object and return response; err = ' + str(err),
                                         'status': 500  # HTTP status code
                                      })
