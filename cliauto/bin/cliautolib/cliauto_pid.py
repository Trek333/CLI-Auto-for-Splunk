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
import errno
import requests

# Append directory of this file to the Python path (sys.path) to be able to import cliauto libs
if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from cliautolib.cliauto_kvstore import cliauto_kvstore
from cliautolib.cliauto_sshcom import sshcom
from cliautolib.cliauto_helpers import helpers
import splunklib.binding as binding
import splunklib.client as client

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

class pid(object):

    def __init__(self, fargs, sargs, cargs, ppid, objcfg):

        # Processing the request
        try:
            self.response = json.dumps({ 'payload': 'Error, Default pid response',
                                         'status': 400  # HTTP status code
                                      })

            self.fargs = fargs
            self.sargs = sargs
            self.cargs = cargs
            self.ppid = ppid
            self.pids = []
            self.objcfg = objcfg

            logging.info('Starting processing request...')

            # Development - cmdtype=LRP is to gain understanding of Splunk REST API python process life cycle
            if self.fargs['cmdtype'].lower() == 'lrp':
                logging.info('Success, long running process disabled')
                self.response = json.dumps({ 'payload': 'Success, long running process disabled',
                                             'status': 200  # HTTP status code
                                          })
                return None

                #host_list = ['h1', 'h2']
                #r = self.parallel_lrp(host_list, self.fargs, self.sargs)
                #logging.info('Success, started long running process')
                #self.response = json.dumps({ 'payload': 'Success, started long running process',
                #                             'status': 200  # HTTP status code
                #                          })
                #return None

            # Process cmdtype = status
            if self.fargs['cmdtype'].lower() == 'status':
                binding_service = binding.connect(token=self.sargs['authtoken'])
                self.sk = cliauto_kvstore(binding_service)

                if self.sk.status != 'Success':
                    self.response = json.dumps({ 'payload': str(self.sk.status),
                                                 'status': 400  # HTTP status code
                                              })
                    return None

                # Get the PID status
                gps = self.get_pid_status()

                # If the PID Status = Ready or Busy then set response status = 200
                # Else set response status = 400
                if gps[:5] == 'Ready' or gps[:4] == 'Busy':
                    self.response = json.dumps({ 'payload': str(gps),
                                                 'status': 200  # HTTP status code
                                              })
                else:
                    self.response = json.dumps({ 'payload': str(gps),
                                                 'status': 400  # HTTP status code
                                              })

                return None

            # Process cmdtype = cli*
            if self.fargs['cmdtype'][:3].lower() == 'cli':
                client_service = client.connect(token=self.sargs['authtoken'])
                binding_service = binding.connect(token=self.sargs['authtoken'])
                self.sk = cliauto_kvstore(binding_service)

                if self.sk.status != 'Success':
                    self.response = json.dumps({ 'payload': str(self.sk.status),
                                                 'status': 400  # HTTP status code
                                              })
                    return None

                # Get the PID status
                gps = self.get_pid_status()

                # If the PID Status = Ready & cmdtype = CLI then execute requested cmd
                # Else set response to PID status
                if gps == 'Ready':

                    ssc = sshcom(self.fargs, self.sargs, self.cargs, self.ppid, self.sk, binding_service, client_service, self.objcfg)
                    if ssc.status != 'Success':
                        self.response = ssc.response
                        return None

                    pc = ssc.process_cmd()
                    if pc != 'Success':
                        self.response = json.dumps({ 'payload': str(pc),
                                                     'status': 400  # HTTP status code
                                                  })
                        return None

                else:
                    self.response = json.dumps({ 'payload': str(gps),
                                                 'status': 400  # HTTP status code
                                              })
                    return None

                self.response = json.dumps({ 'payload': 'Success, started processing cli command',
                                             'status': 200  # HTTP status code
                                          })
                return None

            # Process unknown cmdtype
            else:
                self.response = json.dumps({ 'payload': 'Unknown cmdtype',
                                             'status': 400  # HTTP status code
                                          })
        except Exception as err:
            logging.error('Error, pid - processing request; err = ' + str(err))
            self.response = json.dumps({ 'payload': 'Error, Processing the request; err = ' + str(err),
                                         'status': 400  # HTTP status code
                                      })

    def fargs(self):
        return self.fargs

    def sargs(self):
        return self.sargs

    def cargs(self):
        return self.cargs

    def ppid(self):
        return self.ppid

    def objcfg(self):
        return self.objcfg

    def sk(self):
        return self.sk

    def response(self):
        return self.response

    def pids(self):
        return self.pids

    def get_pid_status(self):

        try:
            gp = self.get_pids()
            if gp != 'Success':
                return gp

            ft = self.fix_timestamps()
            if ft != 'Success':
                return ft

            gp = self.get_pids()
            if gp != 'Success':
                return gp

            doi = self.delete_old_items()
            if doi != 'Success':
                return doi

            ots = self.oktostart()
            return ots

        except Exception as err:
            logging.error('Error, get_pid_status method, err = ' + str(err))
            return 'Error, get_pid_status method, err = ' + str(err)

    def get_pids(self):

        try:
            gk = self.sk.get_items("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection")
            self.pids = gk[1]
            return gk[0]

        except Exception as err:
            logging.error('Error, get_pids method, err = ' + str(err))
            return ['Error, get_pids method, err = ' + str(err)]

    def delete_old_items(self):

        try:
            for item in self.pids:
                try:
                    starttime = int(item['StartTime'])/1000
                except:
                    continue
                epoch_now = int(time.time()*1000)/1000
                age = abs(epoch_now - starttime)

                # If age > pid_history_days (86,400 seconds in one day) then delete item
                if age  > (self.objcfg.pid_history_days * 86400):
                    gk = self.sk.delete_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + str(item['_key']))
                    if gk != 'Success':
                        return gk
            return 'Success'
        except Exception as err:
            logging.error('Error, delete_old_items method, err = ' + str(err))
            return 'Error, delete_old_items method, err = ' + str(err)

    def fix_timestamps(self):

        try:
            for item in self.pids:
                if 'Timestamp' not in item:
                    item['Timestamp'] = str(int(time.time() *1000))
                    cpurb = self.sk.create_pid_update_request_body(item, str(item['PID']), str(item['Status']), False)
                    if cpurb[0] != 'Success':
                        return cpurb
                    ui = self.sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + item['_key'],cpurb[1])
                    if ui[0] != 'Success':
                        return ui
            return 'Success'

        except Exception as err:
            logging.error('Error, fix_timestamps method, err = ' + str(err))
            return 'Error, fix_timestamps method, err = ' + str(err)

    def oktostart(self):

        try:
            for item in self.pids:

                # If an item key does not exist, continue to next item since unable to process the item
                # Probably never happen, but it does not cost much to check
                try:
                    item['_key']
                except:
                    continue

                # If a PID (or not integer) or Status does not exist, update the item Status = Data Error
                # Probably never happen, but it does not cost much to check and correct invalid data
                try:
                    int(item['PID'])
                    item['Status']
                    int(item['StartTime'])
                except:
                    try:
                        fpid = item['PID']
                    except:
                        fpid = ''

                    if item['Status'] != 'Done-Err' or fpid != '****':
                        cpurb = self.sk.create_pid_update_request_body(item, '****', 'Done-Err', True)

                        # If creating pid update request body is not successful, then return the error
                        if cpurb[0] != 'Success':
                            return cpurb[0]
                        uk = self.sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + str(item['_key']),cpurb[1])

                        # If the item update is not successful, then return the error
                        # Else continue
                        if uk[0] == 'Success':
                            return uk[0]
                        else:
                            continue

                # If a Status != Done, check if PID is active
                if item['Status'][:4] != 'Done':

                    # If the Timestamp is within IterationTimeout of current time, return Busy
                    ts = int(time.time() * 1000)
                    td = abs(ts - int(item['Timestamp']))/1000
                    if td < self.objcfg.IterationTimeout:
                        return 'Busy, PID = ' + str(item['PID']) + '; _key = ' + str(item['_key'])
                    
                    # If the PID is active, return Busy
                    # Else update the item Status = Done - Orphan
                    pe = self.pid_exists(int(item['PID']))
                    if pe:
                        return 'Busy, PID = ' + str(item['PID']) + '; _key = ' + str(item['_key'])
                    else:
                        cpurb = self.sk.create_pid_update_request_body(item, str(item['PID']), 'Done - Orphan', True)

                        # If creating pid update request body is not successful, then return the error
                        if cpurb[0] != 'Success':
                            return cpurb[0]
                        uk = self.sk.update_item("/servicesNS/nobody/cliauto/storage/collections/data/cliauto_pid_collection/" + str(item['_key']),cpurb[1])

                        # If the item update is not successful, then return the error
                        # Else continue
                        if uk[0] != 'Success':
                           return uk[0]
                        else:
                           continue

            return 'Ready'

        except Exception as err:
            logging.error('Error, oktostart method, err = ' + str(err))
            return 'Error, oktostart method, err = ' + str(err)

    def pid_exists(self, pid):
        # Check whether pid exists in the current process table.
        # UNIX only.
        if pid < 0:
            return False
        if pid == 0:
            # According to "man 2 kill" PID 0 refers to every process
            # in the process group of the calling process.
            # On certain systems 0 is a valid PID but we have no way
            # to know that in a portable fashion.
            raise ValueError('invalid PID 0')
        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                # ESRCH == No such process
                return False
            elif err.errno == errno.EPERM:
                # EPERM clearly means there's a process to deny access to
                return True
            else:
                # According to "man 2 kill" possible error values are
                # (EINVAL, EPERM, ESRCH)
                raise
        else:
            return True

    # Development - function to gain understanding of Splunk REST API python process life cycle
    def lrp(self, host, num_of_delays, wait_time, fargs, sargs, parallel=False):

        logging.debug("Starting lrp...")
        i = 0

        if num_of_delays > 600:
            num_of_delays = 600

        if wait_time > 60:
            wait_time = 60

        logging.debug("Starting lrp while loop...num_of_delays = " + str(num_of_delays) + "; wait_time = " + str(wait_time))
        while i < num_of_delays:
            logging.debug("In lrp while loop...i = " + str(i) + "; wait_time = " + str(wait_time))
            time.sleep(wait_time)
            logging.debug('wait delay ' + str(i) + ' complete...')
            i += 1

        logging.debug("lrp exiting...")
        return 0

    # Development - function to gain understanding of Splunk REST API python process life cycle
    def lrp_refresh(self, num_of_delays, wait_time, fargs, sargs, parallel=False):

        logging.debug("Starting lrp_refresh...")
        i = 0

        if num_of_delays > 7200:
            num_of_delays = 7200

        if wait_time > 60:
            wait_time = 60

        #reqbody = 'cmdtype=HB&cmd=na&suser=su&spw=spw&nodelist=nl'
        reqbody = 'cmdtype=HB'
        #logging.debug ("reqbody = " + str(reqbody))
        header = [('Content-Type', 'application/x-www-form-urlencoded')]
        service = binding.connect(token=str(sargs['authtoken']))

        logging.debug("Starting lrp_refresh while loop...num_of_delays = " + str(num_of_delays) + "; wait_time = " + str(wait_time))
        while i < num_of_delays:
            logging.debug("In lrp_refresh while loop...i = " + str(i) + "; wait_time = " + str(wait_time))
            time.sleep(wait_time)
            logging.debug('wait delay ' + str(i) + ' complete...')
            response = service.request('/services/cliauto', method='POST', headers=header, body=reqbody)
            #response = requests.post('https://127.0.0.1/en-US/splunkd/__raw/services/cliauto', headers=self.cargs, data={'cmdtype' : 'HB'}, verify=False)
            response_web = requests.post('https://127.0.0.1/en-US/app/cliauto/hb', headers=self.cargs, verify=False)
            logging.debug('lrp_refresh call ' + str(i) + ' complete...')
            logging.debug('response = ' + str(response))
            logging.debug('response_web = ' + str(response_web))
            i += 1

        logging.debug("lrp exiting...")
        return 0

    # Development - function to gain understanding of Splunk REST API python process life cycle
    def parallel_lrp(self, host_list, fargs, sargs):

        # Use threads to run a ssh command on hosts.
        # Returns a dict of {hostname:result} for each host.

        logging.debug("running lrp on " + str(len(host_list)) + " hosts")
        for host in host_list:
            t = Thread(target=self.lrp, args=([host, 600, 60, fargs, sargs, True]))
            #t = Thread(target=self.lrp, args=([host, 2, 2, fargs, sargs, True]))
            t.start()

        t = Thread(target=self.lrp_refresh, args=([7200, 5, fargs, sargs, True]))
        #t = Thread(target=self.lrp_refresh, args=([2, 2, fargs, sargs, True]))
        t.start()

        logging.debug("Started threads")
        start_time = time.time()
        logging.debug("len(host_list) = " + str(len(host_list)))
        logging.debug("Exiting parallel_lrp")
        return True
