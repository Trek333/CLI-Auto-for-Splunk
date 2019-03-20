from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import re
import json
import logging
from logging.config import fileConfig
import time
from threading import Thread
import threading
from datetime import datetime
from collections import OrderedDict
import select
import socket
from contextlib import closing
from operator import itemgetter
import requests
import splunk
import copy

# Append directory of this file to the Python path (sys.path) to be able to import cliauto libs
if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

#from cliauto_configfile import ConfigFile
from cliauto_helpers import helpers
from cliauto_index import cliauto_index
import splunklib.client as client

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

logging.debug("importing pexpect...")
try:
    #from pexpect import pxssh
    import pexpect
    from pxssh_cliauto import pxssh_cliauto
    from pxssh_cliauto import ExceptionPxssh
    from pxssh_cliauto import ExceptionPxsshAccessDenied
    from pxssh_cliauto import ExceptionPxsshLoginTimeout
    from pxssh_cliauto import ExceptionPxsshHostKeyChanged
    from pxssh_cliauto import ExceptionPxsshMaxHostsExceeded
    from pxssh_cliauto import ExceptionPxsshNoCipherFound

except Exception:
    logging.debug("Build and copy the pexpect and ptyprocess package libraries to the bin folder of the cliauto app")
logging.debug("imported pexpect")


