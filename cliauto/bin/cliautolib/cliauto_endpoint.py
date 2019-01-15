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

# Import cliauto libs
from cliautolib.cliauto_helpers import helpers
from cliautolib.cliauto_access import cliauto_access
from cliautolib.cliauto_pid import pid
from cliauto_configconf import configconf

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

class endpoint(object):

    def __init__(self, in_string, ppid):

        # Processing the request
        try:
            self.response = json.dumps({ 'payload': 'Error, Default endpoint response',
                                         'status': 400  # HTTP status code
                                       })
            logging.info('Starting process_cli_request, endpoint constructor...')
            self.ppid = ppid
            ci = self.process_cli_request(in_string)
            if ci[0] != 'Success':
                self.response = ci[1]
                return None
    
        except Exception as err:
            logging.error('Error, Processing the request, endpoint constructor, err = ' + str(err))
            self.response = json.dumps({ 'payload': 'Error, Processing the request, endpoint constructor, err = ' + str(err),
                                         'status': 500  # HTTP status code
                                      })
            return None

        try:
            # Process cmdtype
            if self.fargs['cmdtype'][:3].lower() == 'cli' or self.fargs['cmdtype'].lower() == 'status' or self.fargs['cmdtype'].lower() == 'lrp':

                # Verify ssh libraries are available
                try:
                    if self.fargs['cmdtype'][:3].lower() == 'cli':
                        import pexpect
                        from pxssh_cliauto import pxssh_cliauto
                        from pxssh_cliauto import ExceptionPxssh
                        from pxssh_cliauto import ExceptionPxsshAccessDenied
                        from pxssh_cliauto import ExceptionPxsshLoginTimeout
                except Exception as err:
                    logging.error("import error; Build and copy the pexpect and ptyprocess package libraries to the bin folder of the cliauto app, err = " + str(err))
                    self.response = json.dumps({ 'payload': 'import error; Build and copy the pexpect and ptyprocess package libraries to the bin folder of the cliauto app',
                                                 'status': 500  # HTTP status code
                                              })
                    return None

                # Verify proper Splunk capability(ies) granted for user to execute a job
                ca = cliauto_access(self.sargs)

                if ca.status != 'Success':
                    self.response = json.dumps({ 'payload': str(ca.status),
                                                 'status': 400  # HTTP status code
                                              })
                    return None

                guc = ca.get_user_capabilities('/services/authentication/users/' + str(self.sargs['user']))
                if guc[0] != 'Success':
                    self.response = json.dumps({ 'payload': str(guc[0]),
                                                 'status': 400  # HTTP status code
                                              })
                    return None

                if 'edit_tcp' not in guc[1]:
                    self.response = json.dumps({ 'payload': 'missing permission for edit_tcp capability',
                                                 'status': 400  # HTTP status code
                                              })
                    return None

                del ca

                # Create configuration object
                self.objcfg = configconf(self.fargs, self.sargs, self.ppid)
                if self.objcfg.status != 'Success':
                    logging.error('Error, creating configconf object, err = ' + str(self.objcfg.status))
                    self.response = json.dumps({ 'payload': 'Error, creating configconf object, err = ' + str(self.objcfg.status),
                                                 'status': 500  # HTTP status code
                                              })
                    return None

                # If getconfig unsuccessful, log errmsg and exit script
                gc = self.objcfg.getconfig()
                if gc != 'Success':
                    logging.error('Error, getconfig function, err = ' + str(gc))
                    self.response = json.dumps({ 'payload': 'Error, getconfig function, err = ' + str(gc),
                                                 'status': 500  # HTTP status code
                                              })
                    return None

                # If cli* cmdtype then check if cmdtype is enabled for cmdtype = cli*, validate user data input, and get hosts file
                if self.fargs['cmdtype'][:3].lower() == 'cli':

                    # Check if cmdtype is enabled for cmdtype = cli*
                    cmdtype_enable = '0'
                    for cmdtype_dict in self.objcfg.cmdtype_dict_list:
                        if self.fargs['cmdtype'].lower() == cmdtype_dict['cmdtype'].lower():
                            cmdtype_dict_current = cmdtype_dict
                            try:
                                cmdtype_enable = cmdtype_dict_current['cmdtype_enable']
                                logging.debug('Found cmdtype: cmdtype_enable = ' + str(cmdtype_enable))
                            except:
                                pass
                            break
                    logging.debug('cmdtype_enable = ' + str(cmdtype_enable))
                    if cmdtype_enable == '0':
                        self.response = json.dumps({ 'payload': 'Bad Request, cmdtype = ' + str(self.fargs['cmdtype'] + ' is not enabled'),
                                                     'status': 400  # HTTP status code
                                                  })
                        return None

                    # Validate user data input for the cli cmdtype
                    vdi = self.invalid_data_input(cmdtype_dict_current)
                    if vdi[0] != 'Success':
                        logging.error('Error, invalid_data_input function, err = ' + str(vdi[0]))
                        self.response = json.dumps({ 'payload': 'Error, invalid_data_input function, err = ' + str(vdi[0]),
                                                     'status': 500  # HTTP status code
                                                  })
                        return None

                    # If invalid user data input exists then return invalid data input
                    if vdi[1]:
                        self.response = json.dumps({ 'payload': 'Bad Request, invalid user input, ' + vdi[2] + ', cmdtype = ' + str(self.fargs['cmdtype']),
                                                     'status': 400  # HTTP status code
                                                  })
                        return None

                    # Get hosts from csv file
                    gh = self.objcfg.get_hosts()
                    if gh != 'Success':
                        logging.error('Error, get_hosts function, err = ' + str(gh))
                        self.response = json.dumps({ 'payload': 'Error, get_hosts function, err = ' + str(gh),
                                                     'status': 500  # HTTP status code
                                                  })
                        return None

                # Create pid object
                opid = pid(self.fargs, self.sargs, self.cargs, self.ppid, self.objcfg)
                self.response = opid.response
                return None

            elif self.fargs['cmdtype'].lower() == 'hb':
                logging.debug('cmdtype=hb')
                self.response = json.dumps({ 'payload': 'Success, Heartbeat received',
                                             'status': 200  # HTTP status code
                                          })
                return None

            else:
                self.response = json.dumps({ 'payload': 'Bad Request, Unknown cmdtype = ' + str(self.fargs['cmdtype']),
                                             'status': 400  # HTTP status code
                                          })
                return None

        except Exception as err:
            logging.error('Error, Starting process, err = ' + str(err))
            self.response = json.dumps({ 'payload': 'Error, CLI: Starting process, err = ' + str(err),
                                         'status': 500  # HTTP status code
                                      })
            return None

        return None

    def in_string(self):
        return self.in_string

    def ppid(self):
        return self.ppid

    def response(self):
        return self.response

    def objcfg(self):
        return self.objcfg

    def fargs(self):
        return self.fargs

    def sargs(self):
        return self.sargs

    def cargs(self):
        return self.cargs

    def parse_in_string(self, in_string):

        # Parse the in_string
        params = json.loads(in_string)

        return params

    def get_forms_args_as_dict(self, form_args):
        
        post_arg_dict = {}

        for arg in form_args:
            name = arg[0]
            value = arg[1]

            post_arg_dict[name] = value

        return post_arg_dict

    def process_cli_request(self, in_string):

        try:
            in_string

        except:
            return ['Bad Request', json.dumps({ 'payload': 'Bad Request, in_string is undefined',
                                                'status': 400  # HTTP status code
                                             })]
        try:
            args = self.parse_in_string(in_string)

        except:
            return ['Bad Request', json.dumps({ 'payload': 'Bad Request, parsing in_string',
                                                'status': 400  # HTTP status code
                                             })]
 
        try:
            self.sargs = args.get('session', [])

        except:
            return ['Bad Request', json.dumps({ 'payload': 'Bad Request, getting session credentials',
                                               'status': 400  # HTTP status code
                                             })]

        try:
            self.cargs = self.get_forms_args_as_dict(args["headers"])

        except:
            return ['Bad Request', json.dumps({ 'payload': 'Bad Request, getting cookies',
                                               'status': 400  # HTTP status code
                                             })]

        # Check if the method = POST (only POST method is supported due to security concerns)
        method = args['method']
        try:
            if method.lower() == 'post':
                fargs = self.get_forms_args_as_dict(args["form"])
            else:
                return ['Bad Request', json.dumps({ 'payload': 'Bad Request, Only POST request method supported',
                                                    'status': 400  # HTTP status code
                                                 })]

        except:
            return ['Bad Request', json.dumps({ 'payload': 'Bad Request, get_forms_args_as_dict',
                                                'status': 400  # HTTP status code
                                             })]

        # Check that the POST form is defined
        try:
            self.fargs = fargs

        except:
            return ['Bad Request', json.dumps({ 'payload': 'Bad Request, form arguments not found in request',
                                                'status': 400  # HTTP status code
                                             })]

        # Check that the POST form arguments are defined
        try:
            if self.fargs['cmdtype'].lower() == 'hb'or self.fargs['cmdtype'].lower() == 'status':
                self.fargs['var1'] = ''
                self.fargs['var2'] = ''
                self.fargs['var3'] = ''
                self.fargs['var4'] = ''
                self.fargs['pw1'] = ''
                self.fargs['pw2'] = ''
                self.fargs['pw3'] = ''
                self.fargs['check1'] = ''
                self.fargs['drop1'] = ''
                self.fargs['suser'] = ''
                self.fargs['spw'] = ''
                self.fargs['nodelist'] = ''
            elif self.fargs['cmdtype'][:3].lower() == 'cli':
                self.fargs['var1']
                self.fargs['var2']
                self.fargs['var3']
                self.fargs['var4']
                self.fargs['pw1']
                self.fargs['pw2']
                self.fargs['pw3']
                self.fargs['check1']
                self.fargs['drop1']
                self.fargs['suser']
                self.fargs['spw']
                self.fargs['nodelist']
            else:
                self.fargs['var1']
                self.fargs['var2']
                self.fargs['var3']
                self.fargs['var4']
                self.fargs['pw1']
                self.fargs['pw2']
                self.fargs['pw3']
                self.fargs['check1']
                self.fargs['drop1']
                self.fargs['suser']
                self.fargs['spw']
                self.fargs['nodelist']

        except Exception as err:
            logging.error('Bad Request, missing required form arguments..., err = ' + str(err))
            return ['Bad Request', json.dumps({ 'payload': 'Bad Request, missing required form arguments, err = ' + str(err),
                                                'status': 400  # HTTP status code
                                             })]

        # Global data input validation of the POST form arguments
        # The initial code geared toward certain use cases
        # JB - 11/30/2018 - replaced global input validation with cmdtype data input validation configuration

        # Checking for session credentials
        logging.info('Checking for session credentials...')
        try:
            self.sargs['user']
            self.sargs['authtoken']
            if self.sargs['authtoken'] == "":
                return ['Bad Request', json.dumps({ 'payload': 'Bad Request, authtoken is empty',
                                                    'status': 400  # HTTP status code
                                                 })]

        except Exception as err:
            logging.error('Bad Request, Checking for session credentials..., err = ' + str(err))
            return ['Bad Request', json.dumps({ 'payload': 'Bad Request, Checking for session credentials..., err = ' + str(err),
                                                'status': 400  # HTTP status code
                                              })]

        logging.info('Exiting process_cli_request with success...')
        return ['Success', json.dumps({ 'payload': 'Success',
                                            'status': 200  # HTTP status code
                                         })]

    def invalid_data_input(self, cmdtype_dict):

        try:

            logging.debug('cmdtype_dict = ' + str(cmdtype_dict))

            # Check for non-UTF8 (ASCII) character in string
            if (self.IsNotUTF8(self.fargs['suser']) or self.IsNotUTF8(self.fargs['spw']) \
            or self.IsNotUTF8(self.fargs['var1']) or self.IsNotUTF8(self.fargs['var2']) \
            or self.IsNotUTF8(self.fargs['var3']) or self.IsNotUTF8(self.fargs['var4']) \
            or self.IsNotUTF8(self.fargs['pw1']) or self.IsNotUTF8(self.fargs['pw2']) \
            or self.IsNotUTF8(self.fargs['pw3'])) or self.IsNotUTF8(self.fargs['check1']) \
            or self.IsNotUTF8(self.fargs['drop1']) or self.IsNotUTF8(self.fargs['nodelist']) \
            or self.IsNotUTF8(self.fargs['suser']) or self.IsNotUTF8(self.fargs['spw']):
                return ['Success', True, 'Only printable UTF8 (ASCII) characters are supported']

            # Initialize min and max length variables
            ui_var1_length_min = cmdtype_dict['ui_var1_length_min']
            ui_var2_length_min = cmdtype_dict['ui_var2_length_min']
            ui_var3_length_min = cmdtype_dict['ui_var3_length_min']
            ui_var4_length_min = cmdtype_dict['ui_var4_length_min']
            ui_var1_length_max = cmdtype_dict['ui_var1_length_max']
            ui_var2_length_max = cmdtype_dict['ui_var2_length_max']
            ui_var3_length_max = cmdtype_dict['ui_var3_length_max']
            ui_var4_length_max = cmdtype_dict['ui_var4_length_max']
            ui_pw1_length_min = cmdtype_dict['ui_pw1_length_min']
            ui_pw2_length_min = cmdtype_dict['ui_pw2_length_min']
            ui_pw3_length_min = cmdtype_dict['ui_pw3_length_min']
            ui_pw1_length_max = cmdtype_dict['ui_pw1_length_max']
            ui_pw2_length_max = cmdtype_dict['ui_pw2_length_max']
            ui_pw3_length_max = cmdtype_dict['ui_pw3_length_max']

            # Initialize invalid character variables
            ui_var1_invalid_characters = cmdtype_dict['ui_var1_invalid_characters']
            ui_var2_invalid_characters = cmdtype_dict['ui_var2_invalid_characters']
            ui_var3_invalid_characters = cmdtype_dict['ui_var3_invalid_characters']
            ui_var4_invalid_characters = cmdtype_dict['ui_var4_invalid_characters']
            ui_pw1_invalid_characters = cmdtype_dict['ui_pw1_invalid_characters']
            ui_pw2_invalid_characters = cmdtype_dict['ui_pw2_invalid_characters']
            ui_pw3_invalid_characters = cmdtype_dict['ui_pw3_invalid_characters']

            # Validate length of vars and pws
            if ui_var1_length_min == None:
                pass
            elif helpers().is_number(ui_var1_length_min):
                if len(self.fargs['var1']) < int(ui_var1_length_min):
                    return ['Success', True, cmdtype_dict['ui_var1_length_min_msg']]
            else:
                return ['Success', True, "ui_var1_length_min is not set to a number"]
            if ui_var2_length_min == None:
                pass
            elif helpers().is_number(ui_var2_length_min):
                if len(self.fargs['var2']) < int(ui_var2_length_min):
                    return ['Success', True, cmdtype_dict['ui_var2_length_min_msg']]
            else:
                return ['Success', True, "ui_var2_length_min is not set to a number"]
            if ui_var3_length_min == None:
                pass
            elif helpers().is_number(ui_var3_length_min):
                if len(self.fargs['var3']) < int(ui_var3_length_min):
                    return ['Success', True, cmdtype_dict['ui_var3_length_min_msg']]
            else:
                return ['Success', True, "ui_var3_length_min is not set to a number"]
            if ui_var4_length_min == None:
                pass
            elif helpers().is_number(ui_var4_length_min):
                if len(self.fargs['var4']) < int(ui_var4_length_min):
                    return ['Success', True, cmdtype_dict['ui_var4_length_min_msg']]
            else:
                return ['Success', True, "ui_var4_length_min is not set to a number"]
            if ui_var1_length_max == None:
                pass
            elif helpers().is_number(ui_var1_length_max):
                if len(self.fargs['var1']) > int(ui_var1_length_max):
                    return ['Success', True, cmdtype_dict['ui_var1_length_max_msg']]
            else:
                return ['Success', True, "ui_var1_length_max is not set to a number"]
            if ui_var2_length_max == None:
                pass
            elif helpers().is_number(ui_var2_length_max):
                if len(self.fargs['var2']) > int(ui_var2_length_max):
                    return ['Success', True, cmdtype_dict['ui_var2_length_max_msg']]
            else:
                return ['Success', True, "ui_var2_length_max is not set to a number"]
            if ui_var3_length_max == None:
                pass
            elif helpers().is_number(ui_var3_length_max):
                if len(self.fargs['var3']) > int(ui_var3_length_max):
                    return ['Success', True, cmdtype_dict['ui_var3_length_max_msg']]
            else:
                return ['Success', True, "ui_var3_length_max is not set to a number"]
            if ui_var4_length_max == None:
                pass
            elif helpers().is_number(ui_var4_length_max):
                if len(self.fargs['var4']) > int(ui_var4_length_max):
                    return ['Success', True, cmdtype_dict['ui_var4_length_max_msg']]
            else:
                return ['Success', True, "ui_var4_length_max is not set to a number"]
            if ui_pw1_length_min == None:
                pass
            elif helpers().is_number(ui_pw1_length_min):
                if len(self.fargs['pw1']) < int(ui_pw1_length_min):
                    return ['Success', True, cmdtype_dict['ui_pw1_length_min_msg']]
            else:
                return ['Success', True, "ui_pw1_length_min is not set to a number"]
            if ui_pw2_length_min == None:
                pass
            elif helpers().is_number(ui_pw2_length_min):
                if len(self.fargs['pw2']) < int(ui_pw2_length_min):
                    return ['Success', True, cmdtype_dict['ui_pw2_length_min_msg']]
            else:
                return ['Success', True, "ui_pw2_length_min is not set to a number"]
            if ui_pw3_length_min == None:
                pass
            elif helpers().is_number(ui_pw3_length_min):
                if len(self.fargs['pw3']) < int(ui_pw3_length_min):
                    return ['Success', True, cmdtype_dict['ui_pw3_length_min_msg']]
            else:
                return ['Success', True, "ui_pw3_length_min is not set to a number"]
            if ui_pw1_length_max == None:
                pass
            elif helpers().is_number(ui_pw1_length_max):
                if len(self.fargs['pw1']) > int(ui_pw1_length_max):
                    return ['Success', True, cmdtype_dict['ui_pw1_length_max_msg']]
            else:
                return ['Success', True, "ui_pw1_length_max is not set to a number"]
            if ui_pw2_length_max == None:
                pass
            elif helpers().is_number(ui_pw2_length_max):
                if len(self.fargs['pw2']) > int(ui_pw2_length_max):
                    return ['Success', True, cmdtype_dict['ui_pw2_length_max_msg']]
            else:
                return ['Success', True, "ui_pw2_length_max is not set to a number"]
            if ui_pw3_length_max == None:
                pass
            elif helpers().is_number(ui_pw3_length_max):
                if len(self.fargs['pw3']) > int(ui_pw3_length_max):
                    return ['Success', True, cmdtype_dict['ui_pw3_length_max_msg']]
            else:
                return ['Success', True, "ui_pw3_length_max is not set to a number"]

            # Check for invalid characters in vars and pws
            if self.containsInvalidChars(self.fargs['var1'], ui_var1_invalid_characters):
                return ['Success', True, cmdtype_dict['ui_var1_invalid_characters_msg']]
            if self.containsInvalidChars(self.fargs['var2'], ui_var2_invalid_characters):
                return ['Success', True, cmdtype_dict['ui_var2_invalid_characters_msg']]
            if self.containsInvalidChars(self.fargs['var3'], ui_var3_invalid_characters):
                return ['Success', True, cmdtype_dict['ui_var3_invalid_characters_msg']]
            if self.containsInvalidChars(self.fargs['var4'], ui_var4_invalid_characters):
                return ['Success', True, cmdtype_dict['ui_var4_invalid_characters_msg']]
            if self.containsInvalidChars(self.fargs['pw1'], ui_pw1_invalid_characters):
                return ['Success', True, cmdtype_dict['ui_pw1_invalid_characters_msg']]
            if self.containsInvalidChars(self.fargs['pw2'], ui_pw2_invalid_characters):
                return ['Success', True, cmdtype_dict['ui_pw2_invalid_characters_msg']]
            if self.containsInvalidChars(self.fargs['pw3'], ui_pw3_invalid_characters):
                return ['Success', True, cmdtype_dict['ui_pw3_invalid_characters_msg']]

            # Check vars and pws lengths greater than default_input_data_length_max for unset max lengths (i.e. guard against buffer overflow)
            if len(self.fargs['var1']) > self.objcfg.default_input_data_length_max and ui_var1_length_max == None:
                return ['Success', True, 'var1 length  > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['var2']) > self.objcfg.default_input_data_length_max and ui_var1_length_max == None:
                return ['Success', True, 'var2 length  > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['var3']) > self.objcfg.default_input_data_length_max and ui_var1_length_max == None:
                return ['Success', True, 'var3 length  > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['var4']) > self.objcfg.default_input_data_length_max and ui_var1_length_max == None:
                return ['Success', True, 'var4 length  > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['pw1']) > self.objcfg.default_input_data_length_max and ui_var1_length_max == None:
                return ['Success', True, 'pw1 length  > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['pw2']) > self.objcfg.default_input_data_length_max and ui_var1_length_max == None:
                return ['Success', True, 'pw2 length  > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['pw3']) > self.objcfg.default_input_data_length_max and ui_var1_length_max == None:
                return ['Success', True, 'pw3 length  > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']

            # Check check1, drop1, nodelist, suser, and spw lengths greater than default_input_data_length_max (i.e. guard against buffer overflow)
            if len(self.fargs['check1']) > self.objcfg.default_input_data_length_max:
                return ['Success', True, 'check1 > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['drop1']) > self.objcfg.default_input_data_length_max:
                return ['Success', True, 'drop1 > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['nodelist']) > self.objcfg.default_input_data_length_max:
                return ['Success', True, 'nodelist > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['suser']) > self.objcfg.default_input_data_length_max:
                return ['Success', True, 'suser > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']
            if len(self.fargs['spw']) > self.objcfg.default_input_data_length_max:
                return ['Success', True, 'spw > default_input_data_length_max(' + str(self.objcfg.default_input_data_length_max) +')']

            # Check vars and pws lengths greater than absolute_input_data_length_max (i.e. guard against buffer overflow)
            if len(self.fargs['var1']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'var1 length  > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['var2']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'var2 length  > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['var3']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'var3 length  > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['var4']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'var4 length  > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['pw1']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'pw1 length  > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['pw2']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'pw2 length  > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['pw3']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'pw3 length  > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']

            # Check check1, drop1, nodelist, suser, and spw lengths greater than absolute_input_data_length_max (i.e. guard against buffer overflow)
            if len(self.fargs['check1']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'check1 > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['drop1']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'drop1 > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['nodelist']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'nodelist > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['suser']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'suser > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']
            if len(self.fargs['spw']) > self.objcfg.absolute_input_data_length_max:
                return ['Success', True, 'spw > absolute_input_data_length_max(' + str(self.objcfg.absolute_input_data_length_max) +')']

            return ['Success', False, 'Input validated']

        except Exception as err:
            logging.error('Error, invalid_data_input function..., err = ' + str(err))
            logging.error('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return ['Error', True, 'Error, invalid_data_input function..., err = ' + str(err)]

    def containsInvalidChars(self, istr, chars):

        # If a starting double quote exists, remove it
        if chars[:1] == '"':
            chars = chars[1:]

        # If an ending double quote exists, remove it
        if chars[:-1] == '"':
            chars = chars[:-1]

        # Loop through chars to check for invalid characters in istr
        for char in chars:
            for istrc in istr:
                if char == istrc:
                    return True

        return False

    # Check for non-UTF8 (ASCII) character in string
    def IsNotUTF8(self, istr):
        charcode = 0
        for istrc in istr:
            charcode = ord(istrc)
            if((charcode < 32) or (charcode > 126)):
                return True

        return False

    def flatten_query_params(params):
        # Query parameters are provided as a list of pairs and can be repeated, e.g.:
        #
        #   "query": [ ["arg1","val1"], ["arg2", "val2"], ["arg1", val2"] ]
        #
        # This function simply accepts only the first parameter and discards duplicates and is not intended to provide an
        # example of advanced argument handling.
        flattened = {}
        for i, j in params:
            flattened[i] = flattened.get(i) or j
        return flattened
