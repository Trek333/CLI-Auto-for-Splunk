# This file describes the cliauto_cmds.conf file that is included
# with the CLI Auto for Splunk app.
# 
# cliauto_cmds.conf is meant to correspond with default/cliauto.conf
#
# Modifying either of these files incongruently will affect the CLI (ssh) sessions 
# functionality
#

# ---- Command Type Templates ----
# Each stanza contains the configuration of a Command Type (a set of CLI commands that
# is executed during a CLI (ssh) session) for a selected Node List of a submitted 
# job. The default/cliauto.conf is related since it contains global settings for the
# app.

[<cmdtype>]
cmdtype_enable = <no | yes>
* A value of no disables the cmdtype (not an option in the Script Command drop down)
* A value of yes enables the cmdtype (an option in the Script Command drop down)

output_line_delimiter = <delimiter string>
* A <delimiter string> to replace line separator characters

kv_cmd_string = <short description>
* A <short description> (human readable) of the cmd type that displayed in the Script Command drop down and the Command field of the KVStore history table

ui_cmdtype_title = <short description>
* UI Command Type title (tooltip)

ui_nodelist_title = <short description>
* UI Node List title (tooltip)

ui_suser_label = <short description>
* If specified, the Script User input field is displayed on UI for input
* A <short description> for the Script User input field

ui_suser_placeholder = <short description>
* A <short description> for the Script User input field inside the component

ui_suser_title = <short description>
* UI Script User title (tooltip)

ui_spw_label = <short description>
* If specified, the Script Password input field is displayed on UI for input
* A <short description> for the Script Password input field

ui_spw_title = <short description>
* UI Script Password title (tooltip)

ui_spw_placeholder = <short description>
* A <short description> for the Script Password input field inside the component

ui_var<1-4>_label = <short description>
* If specified, the var<1-4) input field is displayed on UI for input
* A <short description> for the var<1-4> input field

ui_var<1-4>_title = <short description>
* UI var<1-4> title (tooltip)

ui_var<1-4>_placeholder = <short description>
* A <short description> for the var<1-4> input field inside the component

ui_pw<1-3>_label = <short description>
* If specified, the pw<1-3> input field is displayed on UI for input
* A <short description> for the pw<1-3> input field

ui_var<1-4>_title = <short description>
* UI pw<1-4> title (tooltip)

ui_pw<1-3>_placeholder = <short description>
* A <short description> for the pw<1-3> input field inside the component

ui_general_msg = <short description>
* If specified, a text message is displayed on UI near var(s).
* The intended use is to display the Script Command delimiter for Custom Command Type.

ui_drop1_label = <short description>
* If specified, the ui_drop1 input component is displayed on UI for input
* A <short description> for the ui_drop1 input component

ui_drop1_title = <short description>
* UI drop1 title (tooltip)

ui_drop1_options = <command seperated value string>
* A <command seperated value string> of the options for the ui_drop1 input component

ui_check1_label = <short description>
* If specified, the ui_check1 input component is displayed on UI for input
* A <short description> for the ui_check1 input component

ui_check1_msg = <short description>
* If specified, a text message is displayed on UI near ui_check1.
* The intended use is to display a warning message for the ui_check1.

ui_drop1_not_empty = <no | yes>
* Input validation initially intended to verify drop1 dropdown is not empty

ui_drop1_not_empty_msg=Please enter user group
* The error message displayed for failure of ui_drop1_not_empty validation

ui_var<1-4>_length_min = <integer>
* Input validation for minimum variable length

ui_var<1-4>_length_min_msg=<short description>
* The error message displayed for ui_var<1-4>_length_min condition

ui_var<1-4>_length_max = <integer>
* Input validation for maximum variable length

ui_var<1-4>_length_max_msg=<short description>
* The error message displayed for ui_var<1-4>_length_max condition

ui_pw<1-3>_length_min = <integer>
* Input validation for minimum password length

ui_pw<1-3>_length_min_msg=<short description>
* The error message displayed for ui_pw<1-3>_length_min condition

ui_pw<1-3>_length_max = <integer>
* Input validation for maximum password length

ui_pw<1-3>_length_max_msg=<short description>
* The error message displayed for ui_pw<1-3>_length_max condition

