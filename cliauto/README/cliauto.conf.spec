# This file describes the cliauto_cmds.conf file that is included
# with the CLI Auto for Splunk app.
# 
# cliauto.conf is meant to correspond with default/cliauto_cmds.conf
#
# Modifying either of these files incongruently will affect the CLI (ssh) sessions 
# functionality
#

# ---- Main Stanza ----
# Contains global variables for the app.

[main]
index =  <index string>
* Splunk index to store results

sourcetype = <sourcetype string>
* Sourcetpye to store results to the Splunk index

source = <source string>
* Source to store results to the Splunk index

ConnectRetries = <number of ssh connect retries>
* Set the <number of ssh connect retries>. Min = 0, Max = 10.

ConnectTimeout = <time in seconds>
* Set the ConnectTimeout(seconds) option for ssh login. Min = 15, Max = 600.

SocketRetries = <number of socket connect retries>
* Set the number of socket retries. Min = 0, Max = 10.

SocketTimeout = <time in seconds>
* Set the SocketTimeout(seconds) option to check if port is open. Min = 0, Max = 10. 0 disables port check

sshport = <port number>
* Set the port for ssh command. Min = 1, Max = 65535.

cipher = <comma seperated values string of ciphers>
* Set the cipher (ssh) required by the various node types
* Sonicwall v6.1.x firmware of test firewall required 3des-cbc
* If a cipher that is not supported by your version of Openssh client is in this key/value, Openssh client will get an error and cliauto job will fail.
* Execute "ssh -Q cipher" to get supported ciphers of Openssh client
* The supported ciphers of Openssh client vary with Openssh versions

StrictHostKeyChecking = <"yes | "no">
* StrictHostKeyChecking option for ssh connection to nodes

HostKeyAlgorithms = <comma seperated values string of HostKeyAlgorithms>
* HostKeyAlgorithms option for ssh connection to nodes
* ecdsa-sha2-nistp256 included for CentOS 7 ssh client (for testing cli_custom cmdtpye)

KexAlgorithms = <comma seperated values string of KexAlgorithms>
* KexAlgorithms option for ssh connection to nodes

PreferredAuthentications = <gssapi-with-mic, hostbased, publickey, keyboard-interactive, password>
* PreferredAuthentications option for ssh connection to nodes

MaxThreads= <maximum number of threads>
* Max Number of threads (hosts) for each parallel iteration
* A value of 75 is recommended for average resources available on the machine executing script
* The absolute maximum is 100 (i.e. MaxThreads > 100 is set to MaxThreads=100)
* To execute commands serially instead in parallel, set value to 1. Min = 1, Max = 75.

HBTimeout = <number of seconds>
* The Splunk Custom REST API (cliauto - running in persistent mode) python process life cycle ends after 1-2 minutes
* without any calls to it. A heartbeat call (cmdtype=hb) is made after HBTimeout (seconds) while processing each
* iteration and at the beginning of each iteration.
* It is recommended that HBTimeout be 10 (10 seconds). Min = 10, Max = 50.

pid_history_days = <number of days>
* The cliauto_pid_collection KVStore stores the job/pid history.
* The pid_history_days setting is the number of days to keep the this history. Min = 1, Max = 365.

max_host_count = <maximum number of hosts>
* The <maximum number of hosts> that are processed in a Node List file. Min = 1, Max = 5000. 

max_result_blocks = <maximum number of blocks>
* The <maximum number of blocks> in each result (1 block = 1 KB or 1024 bytes). Min = 1, Max = 10.

IterationTimeout = <time in seconds>
* Iteration timeout is max time to allow for one iteration to process. Min = 300, Max = 600.

cli_cmd_delay = <time in seconds>
* CLI command delay to expect output of command. Min = 1, Max = 60
* cli_cmd_delay can be overriden by cmd<1-20>_cli_cmd_delay in the default/cliauto_cmds.conf file

ui_job_rows = <number of jobs>
* UI <number of jobs> (rows) in history to display from KVStore table.

default_input_data_length_max = <number of characters>
* Default max length of data input strings of Custom REST API. Min = 1, Max = 1000.

absolute_input_data_length_max = <number of characters>
* Absolute max length of data input strings of Custom REST API. Min = 1, Max = 2000.

allow_duplicate_ip_address = <no | yes>
* Allow duplicate ip address in node list

kex_verbose_level = <0 | 1 | 2 | 3>
* ssh key exchange verbose level for the "Check ssh Key Exchange" command type

kex_filter_regex = <regular expression>
* ssh key exchange regex filter for the "Check ssh Key Exchange" command type

ui_job_rows = <number of jobs>
* UI <number of jobs> (rows) in history to display from KVStore table.

ui_jobid_title = <short description>
* UI Job ID title (tooltip)

ui_nodelist_title = <short description>
* UI NodeList title (tooltip)

ui_status_title = <short description>
* UI Status title (tooltip)

ui_pid_title = <short description>
* UI PID title (tooltip)

ui_timestamp_title = <short description>
* UI Timestamp title (tooltip)

ui_command_title = <short description>
* UI Command title (tooltip)

ui_starttime_title = <short description>
* UI Starttime title (tooltip)

ui_endtime_title = <short description>
* UI Endtime title (tooltip)

ui_scriptuser_title = <short description>
* UI Script User title (tooltip)

ui_sessionuser_title = <short description>
* UI Session User title (tooltip)

ui_hostcount_title = <short description>
* UI Host Count title (tooltip)
