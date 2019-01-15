# CLI Auto

## About

The CLI Auto app provides a job engine (via a custom REST API endpoint) and an user interface to connect to several nodes (hosts) via ssh to execute and index (i.e. log to Splunk) the output of a Command Type (i.e. a set of CLI commands). Each Command Type configuration defines the set of CLI command(s), user input variables, data validation, success/failure regular expressions, and other configuration settings for the associated Command Type. Only a few Command Types were included in the initial version of the app; however, the app allows an user to develop and add more Command Types. With the wide support of CLI (ssh), the number of possible Command Types are numerous. It should be noted that the initial development of this app was geared toward user management CLI commands for Checkpoint, Palo Alto, and Sonicwall firewalls. The intent of this app is not to be a replacement for any management tools for these firewall brands or any other network device that supports CLI.

## Dependencies

- The CLI Auto application was developed on a Linux OS VM (CentOS) with a Splunk Dev environment. Due to limited resources, no development/testing at all was done against the Splunk Windows OS environment.

- The Pexpect (pxssh) libraries (i.e. provide the ssh connection) were built for the CentOS hosting the Splunk dev environment and copied to the `$SPLUNK_HOME/etc/apps/cliauto/bin` folder. The Openssh app (included with several Linux OS distros) is a dependency of the Pexpect (pxssh) libraries. And as of this writing, the ptyprocess libraries are a dependency for the Pexpect (pxssh) libraries; so the ptyprocess libraries were built for the OS hosting the Splunk dev environment and copied to the `$SPLUNK_HOME/etc/apps/cliauto/bin` folder also. For most Linux OS Splunk installations, the `/opt/splunk` folder is the default value for the $SPLUNK_HOME environment variable.

- The Splunk Python SDK libraries provide intergration to the Splunk environment for the job engine (reference the `$SPLUNK_HOME/etc/apps/cliauto/bin/splunklib` and `$SPLUNK_HOME/etc/apps/cliauto/bin/utils` folders).

- The Bootstrap (JS and CSS files) and Splunk Javascript SDK libraries help to provide front-end (UI) components (reference the `$SPLUNK_HOME/etc/apps/cliauto/appserver/static` folder).

- The app was developed using the Chrome web browser. No testing/development was done with other web browsers.

## Usage

The CLI Auto dashboard provides an user interface (UI) to start and monitor submitted jobs. To get the help notes for the UI, hover your cursor over the input fields and job record table headers to display the associated tooltip. Enter a Script User, enter a Script Password, select a Node List KVStore CSV Lookup file (see the instructions below to create the Node List file), and select a Command Type.

![Alt text](/cliauto/appserver/static/img/help/cliautoui.png?raw=true)

#### Script Username

Enter the username that has permissions to login via to all of the nodes in the Node List. The tooltips are defined in the `cliauto.conf` and `cliauto_cmds.conf` files.

![Alt text](/cliauto/appserver/static/img/help/scriptusername.png?raw=true)

#### Script Password

Enter the password for the Script username.

![Alt text](/cliauto/appserver/static/img/help/scriptpassword.png?raw=true)

#### Command Type

Select the CLI command(s) to be executed in the Command Type field. (example: SWFW Show Version)

![Alt text](/cliauto/appserver/static/img/help/scriptcommand.png?raw=true)

#### Node List

The KVStore Lookup CSV file needs to contain a header record with 2 columns named `host` and `ip_address`. Please see the example in the screenshot below.

![Alt text](/cliauto/appserver/static/img/help/nodelistcsv.png?raw=true)

To create the KVStore Lookup CSV file within Splunk, click Settings->Lookups.

![Alt text](/cliauto/appserver/static/img/help/settingslookups.png?raw=true)

Click Add New for Lookup table files.

![Alt text](/cliauto/appserver/static/img/help/lookuptableaddnew.png?raw=true)

Select cliauto for the Destination app, click the Choose File button to select your Node List CSV file, give the Destination file an appropiate name, and click Save.

![Alt text](/cliauto/appserver/static/img/help/lookuptablesave.png?raw=true)

