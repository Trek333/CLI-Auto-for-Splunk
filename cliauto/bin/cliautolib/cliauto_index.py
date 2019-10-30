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
import operator

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

            # Get app's version
            self.cliauto_version = objcfg.cliauto_version

            self.status = "Success"

        except Exception as err:
            logging.error('Error, Creating cliauto_index, err = ' + str(err))
            self.status = 'Error, Creating cliauto_index, err = ' + str(err)


    def service(self):
        return self.service

    def cliauto_version(self):
        return self.cliauto_version

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

            # Get cli command times
            sorted_cmd_times = []
            index = 1
            sorted_cmd_times = sorted(ssh_result['cmd_time_dict'].items(), key=operator.itemgetter(1), reverse=True)
            for cmd_time in sorted_cmd_times:
                ndata = ndata + ' slow' + str(index) + '_cmd="' + str(cmd_time[0]) + '"'
                ndata = ndata + ' slow' + str(index) + '_time="' + '%.3f' % round(cmd_time[1], 3) + '"'
                if index > 2:
                    break
                index += 1

            try:
                ssh_result['login_dict']['login_socket_check_time']
                ssh_result['login_dict']['login_socket_check_count']
                ndata = ndata + ' sock_time="' + '%.3f' % round(ssh_result['login_dict']['login_socket_check_time'], 3) + '"'
                ndata = ndata + ' sock_cnt="' + str(ssh_result['login_dict']['login_socket_check_count']) + '"'
            except:
                ndata = ndata + ' sock_time=""'
                ndata = ndata + ' sock_cnt=""'

            try:
                ssh_result['login_dict']['login_time']
                ssh_result['login_dict']['login_connect_count']
                ndata = ndata + ' login_time="' + '%.3f' % round(ssh_result['login_dict']['login_time'], 3) + '"'
                ndata = ndata + ' login_cnt="' + str(ssh_result['login_dict']['login_connect_count']) + '"'
            except:
                ndata = ndata + ' login_time=""'
                ndata = ndata + ' login_cnt=""'

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
            ndata = ndata + ' cliauto_version="' + str(self.cliauto_version) + '"'
            ndata = ndata + ' jobid="' + str(item['_key']) + '"'
            ndata = ndata + ' hostnum="' + str(ssh_result['record_num']) + '"'
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

            # Get cli command times
            sorted_cmd_times = []
            index = 1
            sorted_cmd_times = sorted(ssh_result['cmd_time_dict'].items(), key=operator.itemgetter(1), reverse=True)
            for cmd_time in sorted_cmd_times:
                ndata = ndata + ' slow' + str(index) + '_cmd="' + str(cmd_time[0]) + '"'
                ndata = ndata + ' slow' + str(index) + '_time="' + '%.3f' % round(cmd_time[1], 3) + '"'
                if index > 2:
                    break
                index += 1

            try:
                ssh_result['login_dict']['login_socket_check_time']
                ssh_result['login_dict']['login_socket_check_count']
                ndata = ndata + ' sock_time="' + '%.3f' % round(ssh_result['login_dict']['login_socket_check_time'], 3) + '"'
                ndata = ndata + ' sock_cnt="' + str(ssh_result['login_dict']['login_socket_check_count']) + '"'
            except:
                ndata = ndata + ' sock_time=""'
                ndata = ndata + ' sock_cnt=""'

            try:
                ssh_result['login_dict']['login_time']
                ssh_result['login_dict']['login_connect_count']
                ndata = ndata + ' login_time="' + '%.3f' % round(ssh_result['login_dict']['login_time'], 3) + '"'
                ndata = ndata + ' login_cnt="' + str(ssh_result['login_dict']['login_connect_count']) + '"'
            except:
                ndata = ndata + ' login_time=""'
                ndata = ndata + ' login_cnt=""'

            host = str(ssh_result['host'])

            if ssh_result['multiple_host_events'] != []:

                # Strip the \n from ndata
                lines = ndata.strip('\n')

                # Try to submit events to index
                try:
                    with self.myindex.attached_socket(source=source, sourcetype=sourcetype, host=host) as sock:
                        for event in ssh_result['multiple_host_events']:
                            cur_line = lines + ' ' + event + '\r\n'

                            # Encode lines from str to bytes object
                            cur_line = cur_line.encode()

                            # Submit event to index
                            sock.send(cur_line)

                # If an exception occurs submitting events to index, submit an error event to index
                # Issues have occurred in the past submitting mulitple events using the attach method which is similar to attached_socket
                except Exception as err:
                    error_string = lines + ' ' + event + str(err)
                    r = self.myindex.submit(error_string, source=source, sourcetype=sourcetype, host=host)

            else:

                ndata = ndata + ' resultraw="' + ssh_result['resultraw'] + '"'

                # Strip the \n from ndata
                lines = ndata.strip('\n')

                # Encode lines from str to bytes object
                lines = lines.encode()

                # Submit event to index
                r = self.myindex.submit(lines, source=source, sourcetype=sourcetype, host=host)

            return 'Success'

        except Exception as err:
            logging.error('Error, write_submit function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, write_submit function, err = ' + str(err)
