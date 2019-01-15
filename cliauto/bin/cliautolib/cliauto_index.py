from __future__ import absolute_import
from __future__ import print_function

import os
import re
import sys
import json
import logging
from logging.config import fileConfig
import errno
import time
from datetime import datetime

# Append directory of this file to the Python path (sys.path) to be able to import cliauto libs
if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import splunklib.binding as binding
import splunklib.client as client

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

class cliauto_index(object):

    def __init__(self, service, objcfg):


        # Processing the request
        try:
            self.status = "Failure"
            logging.info('Creating cliauto_index...')

            self.service = service

            # Retrieve the index for the data
            self.myindex = self.service.indexes[objcfg.index]

            self.status = "Success"

        except Exception as err:
            logging.error('Error, Creating cliauto_index, err = ' + str(err))
            self.status = 'Error, Creating cliauto_index, err = ' + str(err)


    def service(self):
        return self.service

    def myindex(self):
        return self.myindex

    def status(self):
        return self.status

    def write_attach(self, ssh_result, source, sourcetype, item, item_cmd_string):

        try:
            logging.debug('Started write_attach')

            # Add timestamp to beginning of event data to match default log file event ingestion transform
            current_time = time.localtime()
            ndata = time.strftime('%Y-%m-%d %H:%M:%S,%03d', current_time)
            ndata = ndata + ' jobid="' + str(item['_key']) + '"'
            ndata = ndata + ' ip_address="' + str(ssh_result['ip_address']) + '"'
            ndata = ndata + ' cmdtype="' + str(item['CommandType']) + '"'
            ndata = ndata + ' command="' + str(item_cmd_string) + '"'
            ndata = ndata + ' iteration="' + str(ssh_result['iteration']) + '"'
            ndata = ndata + ' pid="' + str(item['PID']) + '"'
            ndata = ndata + ' hostcount="' + str(item['HostCount']) + '"'
            ndata = ndata + ' sessionuser="' + str(item['SessionUser']) + '"'
            ndata = ndata + ' scriptuser="' + str(item['ScriptUser']) + '"'
            ndata = ndata + ' nodelist="' + str(item['NodeList']) + '"'
            ndata = ndata + ' starttime="' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(item['StartTime'])/1000)) + '"'
            ndata = ndata + ' endtime="' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(item['EndTime'])/1000)) + '"'
            ndata = ndata + ' result="' + ssh_result['result'] + '"'
            ndata = ndata + ' resultstatus="' + ssh_result['resultstatus'] + '"'

            # Get any custom result fields
            for i,custom_result_field_dict in enumerate(ssh_result['custom_result_field_list']):
                ndata = ndata + ' ' + str(custom_result_field_dict['field_name']) + '="' + str(custom_result_field_dict['value']) + '"'

            ndata = ndata + ' resultraw="' + ssh_result['resultraw'] + '"'

            # Open a socket
            mysocket = self.myindex.attach(host=ssh_result['host'], source=source, sourcetype=sourcetype)

            # Split the data into lines
            lines = ndata.split('\n')

            # Loop through the lines
            for line in lines:
                line = line.strip('\n')
                if line == "":
                    break
                r = mysocket.write(line)

            # Close the socket
            mysocket.close()

            return 'Success'

        except Exception as err:
            logging.error('Error, write_attach function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, write_attach function, err = ' + str(err)

    def write_submit(self, ssh_result, source, sourcetype, item, item_cmd_string):

        try:
            logging.debug('Started write_submit')

            # Add timestamp to beginning of event data to match default log file event ingestion transform
            current_time = time.localtime()
            ndata = time.strftime('%Y-%m-%d %H:%M:%S,%03d', current_time)
            ndata = ndata + ' jobid="' + str(item['_key']) + '"'
            ndata = ndata + ' ip_address="' + str(ssh_result['ip_address']) + '"'
            ndata = ndata + ' cmdtype="' + str(item['CommandType']) + '"'
            ndata = ndata + ' command="' + str(item_cmd_string) + '"'
            ndata = ndata + ' iteration="' + str(ssh_result['iteration']) + '"'
            ndata = ndata + ' pid="' + str(item['PID']) + '"'
            ndata = ndata + ' hostcount="' + str(item['HostCount']) + '"'
            ndata = ndata + ' sessionuser="' + str(item['SessionUser']) + '"'
            ndata = ndata + ' scriptuser="' + str(item['ScriptUser']) + '"'
            ndata = ndata + ' nodelist="' + str(item['NodeList']) + '"'
            ndata = ndata + ' starttime="' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(item['StartTime'])/1000)) + '"'
            ndata = ndata + ' endtime="' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(item['EndTime'])/1000)) + '"'
            ndata = ndata + ' result="' + ssh_result['result'] + '"'
            ndata = ndata + ' resultstatus="' + ssh_result['resultstatus'] + '"'

            # Get any custom result fields
            for custom_result_field_dict in ssh_result['custom_result_field_list']:
                ndata = ndata + ' ' + str(custom_result_field_dict['field_name']) + '="' + str(custom_result_field_dict['value']) + '"'

            # Get any custom fields for duplicate results
            for custom_result_field_dict in ssh_result['custom_result_field_list']:
                logging.debug('custom_result_field_dict = ' + str(custom_result_field_dict))
                try:
                    custom_result_field_dict['duplicate']
                    custom_result_field_dict['duplicate_field_name']
                    logging.debug('custom_result_field_dict[duplicate] = ' + str(custom_result_field_dict['duplicate']))
                    logging.debug('custom_result_field_dict[duplicate_field_name] = ' + str(custom_result_field_dict['duplicate_field_name']))

                except:
                    break

                if str(custom_result_field_dict['duplicate']) != 'na':
                    ndata = ndata + ' duplicate_field_name="' + str(custom_result_field_dict['duplicate_field_name']) + '"'
                    ndata = ndata + ' duplicate="' + str(custom_result_field_dict['duplicate']) + '"'
                    break

            ndata = ndata + ' resultraw="' + ssh_result['resultraw'] + '"'

            # Split the data into lines
            lines = ndata.strip('\n')
            host = str(ssh_result['host'])

            # Submit event to index
            r = self.myindex.submit(lines, source=source, sourcetype=sourcetype, host=host)

            return 'Success'

        except Exception as err:
            logging.error('Error, write_submit function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, write_submit function, err = ' + str(err)
