from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import re
import json
import logging
from logging.config import fileConfig
import time
import errno
import glob

# Append directory of this file to the Python path (sys.path) to be able to import cliauto libs
if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

class helpers(object):

    def __init__(self):
        a = 0

    def process_request(self, args):

        process_request_dict = {}

        # Get the user information
        process_request_dict[session_key] = args['session']['authtoken']

        return process_request_dict

    def convert_to_dict(self, query):
        """
        Create a dictionary containing the parameters.
        """
        parameters = {}

        for key, val in query:

            # If the key is already in the list, but the existing entry isn't a list then make the
            # existing entry a list and add thi one
            if key in parameters and not isinstance(parameters[key], list):
                parameters[key] = [parameters[key], val]

            # If the entry is already included as a list, then just add the entry
            elif key in parameters:
                parameters[key].append(val)

            # Otherwise, just add the entry
            else:
                parameters[key] = val

        return parameters

    def fileexists(self, fname):

        # Check/read config file
        if os.path.isfile(fname):
            return True
        else:
            return False

    def direxists(self, dirname):

        if os.path.isdir(dirname):
            return True
        else:
            return False

    def filedel(self, fname):

        if self.fileexists(fname):
            os.remove(fname)
            return True
        else:
            return False

    def filedelall(self, dirname):

        if self.direxists(dirname):
            files = glob.glob(dirname + '/*')
            for f in files:
                os.remove(f)
            return True
        else:
            return False


    def is_number(self,s):
        try:
            if s == None:
                return False
            int(s)
            return True
        except ValueError:
            return False

    def split(self, arr, size):
        arrs = []
        while len(arr) > size:
            pice = arr[:size]
            arrs.append(pice)
            arr   = arr[size:]
        arrs.append(arr)
        return arrs

    def getfilecontents(self, fname):
        if self.fileexists(fname):
            f = open(fname, "r")
            return f.readline()
        else:
            return ""

    def is_pid_in_file_and_exists(self, fname):
        if self.fileexists(fname):
            fcontents = self.getfilecontents(fname)
            spid = fcontents
            if self.is_number(int(spid)):
                if self.pid_exists(int(spid)):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def create_pid_file(self, dirname, pid):
        if self.direxists(dirname):
            try:
                fpath = dirname + '/' + pid
                f = open(fpath, "w")
                f.write(str(pid))
                return False
            except:
                return True
        else:
            return True

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

    def getfiles(self, dirpath):
        a = [s for s in os.listdir(dirpath)
            if os.path.isfile(os.path.join(dirpath, s))]
        a.sort(key=lambda s: os.path.getmtime(os.path.join(dirpath, s)), reverse=True)
        return a

    def top_pid_file(self, pid_dir):
        fl = self.getfiles(pid_dir)
        for f in fl:
            if self.is_number(f):
                return str(f)
        return ""

    def pid_active(self, pid_dir):

        # If the most recent PID file name is running, return True; otherwise return False & delete all files in PID folder
        try:
            if self.direxists(pid_dir):
               pid_fname = self.top_pid_file(pid_dir)
            else:
               return [True, 'Error, pid_dir does not exist; pid_dir = ' + pid_dir]

        except Exception as err:
            return [True, 'Error, top_pid_file or direxists function, err = ' + str(err) + '; pid_dir = ' + pid_dir]

        try:
            if self.is_number(pid_fname):
                pid = int(pid_fname)
                if self.pid_exists(pid):
                    return [True, 'Busy, pid exists; pid = ' + str(pid)]
                else:
                    fdr = self.filedelall(pid_dir)
                    return [False, 'Success, pid = ' + str(pid)]
            else:
                fdr = self.filedelall(pid_dir)
                return [False, 'Success, pid does not exist; pid_fname = ' + str(pid_fname)]

        except Exception as err:
            fdr = self.filedelall(pid_dir)
            return [True, 'Error, pid does not exist; err = ' + str(err)]