class sshcom(object):

    def __init__(self, fargs, sargs, cargs, ppid, sk, binding_service, client_service, objcfg):

        try:

            self.status = "Failure"
            self.response = json.dumps({ 'payload': 'Error, Default sshcom response',
                                         'status': 400  # HTTP status code
                                      })
            logging.info('Creating sshcom...')
            self.lock = threading.Lock()
            self.fargs = fargs
            self.sargs = sargs
            self.cargs = cargs
            self.ppid = ppid
            self.sk = sk
            self.binding_service = binding_service
            self.client_service = client_service
            self.objcfg = objcfg

            self.parallel_ssh_results = {}
            self.cur_parallel_ssh_results = {}

            self.custom_result_field_list = []
            self.CustomSumFields = []
            for cmdtype_dict in self.objcfg.cmdtype_dict_list:
                if self.fargs['cmdtype'].lower() == cmdtype_dict['cmdtype'].lower():

                    # Check if cmdtype contains Skip regexes and set CustomSumFields list
                    skip_regex1 = ''
                    skip_regex2 = ''
                    skip_regex3 = ''
                    skip_regex4 = ''
                    skip_regex5 = ''
                    try:
                        skip_regex1 = cmdtype_dict['skip_regex1']
                    except:
                        pass

                    try:
                        skip_regex2 = cmdtype_dict['skip_regex2']
                    except:
                        pass

                    try:
                        skip_regex3 = cmdtype_dict['skip_regex3']
                    except:
                        pass

                    try:
                        skip_regex4 = cmdtype_dict['skip_regex4']
                    except:
                        pass

                    try:
                        skip_regex5 = cmdtype_dict['skip_regex5']
                    except:
                        pass

                    if skip_regex1 != '' or skip_regex2 != '' or skip_regex3 != '' or skip_regex4 != '' or skip_regex5 != '':
                        self.CustomSumFields.append({'name' : 'Skip', 'count' : 0})

                    # Get list of custom summary fields
                    self.CustomSumFieldsList = []
                    for CustomSumField in self.CustomSumFields:
                        self.CustomSumFieldsList.append(CustomSumField['name'])

                    # Check if cmdtype has Custom summary fields and initialize them
                    self.custom_result_field_list = cmdtype_dict['custom_result_field_list']
                    for i,custom_result_field_dict in enumerate(self.custom_result_field_list):
                        self.custom_result_field_list[i]['value'] = ''
                    logging.debug('self.custom_result_field_list = ' + str(self.custom_result_field_list))

                    break

            self.status = "Success"

        except Exception as err:
            self.status = "Failure"
            logging.error('Error, init sshcom, err = ' + str(err))
            self.response = json.dumps({ 'payload': 'Error, init sshcom, err = ' + str(err),
                                         'status': 400  # HTTP status code
                                      })

    def lock(self):
        return self.lock

    def status(self):
        return self.status

    def response(self):
        return self.response

    def objcfg(self):
        return self.objcfg

    def custom_result_field_list(self):
        return self.custom_result_field_list

    def fargs(self):
        return self.fargs

    def sargs(self):
        return self.sargs

    def cargs(self):
        return self.cargs

    def ppid(self):
        return self.ppid

    def sk(self):
        return self.sk

    def binding_service(self):
        return self.binding_service

    def client_service(self):
        return self.client_service

    def parallel_ssh_results(self):
        return self.parallel_ssh_results

    def cur_parallel_ssh_results(self):
        return self.cur_parallel_ssh_results

    def CustomSumFields(self):
        return self.CustomSumFields

    def CustomSumFieldsList(self):
        return self.CustomSumFieldsList

    def process_cmd(self):

        try:

            # Set KVStore command string
            kv_cmd_string = 'Unknown Defined Command'
            for cmdtype_dict in self.objcfg.cmdtype_dict_list:
                if self.fargs['cmdtype'].lower() == cmdtype_dict['cmdtype'].lower():
                    kv_cmd_string = cmdtype_dict['kv_cmd_string']
                    break

            # Create request body to insert item into KVStore for the requested cmd
            cpirb = self.sk.create_insert_request_body(self.fargs, self.sargs, self.ppid, self.objcfg.hostcount, self.objcfg.index, self.objcfg.source, self.objcfg.sourcetype, kv_cmd_string, 'Busy - 0%', ",".join(self.CustomSumFieldsList))
            if cpirb[0] != 'Success':
                logging.error('process_cmd, self.sk.create_insert_request_body functions, ' + cpirb[0])
                return 'Error, process_cmd, self.sk.create_insert_request_body functions, ' + cpirb[0]

            # Insert item into the KVStore for the new requested cmd
            ii = self.sk.insert_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection", cpirb[1])
            if ii[0] != 'Success':
                logging.error('process_cmd, self.sk.ii functions, ' + ii[0])
                return 'Error, process_cmd, self.sk.ii functions, ' + ii[0]
            key = ii[1]

            # Get item from the KVStore for the new requested cmd
            gi = self.sk.get_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + key['_key'])
            if gi[0] != 'Success':
                logging.error('process_cmd, self.sk.gi functions, ' + gi[0])
                return 'Error, process_cmd, self.sk.gi functions, ' + gi[0]
            item = gi[1]

            # Create/start thread to process iterations of the requested cmd
            t = Thread(target=self.process_iterations, args=([key, item]))
            t.start()

            return 'Success'

        except Exception as err:
            logging.error('Error, process_cmd function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, process_cmd function, err = ' + str(err)

    def send_hb(self, hb_method, verify_cert=False):
        try:

            logging.debug('Entered send_hb...')
            #logging.debug('self.binding_service.authority = ' + str(self.binding_service.authority))

            #isWebSSL = splunk.getWebConfKeyValue("enableSplunkWebSSL").lower() == "true"
            #logging.debug('isWebSSL = ' + str(isWebSSL))
            #webPrefix = isWebSSL and "https://" or "http://"
            #logging.debug('webPrefix = ' + str(webPrefix))

            #hb_db_ulr = str(splunk.getWebServerInfo()) + '/en-US/app/cliauto/hb'
            #logging.debug('hb_db_ulr = ' + hb_db_ulr)

            header = [('Content-Type', 'application/x-www-form-urlencoded')]

            # Select method of HB call
            if hb_method == 'web':
                # TODO - the intent here is find a workaround for the session user timeout limitation
                # TODO - Splunk variable needed for url path of Splunk web to allow relative path
                # The certificate is not verified since the app should be able to trust itself
                response = requests.post('https://127.0.0.1/en-US/splunkd/__raw/services/cliauto', headers=self.cargs, data={'cmdtype' : 'HB'}, verify=verify_cert)
                #response_web = requests.post('https://127.0.0.1/en-US/app/cliauto/hb', headers=self.cargs, verify=verify_cert)
            else:
                # Using the management port to send HB does not reset the Splunk session timeout
                # So if a job is longer the Splunk session timeout, Splunk will kill the Python process executing the job
                # See Settings->General Settings->Session timeout in Splunk UI (default is 1 hour)
                response = self.binding_service.request('/services/cliauto', method='POST', headers=header, body='cmdtype=HB')
                #response_web = requests.post('https://127.0.0.1/en-US/app/cliauto/hb', headers=self.cargs, verify=verify_cert)

            #logging.debug('response_web = ' + str(response_web))
            return response

        except Exception as err:
            logging.error('Error, send_hb function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, send_hb function, err = ' + str(err)

    def hb_and_wait_for_iteration_result(self, lst, key, item, icount):

        try:
            response = self.send_hb('management')
            start_time = time.time()
            hb_iteration_secs = 0
            previous_progress = 0.0
            progress = '0.00 % - i: 0/0'

            epoch_now = time.time()
            hb_epoch_previous = epoch_now
            iteration_epoch_previous = epoch_now
            hb_cur_secs = abs(epoch_now - hb_epoch_previous)
            iteration_cur_secs = abs(epoch_now - iteration_epoch_previous)

            num_cur_results = len(self.cur_parallel_ssh_results.keys())
            num_cur_records = len(lst)
            while num_cur_results < num_cur_records:

                num_cur_results = len(self.cur_parallel_ssh_results.keys())
                num_results = len(self.parallel_ssh_results.keys())
                num_records = len(self.objcfg.hosts)
                progress = str(round((float(num_results) / float(num_records)) * 100, 2)) + '% - i:' + str(icount) + ' ' + str(num_cur_results) + '/' + str(num_cur_records)

                # Get HB and iteration elasped time
                epoch_now = time.time()
                hb_cur_secs = abs(epoch_now - hb_epoch_previous)
                iteration_cur_secs = abs(epoch_now - iteration_epoch_previous)


                # If HB timeout
                # Check for hang condition and update the KVStore with the progress
                # Send a cmdtype=HB to the endpoint
                if hb_cur_secs > self.objcfg.HBTimeout:

                    hb_cur_secs = 0
                    hb_epoch_previous = epoch_now
                    logging.debug("HB timeout; self.objcfg.HBTimeout = " + str(self.objcfg.HBTimeout))

                    # If the progress has not changed, check if IterationTimeout exists then ssh hang condition must exist so return
                    # Else update the KVStore with the progress
                    if previous_progress == progress:
                        if iteration_cur_secs > self.objcfg.IterationTimeout:
                            logging.error('Hang condition detected; exit while loop & hb_and_wait_for_iteration_result')
                            logging.error('iteration_cur_secs = ' + str(iteration_cur_secs) + '; IterationTimeout = ' + str(self.objcfg.IterationTimeout))
                            return True
                    else:
                        logging.debug('iteration_cur_secs = ' + str(iteration_cur_secs))
                        previous_progress = progress

                        cpurb = self.sk.create_pid_update_request_body(item, str(item['PID']), 'Busy - ' + progress, False)
                        if cpurb[0] == 'Success':
                            ui = self.sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + key['_key'],cpurb[1])
                            if ui[0] != 'Success': logging.error(str(ui[0]))
                        else: logging.error(str(cpurb[0]))

                    response = self.send_hb('management')

                # Sleep for HB tick (0.1 seconds)
                time.sleep(0.1)

            # Update the KVstore before exiting
            cpurb = self.sk.create_pid_update_request_body(item, str(item['PID']), 'Busy - ' + progress, False)
            if cpurb[0] == 'Success':
                ui = self.sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + key['_key'],cpurb[1])
                if ui[0] != 'Success': logging.error(str(ui[0]))
            else: logging.error(str(cpurb[0]))

            logging.debug("Exiting hb_and_wait_for_iteration_result...")
            return False
        except Exception as err:
            logging.error("Error, hb_and_wait_for_iteration_result, err = " + str(err))
            return True

    def process_iterations(self, key, item):

        # Use a thread to run a ssh command on hosts.
        # Returns a dict of {hostname:result} for each host.

        try:

            icount = 1

            # If nhosts is not None, more than one iteration is required, use nhosts (array of lists)
            if self.objcfg.nhosts != None:
                for lst in self.objcfg.nhosts:
                    rps = self.parallel_ssh(lst, icount)
                    if not rps:
                        raise Exception('error in parallel_ssh function')
                    icount = icount + 1
                    hbr = self.hb_and_wait_for_iteration_result(lst, key, item, icount - 1)
                    if hbr:
                        raise Exception('error in hb_and_wait_for_iteration_result function')

            # Only one iteration is needed use hosts list
            else:
                rps = self.parallel_ssh(self.objcfg.hosts, icount)
                if not rps:
                    raise Exception('error in parallel_ssh function')

                hbr = self.hb_and_wait_for_iteration_result(self.objcfg.hosts, key, item, 1)
                if hbr:
                    raise Exception('error in hb_and_wait_for_iteration_result function')

            # Update the KVStore item for the completed cmd with Status=Busy - 100% and EndTime
            cpurb = self.sk.create_pid_update_request_body(item, str(item['PID']), 'Busy - 99% - writing results 0/0', True)
            if cpurb[0] == 'Success':
                ui = self.sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + key['_key'],cpurb[1])
                if ui[0] != 'Success': logging.error(str(ui[0]))
            else: logging.error(str(cpurb[0]))

            # Get item from the KVStore for the updated cmd
            gi = self.sk.get_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + key['_key'])
            if gi[0] != 'Success':
                raise Exception('error in sk.get_item function')
            item = gi[1]

            # Update Command with Success and Fail count
            item_cmd_string = str(item['Command'])
            if item['CommandType'].lower() != "cli_custom":
                crs = self.count_result_status()
                if crs[0] != 'Success': logging.error(str(crs[0]))
                item['Command'] = item['Command'] + crs[1]

                # Update Command with Duplicate count
                cd = self.count_duplicates()
                if cd[0] != 'Success': logging.error(str(cd[0]))
                item['Command'] = item['Command'] + cd[1]

            # Create Splunk index object
            ci = cliauto_index(self.client_service, self.objcfg)
            if ci.status != "Success":
                raise Exception('error in cliauto_index constructor function')

            # Write results to Splunk index and send cmdtype = HB to REST API on HB timeout after write to Splunk index
            header = [('Content-Type', 'application/x-www-form-urlencoded')]
            epoch_now = time.time()
            epoch_previous = epoch_now
            hb_cur_secs = abs(epoch_now - epoch_previous)
            record_count = 0
            num_records = len(self.parallel_ssh_results.keys())
            for record_num in self.parallel_ssh_results:

                record_count += 1

                # Write result
                #cw = ci.write_attach(self.parallel_ssh_results[record_num], self.objcfg.source, self.objcfg.sourcetype, item, item_cmd_string)
                cw = ci.write_submit(self.parallel_ssh_results[record_num], self.objcfg.source, self.objcfg.sourcetype, item, item_cmd_string)
                if cw != "Success":
                    raise Exception('error, Unable to write results to index, record_num = ' + str(record_num))

                # Get HB elasped time
                epoch_now = time.time()
                hb_cur_secs = abs(epoch_now - epoch_previous)

                # If HB timeout, send a cmdtype=HB to the endpoint
                if hb_cur_secs > self.objcfg.HBTimeout:
                    logging.debug("HB timeout; self.objcfg.HBTimeout = " + str(self.objcfg.HBTimeout))
                    hb_cur_secs = 0
                    epoch_previous = epoch_now
                    response = self.send_hb('management')

                    # Update the KVStore item for the completed cmd with Status=Busy - 100% and EndTime
                    cpurb = self.sk.create_pid_update_request_body(item, str(item['PID']), 'Busy - 99% - writing results ' + str(record_count) + '/' + str(num_records), True)
                    if cpurb[0] == 'Success':
                        ui = self.sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + key['_key'],cpurb[1])
                        if ui[0] != 'Success': logging.error(str(ui[0]))
                    else: logging.error(str(cpurb[0]))

                # Bandaid for Splunk Python SDK to index data - getting HTTP 503 error for 1000 nodes in node list for the write_attach function
                # It appears that too many writes too fast causes the "503 Too many HTTP threads (303) already running, try again later" error
                # For write_submit function, .1 second delay after each execution is not needed to prevent HTTP 503 error - 11/1/2018
                #time.sleep(.1)

            # Update the KVStore item for the completed cmd with Status=Done
            cpurb = self.sk.create_pid_update_request_body(item, str(item['PID']), 'Done', False)
            if cpurb[0] == 'Success':
                ui = self.sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + key['_key'],cpurb[1])
                if ui[0] != 'Success': logging.error(str(ui[0]))
            else: logging.error(str(cpurb[0]))

            logging.info("Exiting process_iterations")
            return False

        except Exception as err:
            logging.error('Error, process_iterations, icount = ' + str(icount) + ': err = ' + str(err))
            # Update the KVStore item for the completed cmd with Status=Done

            cpurb = self.sk.create_pid_update_request_body(item, str(item['PID']), 'Done - Error', True)
            if cpurb[0] == 'Success':
                ui = self.sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + key['_key'],cpurb[1])
                if ui[0] != 'Success': logging.error(str(ui[0]))
            else: logging.error(str(cpurb[0]))
            return False

    def count_duplicates(self):

        try:  

            dcount = 0
            field_name = ''
            value_list = []

            # If exists...get field_name for duplicate check
            for record_num in self.parallel_ssh_results:
                for custom_result_field_dict in self.parallel_ssh_results[record_num]['custom_result_field_list']:
                    if custom_result_field_dict['duplicate_check'] == '1':
                        field_name = str(custom_result_field_dict['field_name'])
                        break
                break

            # If a custom field with duplicate check found then get duplicate count
            if field_name != '':

                # Get list of all values for the custom field
                for record_num in self.parallel_ssh_results:
                    value = ''
                    for custom_result_field_dict in self.parallel_ssh_results[record_num]['custom_result_field_list']:
                        if str(custom_result_field_dict['field_name']) == field_name:
                            value = str(custom_result_field_dict['value'])
                            break
                    value_list.append(value)
                        
                # Get list of duplicate values for the custom field
                dup_list = self.list_duplicates(value_list)

                # Update the custom field with duplicate and empty check results
                dcount = 0
                ecount = 0
                for record_num in self.parallel_ssh_results:
                    value = ''
                    for i,custom_result_field_dict in enumerate(self.parallel_ssh_results[record_num]['custom_result_field_list']):
                        if custom_result_field_dict['field_name'] == field_name:
                            self.parallel_ssh_results[record_num]['custom_result_field_list'][i]['duplicate_field_name'] = field_name
                            if custom_result_field_dict['value'].strip() == '':
                                self.parallel_ssh_results[record_num]['custom_result_field_list'][i]['duplicate'] = 'empty'
                                ecount = ecount + 1
                            elif custom_result_field_dict['value'] in dup_list:
                                self.parallel_ssh_results[record_num]['custom_result_field_list'][i]['duplicate'] = 'yes'
                                dcount = dcount + 1
                            else:
                                self.parallel_ssh_results[record_num]['custom_result_field_list'][i]['duplicate'] = 'no'
                        else:
                            self.parallel_ssh_results[record_num]['custom_result_field_list'][i]['duplicate_field_name'] = 'na'
                            self.parallel_ssh_results[record_num]['custom_result_field_list'][i]['duplicate'] = 'na'

                return ['Success', '<br>' + field_name + ': Dups=' + str(dcount) + ', Empty=' + str(ecount)]

            else:
                return ['Success', '']

        except Exception as err:
            logging.error('Error, count_duplicates, err = ' + str(err))
            return ['Error', '<br>Success=err, Fail=err']

    def list_duplicates(self, seq):
        seen = set()
        seen_add = seen.add
        # adds all elements it doesn't know yet to seen and all other to seen_twice
        seen_twice = set( x for x in seq if x in seen or seen_add(x) )
        # turn the set into a list (as requested)
        return list( seen_twice )

    def count_result_status(self):

        try:  

            scount = 0
            fcount = 0

            # Get the counts
            for record_num in self.parallel_ssh_results:
                if self.parallel_ssh_results[record_num]['resultstatus'] == 'Success':
                    scount = scount + 1
                elif self.parallel_ssh_results[record_num]['resultstatus'] in self.CustomSumFieldsList:
                    for i,CustomSumField in enumerate(self.CustomSumFields):
                        if self.parallel_ssh_results[record_num]['resultstatus'] == CustomSumField['name']:
                            self.CustomSumFields[i]['count'] = self.CustomSumFields[i]['count'] + 1
                            break
                else:
                    fcount = fcount + 1

            # Set the command field string
            command_string = '<br>Success=' + str(scount)
            for CustomSumField in self.CustomSumFields:
                command_string = command_string + ', ' + CustomSumField['name'] + '=' + str(CustomSumField['count'])
            command_string = command_string + ', Fail=' + str(fcount)

            return ['Success', command_string]

        except Exception as err:
            logging.error('Error, count_result_status, err = ' + str(err))
            return ['Error', '<br>Success=err, Fail=err']

    def parallel_ssh(self, host_list, icount):

        try:  
            # Use threads to run a ssh command(s) on hosts.
            # Returns a dict of {hostname:result} for each host.

            self.cur_parallel_ssh_results = {}
            logging.info("running " + self.fargs['cmdtype'] + " on " + str(len(host_list)) + " hosts")
            for host_dict in host_list:
                t = Thread(target=self.ssh_pexpect, args=([host_dict, icount]))
                t.start()
            return True
            
        except Exception as err:
            logging.error('Error, parallel_ssh, icount = ' + str(icount) + ': err = ' + str(err))
            return False

    def ssh_update_result(self, host_dict, result, resultraw, iteration, resultstatus, custom_result_field_list):

        try:
            with self.lock:
                logging.debug('custom_result_field_list = ' + str(custom_result_field_list))
                record_num = host_dict['record_num']

                cur_parallel_ssh_results = {}
                cur_parallel_ssh_results[record_num] = host_dict
                cur_parallel_ssh_results[record_num]['result'] = result
                cur_parallel_ssh_results[record_num]['resultraw'] = resultraw
                cur_parallel_ssh_results[record_num]['iteration'] = iteration
                cur_parallel_ssh_results[record_num]['resultstatus'] = resultstatus
                cur_parallel_ssh_results[record_num]['custom_result_field_list'] = custom_result_field_list

                parallel_ssh_results = {}
                parallel_ssh_results[record_num] = host_dict
                parallel_ssh_results[record_num]['result'] = result
                parallel_ssh_results[record_num]['resultraw'] = resultraw
                parallel_ssh_results[record_num]['iteration'] = iteration
                parallel_ssh_results[record_num]['resultstatus'] = resultstatus
                parallel_ssh_results[record_num]['custom_result_field_list'] = custom_result_field_list

                self.cur_parallel_ssh_results[record_num] = cur_parallel_ssh_results[record_num]
                self.parallel_ssh_results[record_num] = parallel_ssh_results[record_num]

            return True
        except Exception as err:
            logging.error('Error, ssh_update_result, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return False


    def add_user_input(self, cmd):

        cmd = cmd.replace("@var1@", self.fargs['var1'])
        cmd = cmd.replace("@var2@", self.fargs['var2'])
        cmd = cmd.replace("@var3@", self.fargs['var3'])
        cmd = cmd.replace("@var4@", self.fargs['var4'])
        cmd = cmd.replace("@pw1@", self.fargs['pw1'])
        cmd = cmd.replace("@pw2@", self.fargs['pw2'])
        cmd = cmd.replace("@pw3@", self.fargs['pw3'])
        cmd = cmd.replace("@drop1@", self.fargs['drop1'])
        return cmd

    def eradicate_string(self, raw_string):

        try:  
            regexd_list = []

            # PW variables
            if self.fargs['pw1'] != '':
                regexd_list.append({"pattern" : re.compile(re.escape(self.fargs['pw1'])), "estring" : "****", "length" : len(self.fargs['pw1'])})
            if self.fargs['pw2'] != '':
                regexd_list.append({"pattern" : re.compile(re.escape(self.fargs['pw2'])), "estring" : "****", 'length' : len(self.fargs['pw2'])})
            if self.fargs['pw3'] != '':
                regexd_list.append({"pattern" : re.compile(re.escape(self.fargs['pw3'])), "estring" : "****", 'length' : len(self.fargs['pw3'])})

            # Sort (descending) list of dictionaries by the string length of each pw variable
            # re.sub command (regex search & replace) needs to executed on the raw_string with each pw variable in descending order of the corresponding pw variable length
            # If not, partial eradication may occur if a pw variable contains another pw variable in it.
            regexd_list_sorted = sorted(regexd_list, key=itemgetter('length'), reverse=True)


            # Loop through the sorted list
            for regexd in regexd_list_sorted:
                raw_string = regexd['pattern'].sub(regexd['estring'], raw_string)

            return raw_string

        except Exception as err:
            logging.error('Error, eradicate_string function, err = ' + str(err) + ', Due to error to eradicate the command(s) result, the entire result was eradicated due to security concerns.')
            return 'Due to error to eradicate the command(s) result, the entire result was eradicated due to security concerns, err = ' + str(err)

    def process_result(self, resultraw):

        try:  

            logging.info("Entering process_result...")
            resultstatus = 'na'
            result = 'na'

            # If Custom cmd then do not process result
            if self.fargs['cmdtype'].lower() == 'cli_custom':
                return ['Success', 'custom', 'custom']

            # Loop through the cmdtype_dict_list to find it then process it
            for cmdtype_dict in self.objcfg.cmdtype_dict_list:

                if self.fargs['cmdtype'].lower() == cmdtype_dict['cmdtype'].lower():

                    logging.info("cmdtype_dict = " + str(cmdtype_dict))
                    resultstatus = 'Fail'
                    result = 'default fail msg - update cliauto_cmds.conf'
                    result_list_f1 = []
                    result_list_f2 = []
                    result_list_f3 = []
                    result_list_f4 = []
                    result_list_f5 = []
                    default_fail_msg = ''
                    find_regex1 = ''
                    success_regex1 = ''
                    success_msg1 = ''
                    find_regex2 = ''
                    success_regex2 = ''
                    success_msg2 = ''
                    find_regex3 = ''
                    success_regex3 = ''
                    success_msg3 = ''
                    find_regex4 = ''
                    success_regex4 = ''
                    success_msg4 = ''
                    find_regex5 = ''
                    success_regex5 = ''
                    success_msg5 = ''
                    fail_regex1 = ''
                    fail_msg1 = ''
                    fail_regex2 = ''
                    fail_msg2 = ''
                    fail_regex3 = ''
                    fail_msg3 = ''
                    fail_regex4 = ''
                    fail_msg4 = ''
                    fail_regex5 = ''
                    fail_msg5 = ''
                    skip_regex1 = ''
                    skip_msg1 = ''
                    skip_regex2 = ''
                    skip_msg2 = ''
                    skip_regex3 = ''
                    skip_msg3 = ''
                    skip_regex4 = ''
                    skip_msg4 = ''
                    skip_regex5 = ''
                    skip_msg5 = ''

                    # Attempt to get variables from conf file
                    try:
                        default_fail_msg = cmdtype_dict['default_fail_msg']
                    except:
                        pass

                    try:
                        find_regex1 = cmdtype_dict['find_regex1']
                        success_regex1 = cmdtype_dict['success_regex1']
                        success_msg1 = cmdtype_dict['success_msg1']
                    except:
                        pass

                    try:
                        find_regex2 = cmdtype_dict['find_regex2']
                        success_regex2 = cmdtype_dict['success_regex2']
                        success_msg2 = cmdtype_dict['success_msg2']
                    except:
                        pass

                    try:
                        find_regex3 = cmdtype_dict['find_regex3']
                        success_regex3 = cmdtype_dict['success_regex3']
                        success_msg3 = cmdtype_dict['success_msg3']
                    except:
                        pass

                    try:
                        find_regex4 = cmdtype_dict['find_regex4']
                        success_regex4 = cmdtype_dict['success_regex4']
                        success_msg4 = cmdtype_dict['success_msg4']
                    except:
                        pass

                    try:
                        find_regex5 = cmdtype_dict['find_regex5']
                        success_regex5 = cmdtype_dict['success_regex5']
                        success_msg5 = cmdtype_dict['success_msg5']
                    except:
                        pass

                    try:
                        skip_regex1 = cmdtype_dict['skip_regex1']
                        skip_msg1 = cmdtype_dict['skip_msg1']
                    except:
                        pass

                    try:
                        skip_regex2 = cmdtype_dict['skip_regex2']
                        skip_msg2 = cmdtype_dict['skip_msg2']
                    except:
                        pass

                    try:
                        skip_regex3 = cmdtype_dict['skip_regex3']
                        skip_msg3 = cmdtype_dict['skip_msg3']
                    except:
                        pass

                    try:
                        skip_regex4 = cmdtype_dict['skip_regex4']
                        skip_msg4 = cmdtype_dict['skip_msg4']
                    except:
                        pass

                    try:
                        skip_regex5 = cmdtype_dict['skip_regex5']
                        skip_msg5 = cmdtype_dict['skip_msg5']
                    except:
                        pass

                    try:
                        fail_regex1 = cmdtype_dict['fail_regex1']
                        fail_msg1 = cmdtype_dict['fail_msg1']
                    except:
                        pass

                    try:
                        fail_regex2 = cmdtype_dict['fail_regex2']
                        fail_msg2 = cmdtype_dict['fail_msg2']
                    except:
                        pass

                    try:
                        fail_regex3 = cmdtype_dict['fail_regex3']
                        fail_msg3 = cmdtype_dict['fail_msg3']
                    except:
                        pass

                    try:
                        fail_regex4 = cmdtype_dict['fail_regex4']
                        fail_msg4 = cmdtype_dict['fail_msg4']
                    except:
                        pass

                    try:
                        fail_regex5 = cmdtype_dict['fail_regex5']
                        fail_msg5 = cmdtype_dict['fail_msg5']
                    except:
                        pass

                    # Set default fail msg from conf file
                    result = default_fail_msg

                    # Get find regex lists
                    if find_regex1 != '':
                        logging.debug('find_regex1 variable exists; processing it')
                        result_list_f1 = re.findall(find_regex1, resultraw)
                    if find_regex2 != '':
                        logging.debug('find_regex2 variable exists; processing it')
                        result_list_f2 = re.findall(find_regex2, resultraw)
                    if find_regex3 != '':
                        logging.debug('find_regex3 variable exists; processing it')
                        result_list_f3 = re.findall(find_regex3, resultraw)
                    if find_regex4 != '':
                        logging.debug('find_regex4 variable exists; processing it')
                        result_list_f4 = re.findall(find_regex4, resultraw)
                    if find_regex5 != '':
                        logging.debug('find_regex5 variable exists; processing it')
                        result_list_f5 = re.findall(find_regex5, resultraw)

                    # If the find results and success regexes are not empty then check success regexes
                    if result_list_f1 != [] and success_regex1 != '' and re.search(success_regex1, result_list_f1[0]):
                        logging.debug('success_regex1 found; success')
                        resultstatus = 'Success'
                        result = success_msg1
                    elif result_list_f2 != [] and success_regex2 != '' and re.search(success_regex2, result_list_f2[0]):
                        logging.debug('success_regex2 found; success')
                        resultstatus = 'Success'
                        result = success_msg2
                    elif result_list_f3 != [] and success_regex3 != '' and re.search(success_regex3, result_list_f3[0]):
                        logging.debug('success_regex3 found; success')
                        resultstatus = 'Success'
                        result = success_msg3
                    elif result_list_f4 != [] and success_regex4 != '' and re.search(success_regex4, result_list_f4[0]):
                        logging.debug('success_regex4 found; success')
                        resultstatus = 'Success'
                        result = success_msg4
                    elif result_list_f5 != [] and success_regex5 != '' and re.search(success_regex5, result_list_f5[0]):
                        logging.debug('success_regex5 found; success')
                        resultstatus = 'Success'
                        result = success_msg5

                    # If skip regex exists and no success found then check for known skip reason and set result
                    if skip_regex1 != '' or skip_regex2 != '' or skip_regex3 != '' or skip_regex4 != '' or skip_regex5 != '':

                        if skip_regex1 != '' and resultstatus == 'Fail' and re.search(skip_regex1 , resultraw):
                            resultstatus = 'Skip'
                            result = skip_msg1
                        elif skip_regex2 != '' and resultstatus == 'Fail' and re.search(skip_regex2 , resultraw):
                            resultstatus = 'Skip'
                            result = skip_msg2
                        elif skip_regex3 != '' and resultstatus == 'Fail' and re.search(skip_regex3 , resultraw):
                            resultstatus = 'Skip'
                            result = skip_msg3
                        elif skip_regex4 != '' and resultstatus == 'Fail' and re.search(skip_regex4 , resultraw):
                            resultstatus = 'Skip'
                            result = skip_msg4
                        elif skip_regex5 != '' and resultstatus == 'Fail' and re.search(skip_regex5 , resultraw):
                            resultstatus = 'Skip'
                            result = skip_msg5

                    # If fail regex exists and no success or skip found then check for known fail reason and set result
                    if fail_regex1 != '' and resultstatus == 'Fail' and re.search(fail_regex1 , resultraw):
                        result = fail_msg1
                    elif fail_regex2 != '' and resultstatus == 'Fail' and re.search(fail_regex2 , resultraw):
                        result = fail_msg2
                    elif fail_regex3 != '' and resultstatus == 'Fail' and re.search(fail_regex3 , resultraw):
                        result = fail_msg3
                    elif fail_regex4 != '' and resultstatus == 'Fail' and re.search(fail_regex4 , resultraw):
                        result = fail_msg4
                    elif fail_regex5 != '' and resultstatus == 'Fail' and re.search(fail_regex5 , resultraw):
                        result = fail_msg5
                    break

            return ['Success', resultstatus, result]

        except Exception as err:

            logging.error('Error, process_result function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return ['Fail', 'Fail', 'err = ' + str(err)]

    def process_ssh_cmd(self, cmd_out, cmd_dict, host_dict, icount):

        try:  

            logging.debug("Entering process_ssh_cmd...")

            # The default result is Fail
            result = 'Fail'

            # Search for success regex
            cmd_success_regex_list = cmd_dict['cmd_success_regex_list']
            for cmd_success_regex in cmd_success_regex_list:

                logging.debug("cmd_success_regex = " + cmd_success_regex)
                logging.debug("cmd_out = " + cmd_out)
                if re.search(cmd_success_regex , cmd_out):
                    result = 'Success'
                    break

            # Search for fail regex after searching for success regex
            # In other words, a found fail regex will override a found success regex
            cmd_fail_regex_list = cmd_dict['cmd_fail_regex_list']
            for cmd_fail_regex in cmd_fail_regex_list:

                logging.debug("cmd_fail_regex = " + cmd_fail_regex)
                logging.debug("cmd_out = " + cmd_out)
                if re.search(cmd_fail_regex , cmd_out):
                    result = 'Fail'
                    break

            logging.debug("Exiting process_ssh_cmd...result = " + result)
            return ['Success', result]

        except Exception as err:

            logging.error('Error, process_ssh_cmd function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            sptr = self.ssh_update_result(host_dict,  "Error, process_ssh_cmd, err = " + str(err), "Error, process_ssh_cmd, err = " + str(err), \
                str(icount), 'Fail', self.custom_result_field_list)
            return ['Fail', 'Fail']

    def ssh_pexpect(self, host_dict, icount):

        try:
            logging.debug("Starting ssh_pexpect...")

            record_num = host_dict['record_num']

            # Initialize resultraw and get max_result_len
            resultraw = ""
            max_result_len = (self.objcfg.max_result_blocks * 1024)
            logging.debug("max_result_len = " + str(max_result_len))

            # Get the cmd_dict_list for the cmdtpye
            mode_level = 0
            cmd_dict_list = []
            cmdtype_dict_current = {}
            for cmdtype_dict in self.objcfg.cmdtype_dict_list:
                if self.fargs['cmdtype'].lower() == cmdtype_dict['cmdtype'].lower():
                    cmdtype_dict_current = cmdtype_dict
                    cmd_dict_list = cmdtype_dict_current['cmd_dict_list']
                    break

            # Set output line delimiter
            output_line_delimiter = str(cmdtype_dict_current['output_line_delimiter'])
            logging.debug('output_line_delimiter=' + output_line_delimiter)

            # Login to node or just perform ssh key exchange to node
            pl = self.pexpect_login(host_dict, icount)
            ssh_session = pl[1]
            if pl[0] == 'Success':
                pass

            elif pl[0] == 'kex only':

                # Remove LF/CR from result
                result = pl[2]
                result = result.replace('\n',output_line_delimiter)
                result = result.replace('\r',output_line_delimiter)

                # Truncate result to max_result_len length
                result = result[:max_result_len]

                # Log result to app log file
                logging.info("resultraw=" + str(result))

                # Update custom result fields
                ucrfl = self.update_custom_result_field_list(host_dict, icount, result)
                if ucrfl[0] == False:
                    return False

                sptr = self.ssh_update_result(host_dict, 'Check ssh key exchange - success', str(result), str(icount), 'Success', ucrfl[1])
                logging.debug("Exiting ssh_pexpect...")
                return True

            else:
                return False

            # Set echo false for ssh_session
            ssh_session.setecho(False)

            # Get the cmd_dict_list for the cmdtpye
            #mode_level = 0
            #cmd_dict_list = []
            #cmdtype_dict_current = {}
            #for cmdtype_dict in self.objcfg.cmdtype_dict_list:
                #if self.fargs['cmdtype'].lower() == cmdtype_dict['cmdtype'].lower():
                    #cmdtype_dict_current = cmdtype_dict
                    #cmd_dict_list = cmdtype_dict_current['cmd_dict_list']
                    #break

            # Set the default expect prompt
            expect_prompt_regex = cmdtype_dict_current['expect_prompt_regex']
            ssh_session.PROMPT = expect_prompt_regex

            # Initialize execute_exit_cmds_flag
            execute_exit_cmds_flag = False

            # Loop through ssh_cmds
            for cmd_dict in cmd_dict_list:

                # Get cmd and add user input to cmd
                cmd = cmd_dict['cmd']
                cmd = self.add_user_input(cmd)

                # Set the default expect prompt
                ssh_session.PROMPT = expect_prompt_regex

                # If cmd_cli_cmd_delay exists then use it else use cli_cmd_delay
                # cmd_cli_cmd_delay needed for long running CLI commands
                try:
                    cli_cmd_delay = cmd_dict['cmd_cli_cmd_delay']

                except:
                    cli_cmd_delay = self.objcfg.cli_cmd_delay

                # If it exists, set the expect prompt for the current ssh_cmd
                try:
                    cmd_expect_prompt_regex = cmd_dict['cmd_expect_prompt_regex']
                    ssh_session.PROMPT = cmd_expect_prompt_regex
                    logging.debug('cmd_expect_prompt_regex = ' + str(cmd_expect_prompt_regex))

                except Exception as e:
                    pass

                logging.debug('ssh_session.PROMPT = ' + str(ssh_session.PROMPT))

                # Execute custom script
                if self.fargs['cmdtype'].lower() == 'cli_custom':
                    cmd_list = cmd.split("@cmd_del@")
                    for cmditem in cmd_list:
                        esc = self.pexpect_ssh_cmd('custom', cmditem, cli_cmd_delay, ssh_session, host_dict, icount)
                        if esc[0] != 'Success':
                            return False
                        esc[2] = esc[2].replace('\n',output_line_delimiter)
                        esc[2] = esc[2].replace('\r',output_line_delimiter)
                        resultraw += esc[2]
                        if esc[1]:
                            break
                    break

                # Execute conf ssh_command
                esc = self.pexpect_ssh_cmd('conf', cmd, cli_cmd_delay, ssh_session, host_dict, icount)
                if esc[0] != 'Success':
                    return False
                esc[2] = esc[2].replace('\n',output_line_delimiter)
                esc[2] = esc[2].replace('\r',output_line_delimiter)
                result_ssh_cmd = esc[2]
                resultraw += result_ssh_cmd
                if esc[1]:
                    execute_exit_cmds_flag = True
                    break

                # Check for config diff
                cfncd = self.check_for_config_diff(result_ssh_cmd, cmd_dict, host_dict, icount)
                if cfncd[0] != 'Success':
                    return False
                if cfncd[1]:
                    execute_exit_cmds_flag = True
                    break

                # Check for a prompt
                cfp = self.check_for_prompt_pexpect(result_ssh_cmd, cli_cmd_delay, cmd_dict, mode_level, ssh_session, host_dict, icount)
                if cfp[0] != 'Success':
                    return False
                mode_level = cfp[2]
                cfp[3] = cfp[3].replace('\n',output_line_delimiter)
                cfp[3] = cfp[3].replace('\r',output_line_delimiter)
                resultraw += cfp[3]
                if cfp[1]:
                    execute_exit_cmds_flag = True
                    break

                # Process cmd_out against cmd_success_regex_list
                cmd_out = esc[2] + cfp[3]
                psc = self.process_ssh_cmd(cmd_out, cmd_dict, host_dict, icount)
                if psc[0] != 'Success':
                    return False
                if psc[1] != 'Success':
                    execute_exit_cmds_flag = True
                    break

                # Try to get mode_level
                try:
                    # Get mode_level variable for ssh_cmd
                    mode_level = cmd_dict['cmd_mode_level']

                except Exception as err:
                    logging.info('Unable to get mode level for cmd, err = ' + str(err))
                    pass

                # if the max_result_len is exceeded, break out of loop
                # this should not never happen for small length ouput from command
                if len(resultraw) > max_result_len:
                    execute_exit_cmds_flag = True

                # If execute_exit_cmds_flag is true then stop executing commands
                if execute_exit_cmds_flag:
                    break

            # If execute_exit_cmds_flag is True then exit ssh session due to conf ssh_cmd or prompt ssh_cmd failure
            if execute_exit_cmds_flag:
                while mode_level > -1:

                    logging.info('mode_level = ' + str(mode_level) + ' , exiting ssh session...')
                    esc = self.pexpect_ssh_cmd('execute_exit_cmds_flag', cmdtype_dict_current['exit_cmd'], cli_cmd_delay, ssh_session, host_dict, icount)
                    if esc[0] != 'Success':
                        return False

                    mode_level -= 1
                    # Remove LF/CR from cmd_out
                    esc[2] = esc[2].replace('\n',output_line_delimiter)
                    esc[2] = esc[2].replace('\r',output_line_delimiter)

                    resultraw += esc[2]

            # Eradicate resultraw
            result = self.eradicate_string(resultraw)

            # Remove LF/CR from result
            result = result.replace('\n',output_line_delimiter)
            result = result.replace('\r',output_line_delimiter)

            # Process result (get resultstatus & result values) of known commands
            pr = self.process_result(result)
            logging.debug("pr = " + str(pr))

            # Truncate result to max_result_len length
            result = result[:max_result_len]

            # Update custom result fields
            ucrfl = self.update_custom_result_field_list(host_dict, icount, result)
            if ucrfl[0] == False:
                return False

            # Log result to app log file
            logging.info("resultraw=" + str(result))

            # Remove output_line_delimiter from result
            result = result.replace(output_line_delimiter,'')

            sptr = self.ssh_update_result(host_dict,  pr[2], str(result), str(icount), pr[1], ucrfl[1])
            logging.debug("Exiting ssh_pexpect...")

            return True

        except Exception as err:

            logging.error('Error, ssh_pexpect function, icount = ' + str(icount) + ', err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            sptr = self.ssh_update_result(host_dict,  'Error, ssh_pexpect function, icount = ' + str(icount) + ', err = ' + str(err), 'Error, ssh_pexpect function, icount = ' + str(icount) + ', err = ' + str(err), str(icount), 'Fail', self.custom_result_field_list)
            ssh_session.close()
            return False

        finally:
            if ssh_session != None:
                ssh_session.close()

    def update_custom_result_field_list(self, host_dict, icount, result):

        try:

            # Update custom result fields
            custom_result_field_list = copy.deepcopy(self.custom_result_field_list)
            for i,custom_result_field_dict in enumerate(custom_result_field_list):
                match = re.search(custom_result_field_dict['field_regex'], result)

                try:
                    custom_result_field_list[i]['value'] = match.group('value')
                except:
                    custom_result_field_list[i]['value'] = ''

            logging.debug("custom_result_field_list = " + str(custom_result_field_list))
            logging.debug("self.custom_result_field_list = " + str(self.custom_result_field_list))

            return [True, custom_result_field_list]

        except Exception as err:

            logging.error('Error, update_custom_result_field_list function, icount = ' + str(icount) + ', err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            sptr = self.ssh_update_result(host_dict,  'Error, update_custom_result_field_list function, icount = ' + str(icount) + ', err = ' + str(err), \
                'Error, update_custom_result_field_list function, icount = ' + str(icount) + ', err = ' + str(err), str(icount), 'Fail', self.custom_result_field_list)
            return [False, custom_result_field_list]

    def check_socket(self, host, port, socketretries, sockettimeout):

        try:
            socket_count = 0
            check_socket_success = False
            for x in range(socketretries + 1):
                socket_count += 1
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(sockettimeout)
                if sock.connect_ex((host, port)) == 0:
                    check_socket_success = True
                    break

            if check_socket_success:
                return ['Success', socket_count]
            else:
                return ['Fail', socket_count]

        except Exception as err:
            return ['Fail', socket_count]

        finally:
            sock.close()

    def pexpect_login(self, host_dict, icount):

        try:  

            ssh_session = None
            record_num = host_dict['record_num']
            host = host_dict['ip_address']
            port = self.objcfg.sshport
            cipher = self.objcfg.cipher
            username = self.fargs['suser']
            password = self.fargs['spw']
            timeout = self.objcfg.ConnectTimeout
            connect_retries = self.objcfg.ConnectRetries
            socketretries = self.objcfg.SocketRetries
            sockettimeout = self.objcfg.SocketTimeout
            kex_verbose_level = self.objcfg.kex_verbose_level
            kex_filter_regex = self.objcfg.kex_filter_regex
            options = {}
            if self.objcfg.StrictHostKeyChecking != '':
                options['StrictHostKeyChecking'] = self.objcfg.StrictHostKeyChecking
            if self.objcfg.HostKeyAlgorithms != None:
                options['HostKeyAlgorithms'] = self.objcfg.HostKeyAlgorithms
            if self.objcfg.KexAlgorithms != None:
                options['KexAlgorithms'] = self.objcfg.KexAlgorithms
            if self.objcfg.PreferredAuthentications != None:
                options['PreferredAuthentications'] = self.objcfg.PreferredAuthentications

            # Port check
            # If sockettimeout = 0 & cmdtype = cli_check_port then set sockettimeout = 2
            if sockettimeout == 0 and self.fargs['cmdtype'].lower() == 'cli_check_port':
                logging.debug('SocketTimeout 0 & cmdtype = cli_check_port; so setting SocketTimeout = 2')
                sockettimeout = 2

            # If sockettimeout = 0 then port check is disabled
            if sockettimeout == 0:
                logging.debug('Port check is disabled')
            else:
                # If port is open then logon else log the port is not open for host and return
                cs = self.check_socket(host, port, socketretries, sockettimeout)
                logging.info('socket_count=' + str(cs[1]))
                if cs[0] == 'Success':

                    # Sleep for 1 second after successful socket check to allow time for disconnection to prevent max connections to ssh server
                    # This sleep delay was added based on Sonicwall v6.1.x firmware firewalls
                    time.sleep(1)

                    if self.fargs['cmdtype'].lower() == 'cli_check_port':
                        sptr = self.ssh_update_result(host_dict, "Port " + str(port) + " on host open", "Port " + str(port) + " on " + host + " open", \
                            str(icount), 'Success', self.custom_result_field_list)
                        return ['Abort Port Check Only', ssh_session, '']
                else:
                    sptr = self.ssh_update_result(host_dict, "Port " + str(port) + " on host not open", \
                        "Port " + str(port) + " on " + host + " not open after " + str(cs[1]) + " socket connection attempt(s).", \
                        str(icount), 'Fail', self.custom_result_field_list)
                    return ['Fail', ssh_session, '']

            # Try to connect to node
            connect_count = 0
            while True:

                logging.debug("Trying to connect to " + host +" (" + str(connect_count) + "/" + str(connect_retries) + ")")

                try:
                    ssh_session = pxssh_cliauto(options=options)
                    if self.fargs['cmdtype'].lower() == 'cli_check_vkex':
                        logging.debug("ssh key exchange only started for " + host + "; timeout = " + str(timeout))
                        kex_output_filtered = ssh_session.login(host, 'kex', '', login_timeout=timeout, port=port, cipher=cipher, auto_prompt_reset=False, \
                            original_prompt=r'#\s|>\s|% User logout\.', sync_original_prompt=False, quiet=False, \
                            verbose_level=kex_verbose_level, check_kex_only=True, \
                            kex_filter_regex=kex_filter_regex)
                        logging.debug("ssh key exchange only completed for " + host)
                        return ['kex only', ssh_session, kex_output_filtered]
                        break
                    else:
                        ssh_session.login(host, username, password, login_timeout=timeout, port=port, cipher=cipher, auto_prompt_reset=False, \
                            original_prompt='>|#', sync_original_prompt=False, quiet=False)
                        logging.debug("Connected to " + host)
                        break
                except ExceptionPxsshAccessDenied:
                    logging.debug("Authentication failed when connecting to " + host)
                    sptr = self.ssh_update_result(host_dict,  "Authentication failed when connecting to host", "Authentication failed when connecting to " + host, \
                        str(icount), 'Fail', self.custom_result_field_list)
                    return ['Fail', ssh_session, '']
                except ExceptionPxsshLoginTimeout:
                    logging.debug("Login timeout when connecting to " + host)
                    sptr = self.ssh_update_result(host_dict,  "Login timeout when connecting to host", "Login timeout when connecting to " + host, \
                        str(icount), 'Fail', self.custom_result_field_list)
                    return ['Fail', ssh_session, '']
                except ExceptionPxsshHostKeyChanged:
                    logging.debug("WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED FOR " + host + " SINCE LAST LOGIN! POSSIBLE MAN-IN-THE-MIDDLE ATTACK! It is also possible that a host key has just been changed. Verify the known host key on the server with the system administrator.")
                    sptr = self.ssh_update_result(host_dict,  \
                        "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED FOR HOST SINCE LAST LOGIN! POSSIBLE MAN-IN-THE-MIDDLE ATTACK! It is also possible that a host key has just been changed. Verify the known host key on the server with the system administrator.", \
                        "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED FOR " + host + " SINCE LAST LOGIN! POSSIBLE MAN-IN-THE-MIDDLE ATTACK! It is also possible that a host key has just been changed. Verify the known host key on the server with the system administrator.", \
                        str(icount), 'Fail', self.custom_result_field_list)
                    return ['Fail', ssh_session, '']
                except ExceptionPxsshMaxHostsExceeded:
                    logging.debug("Max # of hosts exceeded when connecting to " + host)
                    sptr = self.ssh_update_result(host_dict,  "Max # of hosts exceeded when connecting to host", "Max # of hosts exceeded when connecting to " + host, \
                        str(icount), 'Fail', self.custom_result_field_list)
                    return ['Fail', ssh_session, '']
                except ExceptionPxsshNoCipherFound:
                    logging.debug("No matching cipher found when connecting to " + host)
                    sptr = self.ssh_update_result(host_dict,  "No matching cipher found when connecting to host", "No matching cipher found when connecting to " + host, \
                        str(icount), 'Fail', self.custom_result_field_list)
                    return ['Fail', ssh_session, '']
                except Exception as err:
                    ssh_session.close()
                    logging.debug("Could not SSH to " + host + ", starting " + str(connect_retries) + " retries, err = " + str(err))
                    time.sleep(1)
                    connect_count += 1

                # If we could not connect after num_of_retries, log results and return
                if connect_count > connect_retries:
                    logging.debug("Could not connect to " + host + " after " + str(connect_count) + " connection attempt(s).")
                    sptr = self.ssh_update_result(host_dict,  "Could not connect to host", \
                        "Could not connect to " + host + " after " + str(connect_count) + " connection attempt(s).", \
                        str(icount), 'Fail', self.custom_result_field_list)
                    return ['Fail', ssh_session, '']

            return ['Success', ssh_session, '']

        except Exception as err:
            logging.error('Error, pexpect_login, icount = ' + str(icount) + ': err = ' + str(err))
            sptr = self.ssh_update_result(host_dict,  "Error, pexpect_login, err = " + str(err), "Error, pexpect_login, err = " + str(err), \
                str(icount), 'Fail', self.custom_result_field_list)
            return ['Fail', ssh_session, '']

    def pexpect_ssh_cmd(self, ssh_cmdtype, ssh_cmd, cli_cmd_delay, ssh_session, host_dict, icount):

        try:  

            cmd_out = ''
            ssh_cmd_log = self.eradicate_string(ssh_cmd)
            logging.debug("Entering pexpect_ssh_cmd..., ssh_cmd_log = " + str(ssh_cmd_log))
            execute_exit_cmds_flag = False

            # Send the ssh cmd
            ssh_session.sendline(str(ssh_cmd))

            # Expect the prompt, EOF, or timeout
            try:
                ssh_session.prompt(timeout=cli_cmd_delay)
            except pexpect.EOF:
                pass
            except Exception as err:
                logging.error('Error, pexpect_ssh_cmd function, ssh_cmdtype = ' + str(ssh_cmdtype) + ', err = ' + str(err))
                logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                sptr = self.ssh_update_result(host_dict,  'Error, pexpect_ssh_cmd function', \
                    'Error, pexpect_ssh_cmd function, icount = ' + str(icount) + ', ssh_cmdtype = ' + str(ssh_cmdtype) + ', err = ' + str(err), \
                    str(icount), 'Fail', self.custom_result_field_list)
                return ['Error', True, cmd_out]

            # Try to get the ssh session text
            before = ''
            after = ''
            try:
                before = str(ssh_session.before)
                if 'pexpect.exceptions.EOF'in before:
                    before = ''
            except:
                pass
            try:
                after = str(ssh_session.after)
                if 'pexpect.exceptions.EOF'in after:
                    after = ''
            except:
                pass
            cmd_out = before + after
            cmd_out = self.eradicate_string(cmd_out)

            return ['Success', execute_exit_cmds_flag, cmd_out]

        except Exception as err:

            logging.error('Error, pexpect_ssh_cmd function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            sptr = self.ssh_update_result(host_dict,  'Error, pexpect_ssh_cmd function', \
                'Error, pexpect_ssh_cmd function, icount = ' + str(icount) + ', ssh_cmdtype = ' + str(ssh_cmdtype) + ', err = ' + str(err), \
                 str(icount), 'Fail', self.custom_result_field_list)
            return ['Error', True, cmd_out]

    def check_for_prompt_pexpect(self, cmd_in, cli_cmd_delay, cmd_dict, mode_level, ssh_session, host_dict, icount):

        try:  

            cmd_out = ''
            logging.debug('Entering check_for_prompt_pexpect...')
            execute_exit_cmds_flag = False
            # Initialize prompt variables
            cmd_prompt_regex = ''
            cmd_prompt_response_string = ''
            cmd_prompt_response_mode_level = 0
            cmd_prompt_override_response_string = ''
            cmd_prompt_override_response_mode_level = 0

            # Get prompt variables
            try:
                cmd_prompt_regex = cmd_dict['cmd_prompt_regex']
                cmd_prompt_response_string = cmd_dict['cmd_prompt_response_string']
                cmd_prompt_response_mode_level = cmd_dict['cmd_prompt_response_mode_level']
                cmd_prompt_override_response_string = cmd_dict['cmd_prompt_override_response_string']
                cmd_prompt_override_response_mode_level = cmd_dict['cmd_prompt_override_response_mode_level']

            except:
                pass

            logging.debug('cmd_prompt_regex = ' + str(cmd_prompt_regex))
            # If a cmd prompt regex exists, check for a prompt 
            if cmd_prompt_regex != '':

                logging.debug('Checking for prompt, cmd =' + str(cmd_dict['cmd']))
                # If prompt is in the ssh_cmd cmd_out, respond to it
                if re.search(cmd_prompt_regex, cmd_in):

                    # If user requested prompt override then set response and model level
                    if self.fargs['check1'] == 'override':
                        cmd_prompt_response_string = cmd_prompt_override_response_string
                        cmd_prompt_response_mode_level = cmd_prompt_override_response_mode_level

                    # Execute ssh_command for Prompt
                    esc = self.pexpect_ssh_cmd('prompt', cmd_prompt_response_string, cli_cmd_delay, ssh_session, host_dict, icount)
                    cmd_out = esc[2]
                    if esc[0] != 'Success':
                        return ['Fail', True, mode_level, cmd_out]

                    if esc[1]:
                        execute_exit_cmds_flag = True

                    # Update the mode level
                    mode_level = cmd_prompt_response_mode_level

            return ['Success', execute_exit_cmds_flag, mode_level, cmd_out]

        except Exception as err:
            logging.error('Error, check_for_prompt_pexpect, icount = ' + str(icount) + ': err = ' + str(err))
            sptr = self.ssh_update_result(host_dict,  "Error, check_for_prompt_pexpect, err = " + str(err), \
                "Error, check_for_prompt_pexpect, err = " + str(err), str(icount), 'Fail', self.custom_result_field_list)
            return ['Fail', False, mode_level, cmd_out]

    def check_for_config_diff(self, cmd_in, cmd_dict, host_dict, icount):

        try:  

            cmd_out = ''
            logging.debug('Entering check_for_config_diff...')

            # Initialize cmd_no_config_diff_regex
            cmd_no_config_diff_regex = ''

            # Get cmd_no_config_diff_regex
            try:
                cmd_no_config_diff_regex = cmd_dict['cmd_no_config_diff_regex']

            except:
                pass

            logging.debug('cmd_no_config_diff_regex = ' + str(cmd_no_config_diff_regex))

            if self.fargs['check1'] == 'override':
                override_config_diff_flag = True
            else:
                override_config_diff_flag = False

            # If a cmd_no_config_diff_regex exists, check for config diff
            if cmd_no_config_diff_regex != '':


                logging.debug('Checking for no config diff, cmd =' + str(cmd_dict['cmd']))

                # If cmd_no_config_diff_regex is in the cmd_in, no configuration difference exists so return False
                if re.search(cmd_no_config_diff_regex, cmd_in):
                        return ['Success', False, override_config_diff_flag]

                else:
                    # If user requested override then return False
                    if override_config_diff_flag:
                        return ['Success', False, override_config_diff_flag]

                    else:
                        return ['Success', True, override_config_diff_flag]
            else:

                # Skip checking for configuration difference
                return ['Success', False, False]

        except Exception as err:
            logging.error('Error, check_for_config_diff, icount = ' + str(icount) + ': err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            sptr = self.ssh_update_result(host_dict,  "Error, check_for_config_diff, err = " + str(err), "Error, check_for_config_diff, err = " + str(err), \
                str(icount), 'Fail', self.custom_result_field_list)
            return ['Fail', False, False]