Verify that the KVStore Lookup table file was successfully saved.

![Alt text](/cliauto/appserver/static/img/help/lookuptablesuccess.png?raw=true)

![Alt text](/cliauto/appserver/static/img/help/nodelist.png?raw=true)

Note: Splunk has other ways to create a KVStore Lookup file (a search command, other apps, etc.)

In the dashboard, select the KVStore CSV Lookup file that contains the nodes for the Command Type.

#### Submit Button

Click the Submit button to process the job.

![Alt text](/cliauto/appserver/static/img/help/submit.png?raw=true)

#### Submit Confirm

Please type `yes` to confirm and submit job.

![Alt text](/cliauto/appserver/static/img/help/confirm.png?raw=true)

#### Permissions

If you receive a popup similar to the ones below, your username may not have the proper permissions. Please see the Security section below with info to request your Splunk administrator for the proper access to the app.

![Alt text](/cliauto/appserver/static/img/help/security.png?raw=true)

![Alt text](/cliauto/appserver/static/img/help/security2.png?raw=true)

#### Wait for the job to complete

The Status column of the job table displays the status of the job on the dashboard.

![Alt text](/cliauto/appserver/static/img/help/status.png?raw=true)

#### Job Results

To view the results for a job, click All, Success, or Fail to open the Splunk search app and execute the search with the filters provided in the respective url link. You can also find the job's results that were indexed to Splunk by creating you own search string (SPL) in the Splunk Search app with the index, source, sourcetype, and Job Id as filters. For example in the screenshot, `index=main source=cliauto sourcetype=cliauto_ssh jobid=5bce1418e1382395b6480856`. The default index, source and sourcetype for the app are `index=main`, `source=cliauto` and `sourcetype=cliauto_ssh`; so if you changed them in the CLI Auto app's conf file `$SPLUNK_HOME/etc/apps/cliauto/default/cliauto.conf`, your SPL search string will need to reflect your changes.

![Alt text](/cliauto/appserver/static/img/help/search.png?raw=true)

#### The "result" field

The "result" field in the job results is controlled by the success and failure regular expressions for the associated Command Type. The primary purpose of the "result" field is to provide a method to sort the job results to allow for an user to more quickly identify any possible next actions.

![Alt text](/cliauto/appserver/static/img/help/result.png?raw=true)

## Dependencies install instructions (as needed)