ui_var<1-4>_invalid_characters = <integer>
* Input validation for invalid characters

ui_var<1-4>_invalid_characters_msg = <short description>
* The error message displayed for ui_var<1-4>_invalid_characters condition

ui_pw<1-3>_invalid_characters = <integer>
* Input validation for invalid characters

ui_pw<1-3>_invalid_characters_msg = <short description>
* The error message displayed for ui_pw<1-3>_invalid_characters condition

ui_pw<1-3>_match_string = <match string>
* Input validation to prevent invalid substrings for passwords
* The initial intent of this input validation is to prevent CLI commands from being used as a password

ui_pw<1-3>_match_string_msg = <short description>
* The error message displayed for ui_pw<1-3>_match_string condition

ui_val_equal = <comma seperated values string each value contains equation|short description>
* Input validation equality initially intended to verify password and confirm password values are equal
* Example: pw1=pw2|Password and confirm password do not match,var1=var2|var1 and var2 do not match

expect_prompt_regex = <regular expression>
* Specifies the <regular expression> of the prompt after each CLI command.

default_fail_msg = <short description>
* The default fail <short description> for the outcome each node's result for job

find_regex<1-5> = <regular expression>
success_regex<1-5> = <regular expression>
success_msg<1-5> = <short description>
* If find_regex<1-5> is specified, the raw ouput of each node's job is searched for a string matching the <regular expression>. If a match is found, the match string is searched for the <regular expression> of the corresponding success_regex<1-5> variable. If a match is found, the resultstatus is populated with "Success" and the corresponding success_msg<1-5> is used to populate the result.

skip_regex<1-5> = <regular expression>
skip_msg<1-5> = <short description>
* If skip_regex<1-5> is specified, the raw ouput of each node's job is searched for a string matching the <regular expression>. If a match is found, the resultstatus is populated with "Skip" and the corresponding skip_msg<1-5> is used to populate the result.

fail_regex<1-5> = <regular expression>
fail_msg<1-5> = <short description>
* If the result was not a "Success", the raw ouput of each node's job is searched for a string matching the fail_regex<1-5>'s <regular expression>. If a match is found, the fail_msg <1-5>'s <short description> is used for the result. Otherwise, the default_fail_msg <short description> is used for the result.

exit_cmd = <command string>
* The <command string> for the node type to drop one mode level.

cmd<1-20> = <command>
cmd_branch<1-20>_<1-20> = <command>
* If specified, the <command> is executed in the CLI (ssh) session

cmd<1-20>_send_linefeed = <no | yes>
cmd_branch<1-20>_<1-20>_send_linefeed = <no | yes>
* If specified with a value of yes, the pexpect sendline method is executed for the CLI command in the CLI (ssh) session
* If specified with a value of no, the pexpect send method is executed for the CLI command in the CLI (ssh) session
* Default value is yes

cmd<1-20>_mode_level = <integer level>
cmd_branch<1-20>_<1-20>_mode_level = <integer level>
* The <integer level> is an integer that indicates the mode level of the CLI (ssh) session after the corresponding cmd<1-20> executes successfully.

cmd<1-20>_select<1-20> = <branch string>
cmd<1-20>_select<1-20>_regex<1-20> = <regular expression>
* The raw result of the cmd<1-20> is searched for the <regular expression>. If found, the CLI command execution path is diverted to the set of CLI commands starting at cmd_<branch string>_01.

cmd<1-20>_success_regex<1-20> = <regular expression>
cmd_branch<1-20>_<1-20>_success_regex<1-20> = <regular expression>
* The raw result of the cmd<1-20> is searched for the <regular expression>. If found, the cmd<1-20> is marked a success pending processing of the cmd<1-20>_fail_regex<1-20>.

cmd<1-20>_fail_regex<1-20> = <regular expression>
cmd_branch<1-20>_<1-20>_fail_regex<1-20> = <regular expression>
* The raw result of the cmd<1-20> is searched for the <regular expression>. If found, the cmd<1-20> failed and the CLI (ssh) session will exit using the exit_cmd.
* A found fail regex overrides a found success regex

