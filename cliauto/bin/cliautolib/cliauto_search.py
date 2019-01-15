from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import re
import json
import logging
from logging.config import fileConfig
import time
import pdb
from time import sleep

# Example searchlist
# searchlist = {'args': ['| inputlookup cliauto_pid_lookup'], 'kwargs': {}}

# Append directory of this file to the Python path (sys.path) to be able to import cliauto libs
if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Import Splunk SDK libs

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

try:
    from utils import *
except ImportError:
    raise Exception("Add the SDK repository to your PYTHONPATH to run the examples "
                    "(e.g., export PYTHONPATH=~/splunk-sdk-python.")

FLAGS_TOOL = [ "verbose" ]

FLAGS_CREATE = [
    "earliest_time", "latest_time", "now", "time_format",
    "exec_mode", "search_mode", "rt_blocking", "rt_queue_size",
    "rt_maxblocksecs", "rt_indexfilter", "id", "status_buckets",
    "max_count", "max_time", "timeout", "auto_finalize_ec", "enable_lookups",
    "reload_macros", "reduce_freq", "spawn_process", "required_field_list",
    "rf", "auto_cancel", "auto_pause"
]

FLAGS_RESULTS = [
    "offset", "count", "search", "field_list", "f", "output_mode"
]


class cliauto_search(object):

    def __init__(self, service, searchlist, timeout=300):

        # Processing the request
        try:
            self.response = json.dumps({ 'payload': 'Error, Default splunk_search response',
                                         'status': 400  # HTTP status code
                                      })

            logging.info('Creating splunk_search...')

            self.timeout = timeout
            self.search_sync_status = ""
            self.search_parse_status = "Failure"
            self.service = service

            self.searchlist = searchlist
            self.search = self.searchlist['args'][0]

            self.flags = []
            self.flags.extend(FLAGS_TOOL)
            self.flags.extend(FLAGS_CREATE)
            self.flags.extend(FLAGS_RESULTS)

            self.kwargs_create = dslice(self.searchlist['kwargs'], FLAGS_CREATE)
            self.kwargs_results = dslice(self.searchlist['kwargs'], FLAGS_RESULTS)

            #self.results = []

        except Exception as err:
            logging.error('Error, Creating splunk_search; err = ' + str(err))
            self.response = json.dumps({ 'payload': 'Error, Creating splunk_search; err = ' + str(err),
                                         'status': 400  # HTTP status code
                                      })
            return None

        try:
            self.service.parse(self.search, parse_only=True)
            self.search_parse_status = "Success"

        except Exception as err:
            logging.error('Error, Parsing splunk_search; err = ' + str(err))
            self.response = json.dumps({ 'payload': "query '%s' is invalid; err = %s" % (self.search, str(err)),
                                         'status': 400  # HTTP status code
                                      })
            self.search_parse_status = "Failure"
            return None

        return None

    def timeout(self):
        return self.timeout

    def search_parse_status(self):
        return self.search_parse_status

    def response(self):
        return self.response

    def searchlist(self):
        return self.searchlist

    def search(self):
        return self.search

    def flags(self):
        return self.flags

    def kwargs_create(self):
        return self.kwargs_create

    def kwargs_results(self):
        return self.kwargs_results

    def results(self):
        return self.results

    def search_sync_status(self):
        return self.search_sync_status

    def search_sync_stats(self):
        return self.search_sync_status

    def service(self):
        return self.service

    def search_sync(self):

        try:
            self.search_sync_status = "Initial"
            waittime = 0
            job = self.service.jobs.create(self.search, **(self.kwargs_create))

            while True:
                while not job.is_ready():
                    waittime = waittime + 1
                    sleep(.1)
                    if self.timeout < waittime:
                        self.search_sync_status = "Timeout"
                        job.cancel()
                        return ['Timeout', '']

                self.search_sync_stats = {'isDone': job['isDone'],
                                          'doneProgress': job['doneProgress'],
                                          'scanCount': job['scanCount'],
                                          'eventCount': job['eventCount'],
                                          'resultCount': job['resultCount']}
                #progress = float(stats['doneProgress'])*100
                #scanned = int(stats['scanCount'])
                #matched = int(stats['eventCount'])
                #results = int(stats['resultCount'])
                if self.search_sync_stats['isDone'] == '1': 
                    break
                sleep(.1)
                waittime = waittime + 1
                if self.timeout < waittime:
                    self.search_sync_status = "Timeout"
                    job.cancel()
                    return ['Timeout', '']

            if 'count' not in self.kwargs_results: self.kwargs_results['count'] = 0
            self.results = job.results(**(self.kwargs_results))
            job.cancel()
            self.search_sync_status = "Success"

            return ['Success', '']

        except Exception as err:
            self.search_sync_status = "Error"
            logging.error('Error, splunk_search.search_sync method, err = ' + str(err))
            return ['Error', 'Error, splunk_search.search_sync method, err = ' + str(err)]