For ssh support, you need the ptyprocess and Pexpect (pxssh) python modules for this app, and are included in the installation files. However if needed, they can be downloaded from [here](https://pypi.org/project/ptyprocess/) and [here](https://pypi.org/project/pexpect/).

Due to the limited module set installed with Splunk's Python instance, you may need to build these modules with a second installation of Python. Once you've built the modules you will need to copy the build/lib/ptyprocess and the build/lib/pexpect directories into your $SPLUNK_HOME/etc/apps/cliauto/bin directory. Also, the Splunk Python SDK libraries need to exist in the $SPLUNK_HOME/etc/apps/cliauto/bin directory.

```
Follow build instructions on the respective sites.  No need to install. Instructions should be the same
for both modules:
    cd $BUILD/pexpect-4.6.0
    python setup.py build
    cd $BUILD/ptyprocess-0.6.0
    python setup.py build

Copy the respective directories to $SPLUNK_HOME/etc/apps/cliauto/bin
    cp -Rf $BUILD/pexpect-4.6.0/build/lib/pexpect $SPLUNK_HOME/etc/apps/cliauto/bin
    cp -Rf $BUILD/ptyprocess-0.6.0/build/lib/ptyprocess $SPLUNK_HOME/etc/apps/cliauto/bin

Restart splunk.
```

## Application Data Flow, Main Execution Path, and Threads

The 3 diagrams below show the data flow, main execution path, and threads for the application.

![Alt text](/cliauto/appserver/static/img/help/cliautoappdataflow.png?raw=true)

![Alt text](/cliauto/appserver/static/img/help/cliautorestapiepmainexecutionpath.png?raw=true)

![Alt text](/cliauto/appserver/static/img/help/cliautorestapithreads.png?raw=true)

## Security

- This app is secured with the `cliauto_custom_endpoint` capability and the `cliauto_user` role. It should be noted that the `edit_tcp` capability is included in the `cliauto_user` role to allow the app to index job results to Splunk. Contact your Splunk administrator to grant your Splunk user account the `cliauto_user` role to gain the required capabilities for the app.

- Like any app, the level of security has a dependence on the environment used to host the app. So, it is suggested that the dependenices (see above) be updated periodically with their respective security patches/fixes.

- For security reasons, it is recommended that the Custom (cli_custom) cmdtype be disabled in the `cliauto_cmds.conf` file unless needed for your use cases and proper security controls are in place. The intent of the Custom (cli_custom) cmdtype is to provide Splunk administrators/power users a tool to develop their own cmdtypes.

- The data input validation for the app is to help guard against malicious and/or unintended uses. If your use case(s) requires data input that is blocked by the data input validation, the conf files may have a setting that can be modified to allow it. If not, you are welcome to suggest a new feature.

- Some security related options of the ssh client (pexpect/pxssh library) are included in the `cliauto.conf` file, and should be reviewed/set for your environment/use cases. If more options are needed for your use case, a feature request is suggested.

- It should be noted that the login function of the pexpect (pxssh) library was overridden for the app to account for specific use cases.

- If you have suggestions to improve the security of the app, please contact support.

## Application Performance

Using a Splunk VM on a laptop, the app has successfully executed several jobs with 300+ unique hosts and MaxThreads setting = 75 for multiple Command Types. A job with 1000 hosts (with non-active ip_addresses) was tested successfully also. Please let me know your feedback on the performance of the application.

## Command Types

It should be noted that the app allows for additional Command Types to be configured by Splunk Administrators/Power Users. The configuration of each included Command Type (cmdtype) can be found in the `cliauto_cmds.conf` file in the `$SPLUNK_HOME/etc/apps/cliauto/default` folder. Each cmdtype configuration defines the CLI command(s), user input variables, data validation, success/failure regular expressions, and other configuration settings for the associated cmdtype. Per the "configuration file precedence" design feature of Splunk, it is recommended that new cmdtypes (or changes) be done by creating a `$SPLUNK_HOME/etc/apps/cliauto/local` folder and conf file with the same filename (`cliauto_cmds.conf`). The contents of the new conf file must contain the stanza (aka cmdtype) along with the configuration setting. Also, please reference the `cliauto_cmds.conf.spec` file in the `$SPLUNK_HOME/etc/apps/cliauto/README` folder for a description of the configuration settings.

## Limitations and/or Known Issues

- The app's custom REST API endpoint (job engine) uses the user's session credentials for access to the Splunk environment. These session credentials expire based on the Splunk Session timeout setting (see Settings->Server settings->General settings->Session timeout in Splunk UI) which has a default setting of 1 hour. If a job's exectution time is longer than the Session timeout setting, the job may fail due to losing access to the Splunk environment. It is not expected that any properly configured job would last longer than the default setting of 1 hour, but please be aware of this limitation of Splunk and/or the app.

- This issue only impacts the inspection/certification (i.e. "Splunk AppInspect Passed" badge on splunkbase website) of the "CLI Auto for Splunk" app by the online Splunk AppInspect app, but not the functionality of the "CLI Auto for Splunk" app itself. As of this writing, the Splunk AppInspect app contains a limitation/issue that fails an app for containing Python 3.x commands and/or syntax. Per pexpect's documentation, the pexpect Python library supports both the Python 2.7 and 3.x versions. Per a list of suggested workarounds from the splunkbase support team, the filename extension of the pexpect `_async.py` file was changed to prevent the Splunk AppInspect app from inspecting the file. This workaround prevents the "CLI Auto for Splunk" app from failing the automated online Splunk AppInspect inspection for this limitation/issue during upload to splunkbase.

## Support/Suggestions

Contact the developer