cmd<1-20>_prompt_regex = <regular expression>
cmd<1-20>_prompt_response_string = <response string>
cmd<1-20>_prompt_response_mode_level = <integer>
cmd<1-20>_prompt_override_response_string = <response string>
cmd<1-20>_prompt_override_response_mode_level = <integer>
cmd_branch<1-20>_<1-20>_prompt_regex = <regular expression>
cmd_branch<1-20>_<1-20>_prompt_response_string = <response string>
cmd_branch<1-20>_<1-20>_prompt_response_mode_level = <integer>
cmd_branch<1-20>_<1-20>_prompt_override_response_string = <response string>
cmd_branch<1-20>_<1-20>_prompt_override_response_mode_level = <integer>
* If the cmd<1-20>_prompt_regex is specified, the raw result of the cmd<1-20> is searched for the <regular expression>. If found, the cmd<1-20>_prompt_response_string is sent to CLI (ssh) session to respond to the prompt and the exit_cmd and cmd<1-20>_prompt_override_response_mode_level are used to exit the CLI (ssh) session. However if the check1 input box is checked in the UI, the cmd<1-20>_prompt_override_response_string is sent as a response and the cmd<1-20> commands will continue.

cmd<1-20>_cli_cmd_delay = <time in seconds>
cmd_branch<1-20>_<1-20>_cli_cmd_delay = <time in seconds>
* If specified, the cmd<1-20>_cli_cmd_delay will override the cli_cmd_delay in the default/cliauto.conf file.
* cmd<1-20>_cli_cmd_delay is timeout for pexpect to wait for the next prompt

cmd<1-20>_cli_cmd_sleep = <time in seconds>
cmd_branch<1-20>_<1-20>_cli_cmd_sleep = <time in seconds>
* If specified, the cmd<1-20>_cli_cmd_sleep will sleep before executing CLI command

cmd<1-20>_expect_prompt_regex = <regular expression>
cmd_branch<1-20>_<1-20>_expect_prompt_regex = <regular expression>
* If specified, the cmd<1-20>_expect_prompt_regex will override the expect_prompt_regex

cmd<1-20>_no_config_diff_regex = <regular expression>
cmd_branch<1-20>_<1-20>_no_config_diff_regex = <regular expression>
* If specified and the regular expression is not found in output of the command, the CLI (ssh) session will be terminated by sending the exit_cmd for the current mode level.
* This parameter was initially created for the "show config diff" command of Palo Alto firewalls

cmd<1-20>_max_output_before_truncate = <integer>
cmd_branch<1-20>_<1-20>_max_output_before_truncate = <integer>
* If specified, the cmd<1-20>_max_output_before_truncate is the maximum characters before trunicating output of the cmd<1-20> CLI command

custom_result_field<1-20> = <string>
* If specified and the custom_result_field<1-20>_regex exists, the name of result field to index to Splunk for the value returned by the custom_result_field<1-20>_regex on the raw result

custom_result_field<1-20>_regex = <regular expression>
* The regular expression for custom_result_field<1-20>

custom_result_field<1-20>_duplicate_check = <no | yes>
* A value of no disables the duplicate check of custom field <1-20>
* A value of yes enables the duplicate check of custom field <1-20>

output_data_name<1-20> = <string>
* A name for the type of data

output_data_type<1-20> = <string>
* A value of single_event is for command types that only output a single Splunk event per host
* A value of multiple_events_fixed_width is for command types that output multiple Splunk events per host with fixed width columns and a header record
* If not specified, output_type = single_event

output_data_format<1-20> = <string>
* A string which defines the data format returned by the output_data_regex
* For multiple_events_fixed_width, the value should contain a delimited string using the output_line_delimiter as the delimiter

output_header_regex<1-20> = <regular expression>
* The regular expression to find the header record for the data

output_data_regex<1-20> = <regular expression>
* The regular expression to find the data records for the data

output_data_stats_search_name<1-4> = <string>
* A stats search string suffix name

output_data_stats_search<1-4> = <string>
* A stats search string suffix for a custom search

max_result_blocks_override = <maximum number of blocks>
* An override for the maximum number of blocks setting in the cliauto_.conf file.
* This override was added to due large size of output data for output_type=multiple_events
* The <maximum number of blocks> in each result (1 block = 1 KB or 1024 bytes). Min = 1, Max = 500.

