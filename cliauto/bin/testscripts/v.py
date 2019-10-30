from __future__ import absolute_import
import sys, os
os.environ['PYTHONHTTPSVERIFY'] = '0'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import pdb
import time

try:

    python_version = ''

    # Get Python version
    python_version = sys.version
    python_version = python_version.replace('\n',' ')
    python_version = python_version.replace('\r',' ')

except Exception as err:
    python_version = str(err)

try:

    splunklib_python_version = ''

    # Get Splunk Python SDK version
    import splunklib
    splunklib_python_version = splunklib.__version__

except Exception as err:
    splunklib_python_version = str(err)

try:

    pexpect_version = ''

    # Get pexpect version
    import pexpect
    pexpect_version = pexpect.__version__

except Exception as err:
    pexpect_version = str(err)

try:

    ptyprocess_version = ''

    # Get ptyprocess version
    import ptyprocess
    ptyprocess_version = ptyprocess.__version__

except Exception as err:
    ptyprocess_version = str(err)

print ('python_version = ' + str(python_version))
print ('splunklib_python_version = ' + str(splunklib_python_version))
print ('pexpect_version = ' + str(pexpect_version))
print ('ptyprocess version = ' + str(ptyprocess_version))

sys.exit()

pdb.set_trace()

