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

# Import cliauto and Splunk SDK libs
from cliauto_helpers import helpers
from cliautolib.cliauto_search import cliauto_search
import splunklib.binding as binding
import splunklib.client as client
import splunklib.results as results

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

class configconf(object):

    def __init__(self, fargs, sargs, ppid):

        try:
            self.status = "Failure - default message cliauto_confconfig"
            logging.info("configconf object being created...")
            self.fargs = fargs
            self.sargs = sargs
            self.ppid = ppid

            # app=cliauto is needed to match list of CSV files in UI for permissions
            self.connect_service = client.connect(token=sargs['authtoken'],app='cliauto')
            self.service = binding.connect(token=self.sargs['authtoken'])

            self.cliauto_version = ''
            self.index = 'main'
            self.sourcetype = 'cliauto_ssh'
            self.source = 'cliauto'
            self.ConnectRetries = 0
            self.ConnectTimeout = 15
            self.SocketRetries = 0
            self.SocketTimeout = 2
            self.sshport = 22
            self.cipher = None
            self.StrictHostKeyChecking = ''
            self.HostKeyAlgorithms = None
            self.KexAlgorithms = None
            self.PreferredAuthentications = None
            self.MaxThreads = 75
            self.pid_history_days = 30
            self.HBTimeout = 10
            self.max_host_count = 2000
            self.max_result_blocks = 25
            self.IterationTimeout = 300
            self.cli_cmd_delay = 5
            self.default_input_data_length_max = 100
            self.absolute_input_data_length_max = 1000
            self.allow_duplicate_ip_address = '0'
            self.kex_verbose_level = 2
            self.kex_filter_regex = r'(kex:\s.*[\s\S]?)'

            self.hostcount = 0
            self.hosts = []
            self.nhosts = None
            self.cmdtype_dict_list = []
            self.status = 'Success'

        except Exception as err:
            logging.error('Error, cliauto_confconfig init function, err = ' + str(err))
            self.status = 'Error, cliauto_confconfig init function, err = ' + str(err)
            return None


    def fargs(self):
        return self.fargs

    def sargs(self):
        return self.sargs

    def ppid(self):
        return self.ppid

    def service(self):
        return self.service

    def cliauto_version(self):
        return self.cliauto_version

    def index(self):
        return self.index

    def sourcetype(self):
        return self.sourcetype

    def source(self):
        return self.source

    def ConnectRetries(self):
        return self.ConnectRetries

    def ConnectTimeout(self):
        return self.ConnectTimeout

    def SocketRetries(self):
        return self.SocketRetries

    def SocketTimeout(self):
        return self.SocketTimeout

    def sshport(self):
        return self.sshport

    def cipher(self):
        return self.cipher

    def StrictHostKeyChecking(self):
        return self.StrictHostKeyChecking

    def HostKeyAlgorithms(self):
        return self.HostKeyAlgorithms

    def KexAlgorithms(self):
        return self.KexAlgorithms

    def PreferredAuthentications(self):
        return self.PreferredAuthentications

    def MaxThreads(self):
        return self.MaxThreads

    def pid_history_days(self):
        return self.pid_history_days

    def HBTimeout(self):
        return self.HBTimeout

    def max_host_count(self):
        return self.max_host_count

    def max_result_blocks(self):
        return self.max_result_blocks

    def IterationTimeout(self):
        return self.IterationTimeout

    def cli_cmd_delay(self):
        return self.cli_cmd_delay

    def default_input_data_length_max(self):
        return self.default_input_data_length_max

    def absolute_input_data_length_max(self):
        return self.absolute_input_data_length_max

    def allow_duplicate_ip_address(self):
        return self.allow_duplicate_ip_address

    def kex_verbose_level(self):
        return self.kex_verbose_level

    def kex_filter_regex(self):
        return self.kex_filter_regex

    def hostcount(self):
        return self.hostcount

    def hosts(self):
        return self.hosts

    def nhosts(self):
        return self.nhosts

    def status(self):
        return self.status

    def cmdtype_dict_list(self):
        return self.cmdtype_dict_list

    def get_items(self, path):

        try:
            logging.info('Starting get_items...')
            response = self.service.request(path, method='GET')

            body = response.body.read()
            dom=xml.dom.minidom.parseString(body)
            keys=dom.getElementsByTagName('s:key')
            return ['Success', keys]

        except Exception as err:
            logging.error('Error, get_items function, err = ' + str(err))
            return ['Error, get_items function, err = ' + str(err), []]

    def get_stanzas(self, path):

        try:
            logging.info('Starting get_stanzas...')
            response = self.service.request(path, method='GET')
            body = response.body.read()
            dom=xml.dom.minidom.parseString(body)
            feedkeys=dom.getElementsByTagName('feed')
            for feedkey in feedkeys:
                entrykeys=dom.getElementsByTagName('entry')

            return ['Success', entrykeys]

        except Exception as err:
            logging.error('Error, get_stanzas function, err = ' + str(err))
            return ['Error, get_stanzas function, err = ' + str(err), []]

    def get_hosts(self):

        try:
            searchlist = {'args': ['| inputlookup ' + self.fargs['nodelist'] ], 'kwargs': {}}
            s = cliauto_search(self.connect_service, searchlist)
            logging.debug("s.search_parse_status = " + str(s.search_parse_status))
            ss = s.search_sync()
            reader = results.ResultsReader(s.results)
            self.hosts = []
            rec_count = 0
            for item in reader:
                rec_count = rec_count + 1
                if rec_count > self.max_host_count:
                    logging.info("Max hosts exceeded truncating host list: current rec_count(" + str(rec_count) + ") > max_host_count(" + str(self.max_host_count) + ")")
                    break
                item['record_num'] = rec_count
                self.hosts.append(item)
            self.hostcount = rec_count
            if reader.is_preview:
                logging.info("Results are a preview: %s" % reader.is_preview)
                return 'Failure, Splunk search returned preview of hosts list'

            # if the number hosts is less than 1, exit script
            if len(self.hosts) < 1:
                logging.info("Exiting...# of hosts = " + str(len(self.hosts)))
                return 'Failure, # of hosts < 1'

            # If duplicate ip addresses not allowed, check for duplicate ip addresses and return failure if duplicates found
            logging.debug('self.allow_duplicate_ip_address = ' + str(self.allow_duplicate_ip_address))
            if self.allow_duplicate_ip_address != '1':
                host_list = []
                dup_list = []
                for ihost,host in enumerate(self.hosts):
                    host_list.append(host['ip_address'].strip())
                dup_list = self.list_duplicates(host_list)
                logging.debug('dup_list = ' + str(dup_list))
                if dup_list != []:
                    return 'Failure, ' + str(len(dup_list)) + ' duplicate host ip address(es) exists in ' + str(len(self.hosts)) + ' host(s): ' + str(dup_list)

            # Log number of hosts in config file
            logging.info("# of hosts found in config file = " + str(len(self.hosts)))

            numhosts = len(self.hosts)
            if self.MaxThreads <= numhosts:

                # Create split array for host iterations
                self.nhosts = (helpers().split(self.hosts,self.MaxThreads))
                logging.info(str(len(self.nhosts)) + " iterations will be executed")

                index = 1
                for lst in self.nhosts:
                    logging.info("iteration # " + str(index) + " has " + str(len(lst)) + " host(s)")
                    index = index + 1

            else:
                self.nhosts = None
                logging.info("Just use hosts variable, 1 iteration will be executed")

            # Log hosts to file
            for host in self.hosts:
                logging.debug(host)

            return 'Success'

        except Exception as err:
            logging.error('Error, get_hosts function, err = ' + str(err))
            return 'Error, get_hosts function, err = ' + str(err)

    def list_duplicates(self, seq):
        seen = set()
        seen_add = seen.add
        # adds all elements it doesn't know yet to seen and all other to seen_twice
        seen_twice = set( x for x in seq if x in seen or seen_add(x) )
        # turn the set into a list (as requested)
        return list( seen_twice )

    def validate_num_setting(self, setting_name, conf_value, default_value, min_value, max_value):

        try:
            # If conf_value is number, attempt to set it
            if helpers().is_number(conf_value):
                conf_value = int(conf_value)
                # If conf_value < min_value or > max_value, set to default_value
                if (conf_value < min_value) or (conf_value > max_value):
                    logging.info(setting_name + "(" +  str(conf_value) + ") < " + str(min_value) + " or > " + str(max_value) + "; set " + setting_name + " = " + str(default_value))
                    return ['Success', int(default_value)]
                else:

                    logging.info(setting_name + " = " + str(conf_value))
                    return ['Success', int(conf_value)]
            else:
                # If conf_value is not number, set to default
                logging.info(setting_name + "(" +  str(conf_value) + ") is not a number; set " + setting_name + " = " + str(default_value))
                return ['Success', int(default_value)]

        except Exception as err:
            logging.error('Error, validate_num_setting function, err = ' + str(err))
            return ['Error, validate_num_setting function, err = ' + str(err), 0]

    def getconfig(self):

        try:
            logging.info("Starting getconfig...")

            # Get cliauto variables
            keys = self.get_items("/servicesNS/-/cliauto/configs/conf-cliauto/main")
            if keys[0] != "Success":
                return keys[0]

            for key in keys[1]:
                if key.getAttribute('name') == 'index': 
                    self.index = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'source': 
                    self.source = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'sourcetype': 
                    self.sourcetype = key.childNodes[0].nodeValue

                if key.getAttribute('name') == 'ConnectRetries': 
                    self.ConnectRetries = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'ConnectTimeout': 
                    self.ConnectTimeout = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'SocketRetries': 
                    self.SocketRetries = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'SocketTimeout': 
                    self.SocketTimeout = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'sshport': 
                    self.sshport = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'cipher': 
                    self.cipher = self.getnodevalue(key.childNodes)
                if key.getAttribute('name') == 'StrictHostKeyChecking': 
                    self.StrictHostKeyChecking = key.childNodes[0].nodeValue.strip('"')
                if key.getAttribute('name') == 'HostKeyAlgorithms': 
                    self.HostKeyAlgorithms = self.getnodevalue(key.childNodes)
                if key.getAttribute('name') == 'KexAlgorithms': 
                    self.KexAlgorithms = self.getnodevalue(key.childNodes)
                if key.getAttribute('name') == 'PreferredAuthentications': 
                    self.PreferredAuthentications = self.getnodevalue(key.childNodes)
                if key.getAttribute('name') == 'MaxThreads': 
                    self.MaxThreads = key.childNodes[0].nodeValue

                if key.getAttribute('name') == 'HBTimeout': 
                    self.HBTimeout = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'pid_history_days': 
                    self.pid_history_days = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'max_host_count': 
                    self.max_host_count = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'max_result_blocks': 
                    self.max_result_blocks = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'IterationTimeout': 
                    self.IterationTimeout = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'cli_cmd_delay':
                    self.cli_cmd_delay = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'default_input_data_length_max':
                    self.default_input_data_length_max = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'absolute_input_data_length_max':
                    self.absolute_input_data_length_max = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'allow_duplicate_ip_address':
                    self.allow_duplicate_ip_address = key.childNodes[0].nodeValue

                if key.getAttribute('name') == 'kex_verbose_level': 
                    self.kex_verbose_level = key.childNodes[0].nodeValue
                if key.getAttribute('name') == 'kex_filter_regex': 
                    self.kex_filter_regex = key.childNodes[0].nodeValue

            # Validate ConnectRetries from conf file
            vns = self.validate_num_setting('ConnectRetries', self.ConnectRetries, 0, 0, 10)
            if vns[0] != "Success":
                return vns[0]
            self.ConnectRetries = vns[1]

            # Validate ConnectTimeout from conf file
            vns = self.validate_num_setting('ConnectTimeout', self.ConnectTimeout, 15, 15, 600)
            if vns[0] != "Success":
                return vns[0]
            self.ConnectTimeout = vns[1]

            # Validate SocketRetries from conf file
            vns = self.validate_num_setting('SocketRetries', self.SocketRetries, 0, 0, 10)
            if vns[0] != "Success":
                return vns[0]
            self.SocketRetries = vns[1]

            # Validate SocketTimeout from conf file
            vns = self.validate_num_setting('SocketTimeout', self.SocketTimeout, 2, 0, 10)
            if vns[0] != "Success":
                return vns[0]
            self.SocketTimeout = vns[1]

            # Validate sshport from conf file
            vns = self.validate_num_setting('sshport', self.sshport, 22, 1, 65535)
            if vns[0] != "Success":
                return vns[0]
            self.sshport = vns[1]

            # Validate MaxThreads from conf file
            vns = self.validate_num_setting('MaxThreads', self.MaxThreads, 75, 1, 100)
            if vns[0] != "Success":
                return vns[0]
            self.MaxThreads = vns[1]

            # Validate HBTimeout from conf file
            vns = self.validate_num_setting('HBTimeout', self.HBTimeout, 10, 10, 50)
            if vns[0] != "Success":
                return vns[0]
            self.HBTimeout = vns[1]

            # Validate pid_history_days from conf file
            vns = self.validate_num_setting('pid_history_days', self.pid_history_days, 30, 1, 365)
            if vns[0] != "Success":
                return vns[0]
            self.pid_history_days = vns[1]

            # Validate max_host_count from conf file
            vns = self.validate_num_setting('max_host_count', self.max_host_count, 2000, 1, 5000)
            if vns[0] != "Success":
                return vns[0]
            self.max_host_count = vns[1]

            # Validate max_result_blocks from conf file
            vns = self.validate_num_setting('max_result_blocks', self.max_result_blocks, 25, 1, 50)
            if vns[0] != "Success":
                return vns[0]
            self.max_result_blocks = vns[1]

            # Validate IterationTimeout from conf file
            vns = self.validate_num_setting('IterationTimeout', self.IterationTimeout, 300, 1, 600)
            if vns[0] != "Success":
                return vns[0]
            self.IterationTimeout = vns[1]

            # Validate cli_cmd_delay from conf file
            vns = self.validate_num_setting('cli_cmd_delay', self.cli_cmd_delay, 5, 1, 60)
            if vns[0] != "Success":
                return vns[0]
            self.cli_cmd_delay = vns[1]

            # Validate default_input_data_length_max from conf file
            vns = self.validate_num_setting('default_input_data_length_max', self.default_input_data_length_max, 100, 1, 1000)
            if vns[0] != "Success":
                return vns[0]
            self.default_input_data_length_max = vns[1]

            # Validate absolute_input_data_length_max from conf file
            vns = self.validate_num_setting('absolute_input_data_length_max', self.absolute_input_data_length_max, 1000, 1, 2000)
            if vns[0] != "Success":
                return vns[0]
            self.absolute_input_data_length_max = vns[1]

            # Validate kex_verbose_level from conf file
            vns = self.validate_num_setting('kex_verbose_level', self.kex_verbose_level, 2, 0, 3)
            if vns[0] != "Success":
                return vns[0]
            self.kex_verbose_level = vns[1]

            return 'Success'

        except Exception as err:
            logging.error('Error, getconfig function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, getconfig function, err = ' + str(err)

    def getappversion(self):

        try:

            logging.info("Starting getappversion...")

            # Get cliauto app version
            app_keys = self.get_items("/servicesNS/nobody/cliauto/configs/conf-app/launcher")

            if app_keys[0] != "Success":
                return app_keys[0]

            for app_key in app_keys[1]:
                if app_key.getAttribute('name') == 'version': 
                    self.cliauto_version = app_key.childNodes[0].nodeValue

            return 'Success'

        except Exception as err:
            logging.error('Error, getappversion function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, getappversion function, err = ' + str(err)

    def getconfigall(self):

        try:

            # Get cliauto config
            gc = self.getconfig()
            if gc != "Success":
                return gc

            # Get cliauto_cmds config
            gcc = self.getconfigcmds()
            if gcc != "Success":
                return gcc

            # Get cliauto app version
            gav = self.getappversion()
            if gav != "Success":
                return gav

            return 'Success'

        except Exception as err:
            logging.error('Error, getconfigall function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, getconfigall function, err = ' + str(err)

    def getnodevalue(self, keychildnodes, default_value=None):

        if keychildnodes == []:
            return default_value
        else:
            if keychildnodes[0].nodeValue.strip() == '':
                return default_value
            else:
                return keychildnodes[0].nodeValue

    def getconfigcmds(self):

        try:

            logging.info("Starting getconfigcmds...")

            #self.service = binding.connect(token=self.sargs['authtoken'])

            # Get cliauto_cmds stanzas
            #stanzakeys = self.get_stanzas("/servicesNS/-/cliauto/configs/conf-cliauto_cmds")
            #if stanzakeys[0] != "Success":
                #return stanzakeys[0]

            #stanzas= []
            #for stanzakey in stanzakeys[1]:

                #stanzas.append(str(stanzakey.getElementsByTagName('title')[0].firstChild.data))

            # Get only the stanza from input to REST API due to default max = 30 entries for response
            # The key/value pair count="0" for a GET query parameter would get all stanzas 
            # See https://docs.splunk.com/Documentation/Splunk/7.3.2/RESTREF/RESTprolog#Pagination_and_filtering_parameters
            stanzas = [self.fargs['cmdtype'].lower()]

            # Process stanzas
            for stanza in stanzas:
                logging.debug("stanza = " + stanza)

               # Get cliauto_cmds for stanza
                keys = self.get_items("/servicesNS/-/cliauto/configs/conf-cliauto_cmds/" + stanza)

                if keys[0] != "Success":
                    return keys[0]

                cmdtype_enable = 0
                output_line_delimiter = ''
                kv_cmd_string = ''
                default_fail_msg = ''
                expect_prompt_regex = ''
                find_regex1 = ''
                find_regex2 = ''
                find_regex3 = ''
                find_regex4 = ''
                find_regex5 = ''
                success_msg1 = ''
                success_msg2 = ''
                success_msg3 = ''
                success_msg4 = ''
                success_msg5 = ''
                success_regex1 = ''
                success_regex2 = ''
                success_regex3 = ''
                success_regex4 = ''
                success_regex5 = ''
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
                exit_cmd = ''
                ui_var1_length_min = None
                ui_var2_length_min = None
                ui_var3_length_min = None
                ui_var4_length_min = None
                ui_var1_length_max = None
                ui_var2_length_max = None
                ui_var3_length_max = None
                ui_var4_length_max = None
                ui_pw1_length_min = None
                ui_pw2_length_min = None
                ui_pw3_length_min = None
                ui_pw1_length_max = None
                ui_pw2_length_max = None
                ui_pw3_length_max = None
                ui_var1_invalid_characters = ''
                ui_var2_invalid_characters = ''
                ui_var3_invalid_characters = ''
                ui_var4_invalid_characters = ''
                ui_pw1_invalid_characters = ''
                ui_pw2_invalid_characters = ''
                ui_pw3_invalid_characters = ''
                ui_var1_length_min_msg = ''
                ui_var2_length_min_msg = ''
                ui_var3_length_min_msg = ''
                ui_var4_length_min_msg = ''
                ui_var1_length_max_msg = ''
                ui_var2_length_max_msg = ''
                ui_var3_length_max_msg = ''
                ui_var4_length_max_msg = ''
                ui_pw1_length_min_msg = ''
                ui_pw2_length_min_msg = ''
                ui_pw3_length_min_msg = ''
                ui_pw1_length_max_msg = ''
                ui_pw2_length_max_msg = ''
                ui_pw3_length_max_msg = ''
                ui_var1_invalid_characters_msg = ''
                ui_var2_invalid_characters_msg = ''
                ui_var3_invalid_characters_msg = ''
                ui_var4_invalid_characters_msg = ''
                ui_pw1_invalid_characters_msg = ''
                ui_pw2_invalid_characters_msg = ''
                ui_pw3_invalid_characters_msg = ''
                output_type_dict = {}
                for output_type_index in range(1, 21):
                    output_type_dict[str(output_type_index)] = {}
                max_result_blocks_override = None

                # Loop through keys to get varaibles
                cmd_dict_list = []
                custom_result_field_list = []
                for key in keys[1]:

                    if key.getAttribute('name') == 'cmdtype_enable':
                        cmdtype_enable = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'output_line_delimiter':
                        output_line_delimiter = self.getnodevalue(key.childNodes, default_value='')
                    elif key.getAttribute('name') == 'kv_cmd_string':
                        kv_cmd_string = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'expect_prompt_regex':
                        expect_prompt_regex = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'default_fail_msg':
                        default_fail_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'find_regex1':
                        find_regex1 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'find_regex2':
                        find_regex2 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'find_regex3':
                        find_regex3 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'find_regex4':
                        find_regex4 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'find_regex5':
                        find_regex5 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_msg1':
                        success_msg1 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_msg2':
                        success_msg2 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_msg3':
                        success_msg3 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_msg4':
                        success_msg4 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_msg5':
                        success_msg5 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_regex1':
                        success_regex1 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_regex2':
                        success_regex2 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_regex3':
                        success_regex3 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_regex4':
                        success_regex4 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'success_regex5':
                        success_regex5 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_regex1':
                        skip_regex1 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_msg1':
                        skip_msg1 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_regex2':
                        skip_regex2 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_msg2':
                        skip_msg2 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_regex3':
                        skip_regex3 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_msg3':
                        skip_msg3 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_regex4':
                        skip_regex4 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_msg4':
                        skip_msg4 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_regex5':
                        skip_regex5 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'skip_msg5':
                        skip_msg5 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_regex1':
                        fail_regex1 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_msg1':
                        fail_msg1 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_regex2':
                        fail_regex2 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_msg2':
                        fail_msg2 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_regex3':
                        fail_regex3 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_msg3':
                        fail_msg3 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_regex4':
                        fail_regex4 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_msg4':
                        fail_msg4 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_regex5':
                        fail_regex5 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'fail_msg5':
                        fail_msg5 = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'exit_cmd':
                        exit_cmd = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var1_length_min':
                        ui_var1_length_min = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var2_length_min':
                        ui_var2_length_min = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var3_length_min':
                        ui_var3_length_min = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var4_length_min':
                        ui_var4_length_min = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var1_length_max':
                        ui_var1_length_max = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var2_length_max':
                        ui_var2_length_max = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var3_length_max':
                        ui_var3_length_max = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var4_length_max':
                        ui_var4_length_max = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw1_length_min':
                        ui_pw1_length_min = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw2_length_min':
                        ui_pw2_length_min = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw3_length_min':
                        ui_pw3_length_min = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw1_length_max':
                        ui_pw1_length_max = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw2_length_max':
                        ui_pw2_length_max = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw3_length_max':
                        ui_pw3_length_max = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var1_invalid_characters':
                        ui_var1_invalid_characters = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var2_invalid_characters':
                        ui_var2_invalid_characters = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var3_invalid_characters':
                        ui_var3_invalid_characters = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var4_invalid_characters':
                        ui_var4_invalid_characters = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw1_invalid_characters':
                        ui_pw1_invalid_characters = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw2_invalid_characters':
                        ui_pw2_invalid_characters = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw3_invalid_characters':
                        ui_pw3_invalid_characters = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var1_length_min_msg':
                        ui_var1_length_min_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var2_length_min_msg':
                        ui_var2_length_min_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var3_length_min_msg':
                        ui_var3_length_min_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var4_length_min_msg':
                        ui_var4_length_min_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var1_length_max_msg':
                        ui_var1_length_max_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var2_length_max_msg':
                        ui_var2_length_max_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var3_length_max_msg':
                        ui_var3_length_max_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var4_length_max_msg':
                        ui_var4_length_max_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw1_length_min_msg':
                        ui_pw1_length_min_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw2_length_min_msg':
                        ui_pw2_length_min_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw3_length_min_msg':
                        ui_pw3_length_min_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw1_length_max_msg':
                        ui_pw1_length_max_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw2_length_max_msg':
                        ui_pw2_length_max_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw3_length_max_msg':
                        ui_pw3_length_max_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var1_invalid_characters_msg':
                        ui_var1_invalid_characters_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var2_invalid_characters_msg':
                        ui_var2_invalid_characters_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var3_invalid_characters_msg':
                        ui_var3_invalid_characters_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_var4_invalid_characters_msg':
                        ui_var4_invalid_characters_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw1_invalid_characters_msg':
                        ui_pw1_invalid_characters_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw2_invalid_characters_msg':
                        ui_pw2_invalid_characters_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'ui_pw3_invalid_characters_msg':
                        ui_pw3_invalid_characters_msg = key.childNodes[0].nodeValue
                    elif key.getAttribute('name') == 'max_result_blocks_override':
                        max_result_blocks_override = key.childNodes[0].nodeValue

                        # Validate max_result_blocks_override from conf file
                        vns = self.validate_num_setting('max_result_blocks_override', max_result_blocks_override, 25, 1, 500)
                        if vns[0] != "Success":
                            return vns[0]
                        max_result_blocks_override = vns[1]

                    for output_type_index in range(1, 21):
                        record_num = str(output_type_index)
                        if key.getAttribute('name') == 'output_data_name' + format(output_type_index, '02'):
                            output_type_dict[record_num]['output_data_name'] = key.childNodes[0].nodeValue
                            break
                        elif key.getAttribute('name') == 'output_data_type' + format(output_type_index, '02'):
                            output_type_dict[record_num]['output_data_type'] = key.childNodes[0].nodeValue
                            break
                        elif key.getAttribute('name') == 'output_data_format' + format(output_type_index, '02'):
                            output_type_dict[record_num]['output_data_format'] = key.childNodes[0].nodeValue
                            break
                        elif key.getAttribute('name') == 'output_header_regex' + format(output_type_index, '02'):
                            output_type_dict[record_num]['output_header_regex'] = key.childNodes[0].nodeValue
                            break
                        elif key.getAttribute('name') == 'output_data_regex' + format(output_type_index, '02'):
                            output_type_dict[record_num]['output_data_regex'] = key.childNodes[0].nodeValue
                            break

                    for custom_result_field_index in range(1, 21):
                        if key.getAttribute('name') == 'custom_result_field' + format(custom_result_field_index, '02'):
                            custom_result_field_dict = {}
                            custom_result_field_dict['field_name'] = key.childNodes[0].nodeValue
                            for key in keys[1]:
                                if key.getAttribute('name') == 'custom_result_field' + format(custom_result_field_index, '02') + '_regex':
                                    custom_result_field_dict['field_regex'] = key.childNodes[0].nodeValue
                                    custom_result_field_dict['duplicate_check'] = '0'
                                    for key in keys[1]:
                                        if key.getAttribute('name') == 'custom_result_field' + format(custom_result_field_index, '02') + '_duplicate_check':
                                            custom_result_field_dict['duplicate_check'] = key.childNodes[0].nodeValue
                                            logging.debug('custom_result_field_dict = ' + str(custom_result_field_dict))
                                            break
                                    custom_result_field_list.append(custom_result_field_dict)
                                    break

                    # Get the main branch of CLI cmds
                    if key.getAttribute('name')[:3] == 'cmd':
                        gccl = self.getconfigcmdlist(key, keys, 'main')
                        if gccl[0] != 'Success':
                            return gccl[0]
                        logging.debug('gccl[1]=' + str(gccl[1]))
                        cmd_dict_list = cmd_dict_list + gccl[1]

                    # Get the alternate branches of CLI cmds
                    if key.getAttribute('name')[:10] == 'cmd_branch':
                        for branch_index in range(1, 21):
                            branch_list_name = 'branch' + format(branch_index, '02')
                            gccl = self.getconfigcmdlist(key, keys, branch_list_name)
                            if gccl[0] != 'Success':
                                return gccl[0]
                            cmd_dict_list = cmd_dict_list + gccl[1]

                self.cmdtype_dict_list.append({ \
                'cmdtype' : stanza, 'cmdtype_enable' : cmdtype_enable, 'output_line_delimiter' : output_line_delimiter, \
                'kv_cmd_string' : kv_cmd_string, 'expect_prompt_regex' : expect_prompt_regex, \
                'default_fail_msg' : default_fail_msg, 'find_regex1' : find_regex1, 'find_regex2' : find_regex2, 'find_regex3' : find_regex3, \
                'find_regex4' : find_regex4, 'find_regex5' : find_regex5, \
                'success_msg1' : success_msg1, 'success_msg2' : success_msg2, 'success_msg3' : success_msg3, 'success_msg4' : success_msg4, \
                'success_msg5' : success_msg5, 'success_regex1' : success_regex1, \
                'success_regex2' : success_regex2, 'success_regex3' : success_regex3, 'success_regex4' : success_regex4, 'success_regex5' : success_regex5, \
                'skip_regex1' : skip_regex1, 'skip_msg1' : skip_msg1, \
                'skip_regex2' : skip_regex2, 'skip_msg2' : skip_msg2, 'skip_regex3' : skip_regex3, 'skip_msg3' : skip_msg3, \
                'skip_regex4' : skip_regex4, 'skip_msg4' : skip_msg4, 'skip_regex5' : skip_regex5, 'skip_msg5' : skip_msg5, \
                'fail_regex1' : fail_regex1, 'fail_msg1' : fail_msg1, \
                'fail_regex2' : fail_regex2, 'fail_msg2' : fail_msg2, 'fail_regex3' : fail_regex3, 'fail_msg3' : fail_msg3, \
                'fail_regex4' : fail_regex4, 'fail_msg4' : fail_msg4, 'fail_regex5' : fail_regex5, 'fail_msg5' : fail_msg5, \
                'exit_cmd' : exit_cmd, \
                'ui_var1_length_min' : ui_var1_length_min, 'ui_var2_length_min' : ui_var2_length_min, \
                'ui_var3_length_min' : ui_var3_length_min, 'ui_var4_length_min' : ui_var4_length_min, \
                'ui_var1_length_max' : ui_var1_length_max, 'ui_var2_length_max' : ui_var2_length_max, \
                'ui_var3_length_max' : ui_var3_length_max, 'ui_var4_length_max' : ui_var4_length_max, \
                'ui_pw1_length_min' : ui_pw1_length_min, 'ui_pw2_length_min' : ui_pw2_length_min, 'ui_pw3_length_min' : ui_pw3_length_min, \
                'ui_pw1_length_max' : ui_pw1_length_max, 'ui_pw2_length_max' : ui_pw2_length_max, 'ui_pw3_length_max' : ui_pw3_length_max, \
                'ui_var1_invalid_characters' : ui_var1_invalid_characters, 'ui_var2_invalid_characters' : ui_var2_invalid_characters, \
                'ui_var3_invalid_characters' : ui_var3_invalid_characters, 'ui_var4_invalid_characters' : ui_var4_invalid_characters, \
                'ui_pw1_invalid_characters' : ui_pw1_invalid_characters, 'ui_pw2_invalid_characters' : ui_pw2_invalid_characters, \
                'ui_pw3_invalid_characters' : ui_pw3_invalid_characters, \
                'ui_var1_length_min_msg' : ui_var1_length_min_msg, 'ui_var2_length_min_msg' : ui_var2_length_min_msg, \
                'ui_var3_length_min_msg' : ui_var3_length_min_msg, 'ui_var4_length_min_msg' : ui_var4_length_min_msg, \
                'ui_var1_length_max_msg' : ui_var1_length_max_msg, 'ui_var2_length_max_msg' : ui_var2_length_max_msg, \
                'ui_var3_length_max_msg' : ui_var3_length_max_msg, 'ui_var4_length_max_msg' : ui_var4_length_max_msg, \
                'ui_pw1_length_min_msg' : ui_pw1_length_min_msg, 'ui_pw2_length_min_msg' : ui_pw2_length_min_msg, 'ui_pw3_length_min_msg' : ui_pw3_length_min_msg, \
                'ui_pw1_length_max_msg' : ui_pw1_length_max_msg, 'ui_pw2_length_max_msg' : ui_pw2_length_max_msg, 'ui_pw3_length_max_msg' : ui_pw3_length_max_msg, \
                'ui_var1_invalid_characters_msg' : ui_var1_invalid_characters_msg, 'ui_var2_invalid_characters_msg' : ui_var2_invalid_characters_msg, \
                'ui_var3_invalid_characters_msg' : ui_var3_invalid_characters_msg, 'ui_var4_invalid_characters_msg' : ui_var4_invalid_characters_msg, \
                'ui_pw1_invalid_characters_msg' : ui_pw1_invalid_characters_msg, 'ui_pw2_invalid_characters_msg' : ui_pw2_invalid_characters_msg, \
                'ui_pw3_invalid_characters_msg' : ui_pw3_invalid_characters_msg, \
                'output_type_dict' : output_type_dict, 'max_result_blocks_override' : max_result_blocks_override, \
                'cmd_dict_list' : cmd_dict_list, 'custom_result_field_list' : custom_result_field_list})

            return 'Success'

        except Exception as err:
            logging.error('Error, getconfigcmds function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, getconfigcmds function, err = ' + str(err)

    def getconfigcmdlist(self, initial_key, keys, branch_list_name):

        try:

            cmd_dict_list = []
            if branch_list_name == 'main':
                 branch_list_suffix = ''
                 branch_list_suffix2 = ''
            else:
                branch_list_suffix = '_' + branch_list_name + '_'
                branch_list_suffix2 = '_' + branch_list_name
            for cmd_index in range(1, 21):

                if initial_key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02'):
                    cmd_dict = {}
                    cmd_dict['cmd' + branch_list_suffix2] = initial_key.childNodes[0].nodeValue

                    cmd_select_regex_list_dict = {}
                    cmd_success_regex_list = []
                    cmd_fail_regex_list = []
                    for key in keys[1]:
                        if key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_expect_prompt_regex':
                            cmd_dict['cmd_expect_prompt_regex'] = key.childNodes[0].nodeValue

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_cli_cmd_delay':
                            cmd_dict['cmd_cli_cmd_delay'] = key.childNodes[0].nodeValue

                            # Validate cmd_cli_cmd_delay from conf file
                            vns = self.validate_num_setting('cmd_cli_cmd_delay', cmd_dict['cmd_cli_cmd_delay'], 5, 5, 120)
                            if vns[0] != "Success":
                                return vns[0]
                            cmd_dict['cmd_cli_cmd_delay'] = vns[1]

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_mode_level':
                            cmd_dict['cmd_mode_level'] = key.childNodes[0].nodeValue

                            # Validate cmd_mode_level from conf file
                            vns = self.validate_num_setting('cmd_mode_level', cmd_dict['cmd_mode_level'], 0, -1, 20)
                            if vns[0] != "Success":
                                return vns[0]
                            cmd_dict['cmd_mode_level'] = vns[1]

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_prompt_regex':
                            cmd_dict['cmd_prompt_regex'] = key.childNodes[0].nodeValue

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_prompt_response_string':
                            cmd_dict['cmd_prompt_response_string'] = key.childNodes[0].nodeValue.strip('"')

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_prompt_response_mode_level':
                            cmd_dict['cmd_prompt_response_mode_level'] = key.childNodes[0].nodeValue

                            # Validate cmd_prompt_response_mode_level from conf file
                            vns = self.validate_num_setting('cmd_prompt_response_mode_level', cmd_dict['cmd_prompt_response_mode_level'], 0, -1, 20)
                            if vns[0] != "Success":
                                return vns[0]
                            cmd_dict['cmd_prompt_response_mode_level'] = vns[1]

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_prompt_override_response_string':
                            cmd_dict['cmd_prompt_override_response_string'] = key.childNodes[0].nodeValue.strip('"')

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_prompt_override_response_mode_level':
                            cmd_dict['cmd_prompt_override_response_mode_level'] = key.childNodes[0].nodeValue

                            # Validate cmd_prompt_override_response_mode_level from conf file
                            vns = self.validate_num_setting('cmd_prompt_override_response_mode_level', cmd_dict['cmd_prompt_override_response_mode_level'], 0, -1, 20)
                            if vns[0] != "Success":
                                return vns[0]
                            cmd_dict['cmd_prompt_override_response_mode_level'] = vns[1]

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_no_config_diff_regex':
                            cmd_dict['cmd_no_config_diff_regex'] = key.childNodes[0].nodeValue

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_max_output_before_truncate':
                            cmd_dict['cmd_max_output_before_truncate'] = key.childNodes[0].nodeValue

                            # Validate cmd_max_output_before_truncate from conf file
                            vns = self.validate_num_setting('cmd_max_output_before_truncate', cmd_dict['cmd_max_output_before_truncate'], 500, 1, 25600)
                            if vns[0] != "Success":
                                return vns[0]
                            cmd_dict['cmd_max_output_before_truncate'] = vns[1]

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_cli_cmd_sleep':
                            cmd_dict['cmd_cli_cmd_sleep'] = key.childNodes[0].nodeValue

                            # Validate cmd_cli_cmd_sleep from conf file
                            vns = self.validate_num_setting('cmd_cli_cmd_sleep', cmd_dict['cmd_cli_cmd_sleep'], 0, 0, 10)
                            if vns[0] != "Success":
                                return vns[0]
                            cmd_dict['cmd_cli_cmd_sleep'] = vns[1]

                        elif key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_send_linefeed':
                            cmd_dict['cmd_send_linefeed'] = key.childNodes[0].nodeValue

                        if 'select' in key.getAttribute('name'):
                            for select_index in range(1, 21):
                                select_sub_list_name = 'select' + format(select_index, '02')
                                select_list_sub_abbrev = '_' + select_sub_list_name + '_'
                                if key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_' + select_sub_list_name:
                                    cmd_dict['cmd' + '_' + select_sub_list_name] = key.childNodes[0].nodeValue
                                    continue
                                for cmd_regex_index in range(1, 21):
                                    if key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + select_list_sub_abbrev + 'regex' + str(cmd_regex_index):
                                        try:
                                            cmd_select_regex_list_dict[select_sub_list_name]
                                        except:
                                            cmd_select_regex_list_dict[select_sub_list_name] = []
                                        cmd_select_regex_list_dict[select_sub_list_name].append(key.childNodes[0].nodeValue)
                                        continue

                        for cmd_regex_index in range(1, 21):
                            if key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_success_regex' + str(cmd_regex_index):
                                cmd_success_regex_list.append(key.childNodes[0].nodeValue)
                                continue

                        for cmd_regex_index in range(1, 21):
                            if key.getAttribute('name') == 'cmd' + branch_list_suffix + format(cmd_index, '02') + '_fail_regex' + str(cmd_regex_index):
                                cmd_fail_regex_list.append(key.childNodes[0].nodeValue)
                                continue

                    cmd_dict['cmd_select_regex_list_dict'] = cmd_select_regex_list_dict
                    cmd_dict['cmd_success_regex_list'] = cmd_success_regex_list
                    cmd_dict['cmd_fail_regex_list'] = cmd_fail_regex_list
                    cmd_dict_list.append(cmd_dict)

            return 'Success', cmd_dict_list

        except Exception as err:
            logging.error('Error, getconfigcmdlist function, err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return 'Error, getconfigcmdlist function, err = ' + str(err), cmd_dict_list

