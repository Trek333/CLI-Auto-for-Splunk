from pexpect import pxssh
from pexpect import ExceptionPexpect, TIMEOUT, EOF, spawn
import time
import os
import sys
import re
import logging

# Log file location /opt/splunk/var/log/splunk/cliauto.log
# CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10, NOTSET = 0
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logconfpath = os.sep.join([os.environ['SPLUNK_HOME'], 'etc', 'apps', 'cliauto', 'default', 'logger.conf'])
logging.config.fileConfig(logconfpath, defaults={'logfilename': logfile})

# [JB] - copied
class ExceptionPxssh(ExceptionPexpect):
    '''Raised for pxssh exceptions.
    '''

# [JB] - added specific exception for Access Denied
class ExceptionPxsshAccessDenied(ExceptionPexpect):
    '''Raised for pxssh exceptions.
    '''

# [JB] - added specific exception for Login Timeout
class ExceptionPxsshLoginTimeout(ExceptionPexpect):
    '''Raised for pxssh exceptions.
    '''

class pxssh_cliauto(pxssh.pxssh):

# [JB] - The pxssh login function was overridden due to incompatibility with Sonicwall, Checkpoint, and Palo Alto firewalls
# - changes made based on pexpect version 4.6.0 and firewalls flavors available for testing
# - added cipher and access_denied_regex variables
# - added code to disable second check for password prompt
#    def login (self, server, username, password='', terminal_type='ansi',
#                original_prompt=r"[#$]", login_timeout=10, port=None,
#                auto_prompt_reset=True, ssh_key=None, quiet=True,
#                sync_multiplier=1, check_local_ip=True,
#                password_regex=r'(?i)(?:password:)|(?:passphrase for key)',
#                ssh_tunnels={}, spawn_local_ssh=True,
#                sync_original_prompt=True, ssh_config=None):

    def login (self, server, username, password='', terminal_type='ansi',
                original_prompt=r"[#$]", login_timeout=10, port=None,
                auto_prompt_reset=True, ssh_key=None, quiet=True,
                sync_multiplier=1, check_local_ip=True,
                password_regex=r'(?i)(?:password:)|(?:passphrase for key)',
                ssh_tunnels={}, spawn_local_ssh=True,
                sync_original_prompt=True, ssh_config=None,
                cipher=None, access_denied_regex="(?i)access denied|(?i)permission denied"):
        '''This logs the user into the given server.

        It uses
        'original_prompt' to try to find the prompt right after login. When it
        finds the prompt it immediately tries to reset the prompt to something
        more easily matched. The default 'original_prompt' is very optimistic
        and is easily fooled. It's more reliable to try to match the original
        prompt as exactly as possible to prevent false matches by server
        strings such as the "Message Of The Day". On many systems you can
        disable the MOTD on the remote server by creating a zero-length file
        called :file:`~/.hushlogin` on the remote server. If a prompt cannot be found
        then this will not necessarily cause the login to fail. In the case of
        a timeout when looking for the prompt we assume that the original
        prompt was so weird that we could not match it, so we use a few tricks
        to guess when we have reached the prompt. Then we hope for the best and
        blindly try to reset the prompt to something more unique. If that fails
        then login() raises an :class:`ExceptionPxssh` exception.

        In some situations it is not possible or desirable to reset the
        original prompt. In this case, pass ``auto_prompt_reset=False`` to
        inhibit setting the prompt to the UNIQUE_PROMPT. Remember that pxssh
        uses a unique prompt in the :meth:`prompt` method. If the original prompt is
        not reset then this will disable the :meth:`prompt` method unless you
        manually set the :attr:`PROMPT` attribute.
        
        Set ``password_regex`` if there is a MOTD message with `password` in it.
        Changing this is like playing in traffic, don't (p)expect it to match straight
        away.
        
        If you require to connect to another SSH server from the your original SSH
        connection set ``spawn_local_ssh`` to `False` and this will use your current
        session to do so. Setting this option to `False` and not having an active session
        will trigger an error.
        
        Set ``ssh_key`` to a file path to an SSH private key to use that SSH key
        for the session authentication.
        Set ``ssh_key`` to `True` to force passing the current SSH authentication socket
        to the desired ``hostname``.
        
        Set ``ssh_config`` to a file path string of an SSH client config file to pass that
        file to the client to handle itself. You may set any options you wish in here, however
        doing so will require you to post extra information that you may not want to if you
        run into issues.
        '''
        #[JB] - added line below due to Sonicwall password prompt difference in 6.1.x vs 6.2.x and access denied regex is not a option variable
        #session_regex_array = ["(?i)are you sure you want to continue connecting", original_prompt, password_regex, "(?i)permission denied", "(?i)terminal type", TIMEOUT]
        session_regex_array = ["(?i)are you sure you want to continue connecting", original_prompt, password_regex, access_denied_regex, "(?i)terminal type", TIMEOUT]
        session_init_regex_array = []
        session_init_regex_array.extend(session_regex_array)
        session_init_regex_array.extend(["(?i)connection closed by remote host", EOF])

        ssh_options = ''.join([" -o '%s=%s'" % (o, v) for (o, v) in self.options.items()])
        if quiet:
            ssh_options = ssh_options + ' -q'
        if not check_local_ip:
            ssh_options = ssh_options + " -o'NoHostAuthenticationForLocalhost=yes'"
        if self.force_password:
            ssh_options = ssh_options + ' ' + self.SSH_OPTS
        if ssh_config is not None:
            if spawn_local_ssh and not os.path.isfile(ssh_config):
                raise ExceptionPxssh('SSH config does not exist or is not a file.')
            ssh_options = ssh_options + '-F ' + ssh_config
        if port is not None:
            ssh_options = ssh_options + ' -p %s'%(str(port))
        if ssh_key is not None:
            # Allow forwarding our SSH key to the current session
            if ssh_key==True:
                ssh_options = ssh_options + ' -A'
            else:
                if spawn_local_ssh and not os.path.isfile(ssh_key):
                    raise ExceptionPxssh('private ssh key does not exist or is not a file.')
                ssh_options = ssh_options + ' -i %s' % (ssh_key)
        
        # SSH tunnels, make sure you know what you're putting into the lists
        # under each heading. Do not expect these to open 100% of the time,
        # The port you're requesting might be bound.
        #
        # The structure should be like this:
        # { 'local': ['2424:localhost:22'],  # Local SSH tunnels
        # 'remote': ['2525:localhost:22'],   # Remote SSH tunnels
        # 'dynamic': [8888] } # Dynamic/SOCKS tunnels
        if ssh_tunnels!={} and isinstance({},type(ssh_tunnels)):
            tunnel_types = {
                'local':'L',
                'remote':'R',
                'dynamic':'D'
            }
            for tunnel_type in tunnel_types:
                cmd_type = tunnel_types[tunnel_type]
                if tunnel_type in ssh_tunnels:
                    tunnels = ssh_tunnels[tunnel_type]
                    for tunnel in tunnels:
                        if spawn_local_ssh==False:
                            tunnel = quote(str(tunnel))
                        ssh_options = ssh_options + ' -' + cmd_type + ' ' + str(tunnel)
        #[JB] - added cipher option for ssh
        #cmd = "ssh %s -l %s %s" % (ssh_options, username, server)
        if cipher!=None:
            cmd = "ssh %s -c %s -l %s %s" % (ssh_options, cipher, username, server)
        else:
            cmd = "ssh %s -l %s %s" % (ssh_options, username, server)
        if self.debug_command_string:
            return(cmd)

        # Are we asking for a local ssh command or to spawn one in another session?
        if spawn_local_ssh:
            spawn._spawn(self, cmd)
        else:
            self.sendline(cmd)

        # This does not distinguish between a remote server 'password' prompt
        # and a local ssh 'passphrase' prompt (for unlocking a private key).
        i = self.expect(session_init_regex_array, timeout=login_timeout)
        # First phase
        if i==0:
            # New certificate -- always accept it.
            # This is what you get if SSH does not have the remote host's
            # public key stored in the 'known_hosts' cache.
            self.sendline("yes")
            #[JB] - added timeout variable to expect functions due to inconsistent timeout behavior & Sonicwall login banner behavior differences for several firewalls (extended time to receive "Access denied" message)
            #i = self.expect(session_regex_array)
            i = self.expect(session_regex_array, timeout=login_timeout)
        if i==2: # password or passphrase
            self.sendline(password)
            #[JB] - added line below due to Sonicwall login banner and password prompt difference in 6.1.x vs 6.2.x 
            session_regex_array = ["(?i)are you sure you want to continue connecting", original_prompt, "do not check for password prompt again and update access denied string", access_denied_regex, "(?i)terminal type", TIMEOUT]
            #[JB] - added timeout variable to expect functions due to inconsistent timeout behavior & Sonicwall login banner behavior differences for several firewalls (extended time to receive "Access denied" message)
            #i = self.expect(session_regex_array)
            i = self.expect(session_regex_array, timeout=login_timeout)
        if i==4:
            self.sendline(terminal_type)
            #[JB] - added timeout variable to expect functions due to inconsistent timeout behavior & Sonicwall login banner behavior differences for several firewalls (extended time to receive "Access denied" message)
            #i = self.expect(session_regex_array)
            i = self.expect(session_regex_array, timeout=login_timeout)
        if i==7:
            self.close()
            raise ExceptionPxssh('Could not establish connection to host')

        # Second phase
        if i==0:
            # This is weird. This should not happen twice in a row.
            self.close()
            raise ExceptionPxssh('Weird error. Got "are you sure" prompt twice.')
        elif i==1: # can occur if you have a public key pair set to authenticate.
            ### TODO: May NOT be OK if expect() got tricked and matched a false prompt.
            pass
        elif i==2: # password prompt again
            # For incorrect passwords, some ssh servers will
            # ask for the password again, others return 'denied' right away.
            # If we get the password prompt again then this means
            # we didn't get the password right the first time.
            self.close()
            raise ExceptionPxssh('password refused')
        elif i==3: # permission denied -- password was bad.
            self.close()
            #[JB] - added specific exception for Access Denied
            #raise ExceptionPxssh('permission denied')
            raise ExceptionPxsshAccessDenied('access denied')
        elif i==4: # terminal type again? WTF?
            self.close()
            raise ExceptionPxssh('Weird error. Got "terminal type" prompt twice.')
        elif i==5: # Timeout
            #This is tricky... I presume that we are at the command-line prompt.
            #It may be that the shell prompt was so weird that we couldn't match
            #it. Or it may be that we couldn't log in for some other reason. I
            #can't be sure, but it's safe to guess that we did login because if
            #I presume wrong and we are not logged in then this should be caught
            #later when I try to set the shell prompt.

            #[JB] - added timeout variable to expect functions due to inconsistent timeout behavior & Sonicwall login banner behavior differences for several firewalls (extended time to receive "Access denied" message)
            #pass - [JB] - not commented in parent function
            #raise ExceptionPxssh('timeout') - [JB] - commented in parent function; strange that the close function was after the raise exception command in parent, but both lines are commented
            #self.close() - [JB] - commented in parent function; strange that the close function was after the raise exception command in parent, but both lines are commented
            self.close()
            raise ExceptionPxsshLoginTimeout('timeout')

        elif i==6: # Connection closed by remote host
            self.close()
            raise ExceptionPxssh('connection closed')
        else: # Unexpected
            self.close()
            raise ExceptionPxssh('unexpected login response')
        if sync_original_prompt:
            if not self.sync_original_prompt(sync_multiplier):
                self.close()
                raise ExceptionPxssh('could not synchronize with original prompt')
        # We appear to be in.
        # set shell prompt to something unique.
        if auto_prompt_reset:
            if not self.set_unique_prompt():
                self.close()
                raise ExceptionPxssh('could not set shell prompt '
                                     '(received: %r, expected: %r).' % (
                                         self.before, self.PROMPT,))
        return True

