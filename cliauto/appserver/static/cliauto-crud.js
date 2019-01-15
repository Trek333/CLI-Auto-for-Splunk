'use strict';
var IntervalId = null;
var NUM_JOBS = 10; // Default value
var searchQuery = "| inputlookup cliauto_pid_lookup \
| sort Timestamp desc \
| eval JobId = _key \
, Timestamp=strftime(Timestamp/1000,\"%m/%d/%Y %H:%M:%S\") \
, StartTime=strftime(StartTime/1000,\"%m/%d/%Y %H:%M:%S\") \
, EndTime=strftime(EndTime/1000,\"%m/%d/%Y %H:%M:%S\") \
| table JobId, NodeList, Status, PID, Timestamp, Command, StartTime, EndTime, ScriptUser, SessionUser, HostCount, index, source, sourcetype, CommandType, CustomSumFields \
| fillnull value=\"\" \
| head ";

// Configuration conf file variables
ui_response = new Object();
app_response = new Object();

require(['jquery',
        'underscore',
        'splunkjs/mvc',
        'splunkjs/mvc/utils',
        'splunkjs/mvc/tokenutils',
        'splunkjs/mvc/messages',
        'splunkjs/mvc/searchmanager',
        'splunkjs/mvc/multidropdownview',
        'splunkjs/mvc/dropdownview',        
        '/static/app/cliauto/Modal.js',
        'splunkjs/mvc/simpleform/input/dropdown',
        'splunkjs/mvc/simplexml/ready!'],

    function ($,
          _,
          mvc,
          utils,
          TokenUtils,
          Messages,
          SearchManager,
          MultiDropdownView,
          DropdownView,
          Modal,
          Dropdown) {

    function isArray(x) {
        return x.constructor.toString().indexOf("Array") > -1;
    }

    function anonCallback(callback=function(){}, callbackArgs=null) {
        debugger;
        if(callbackArgs) {
            callback.apply(this, callbackArgs);
        } else { 
            callback();
        }
    }

    function genericPromise() {
        var dfd = $.Deferred();
        dfd.resolve();
        return dfd.promise();
    }

    // Wrapper to execute multiple searches in order and resolve when they've all finished
    function all(array){
        var deferred = $.Deferred();
        var fulfilled = 0, length = array.length;
        var results = [];
    
        if (length === 0) {
            deferred.resolve(results);
        } else {
            _.each(array, function(promise, i){
                $.when(promise()).then(function(value) {
                    results[i] = value;
                    fulfilled++;
                    if(fulfilled === length){
                        deferred.resolve(results);
                    }
                });
            });
        }
    
        return deferred.promise();
    };

    // Helper to figure out if the create form is open
    function isFormOpen() {
        var formOpen = window.sessionStorage.getItem("formOpen");
        if(_.isNull(formOpen) || _.isUndefined(formOpen) || formOpen === "false") {
            return false;
        } else {
            return true;
        }
    }

    // Callback to refresh window
    function refreshWindow() {
        setTimeout(function () {
            location.reload()
            $('#command-table').show();
        }, 500);
    }

    // Check for non-UTF8 (ASCII) character in string
    function IsNotUTF8(str) {
        var charcode = 0;
        for (var ichar = 0; ichar < str.length; ichar++) {
            charcode = str.charCodeAt(ichar);
            if((charcode < 32) || (charcode > 126)){
                return true;
            }
        }
        return false;

    }

    // Check for double or single quote character in string
    function ContainsQuote(str) {
        var charcode = 0;
        for (var ichar = 0; ichar < str.length; ichar++) {
            charcode = str.charCodeAt(ichar);
            if((charcode == 34) || (charcode == 39)){
                return true;
            }
        }
        return false;

    }

    // Check for invalid character in string
    function containsInvalidChars(str, chars) {
        if (chars.charAt(0) == '"') {
            chars = chars.substr(1);
        }
        if (chars.charAt(chars.length-1) == '"') {
            chars = chars.slice(0, -1);
        }
        for (var ichars = 0; ichars < chars.length; ichars++) {
            for (var istr = 0; istr < str.length; istr++) {
                if(chars.charAt(ichars) == str.charAt(istr)){
                    return true;
                }
            }
        }
        return false;
    }

    function confirmSubmit() {
        var txt;
        var userresponse = prompt("Please type yes to confirm and submit job:", "no");
        if (userresponse == "yes") {
            txt = "User cancelled submit";
            return true;
        } else {
            txt = "User confirmed submitted job";
            return false;
        }
    }

    function renderModal(id, title, body, buttonText, callback=function(){}, callbackArgs=null) {
        // Create the modal
        var myModal = new Modal(id, {
                    title: title,
                    backdrop: 'static',
                    keyboard: false,
                    destroyOnHide: true,
                    type: 'wide'
        }); 

        // Add content
        myModal.body.append($(body));
    
        // Add footer
        myModal.footer.append($('<button>').attr({
            type: 'button',
            'data-dismiss': 'modal'
        })
        .addClass('btn btn-primary').text(buttonText).on('click', function () {
                anonCallback(callback, callbackArgs); 
        }))

        // Launch it!  
        myModal.show(); 
    }

    // Clear click listener and register with new callback
    function clearOnClickAndRegister(el, callback, callbackArgs=null) {
        // Register click callback
        if(_.isUndefined($._data($(el).get(0), "events"))) {
            $(el).on('click', function (event) {
                event.preventDefault();
                anonCallback(callback, callbackArgs);
            });
            return;    
        }

        // Unregister click callback
        if(_.isObject($._data($(el).get(0), "events")) && _.has($._data($(el).get(0), "events"), "click")) {
            $(el).off('click');
            $(el).on('click', function () {
                anonCallback(callback, callbackArgs);
            });
        }
    }

    // Return selected rows from bootstrap-table
    function getIdSelections() {
        return $.map($('#rest-command-table').bootstrapTable('getSelections'), function (row) {
            return row
        });
    }

    // Get config cmds (cmdtypes) for UI configuration from server
    function GetConfigCmdsConf() {
        var service = mvc.createService({ owner: "nobody", app: "cliauto" });
        service.request(
            "configs/conf-cliauto_cmds",
            "GET",
            null,
            null,
            '',
            {"Content-Type": "application/json"},
            function(err, response) {
                if ((err != null) || (response.data.entry[0] == undefined)){
                    console.log(err);
                    return renderModal("error-config-cmds",
                                       "Error",
                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Error occurred while getting cmdtypes. Verify the cliauto_cmd.conf file contains at least one cmdtype and/or try refreshing web page.</div>",
                                       "Close")
                }
                console.log(response);
                console.log(response.data.entry[0].name);
                ui_response = response;
                GetConfigConf();
            });
    }

    // Get config for UI configuration from server
    function GetConfigConf() {
        var service = mvc.createService({ owner: "nobody", app: "cliauto" });
        service.request(
            "configs/conf-cliauto",
            "GET",
            null,
            null,
            '',
            {"Content-Type": "application/json"},
            function(err, response) {
                if ((err != null) || (response.data.entry[0].content.ui_job_rows == undefined)){
                    console.log(err);
                    return renderModal("error-config",
                                       "Error",
                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Error occurred while getting UI config. Verify the cliauto.conf file contains ui_job_rows variable with numeric value and/or try refreshing web page.</div>",
                                       "Close")
                }
                console.log(response);
                console.log(response.data.entry[0].content.ui_job_rows);
                app_response = response;
                NUM_JOBS = response.data.entry[0].content.ui_job_rows;
                populateTable();
            });
    }

    // Populate cmdtpyes for UI configuration from server
    function PopulateCmdTypes() {

        // Add enabled cmdtypes to ScriptCommand-dropdown
        var arrayLength = ui_response.data.entry.length;
        for (var i = 0; i < arrayLength; i++) {
            if (ui_response.data.entry[i].content.cmdtype_enable == "1"){
                $("#ScriptCommand-dropdown").append('<option value="'+ui_response.data.entry[i].name+'">'+ui_response.data.entry[i].content.kv_cmd_string+'</option>');
            }
        }
        


    }

    // Verify ssh Port Open
    // Custom
    // SWFW Delete User
    // SWFW Verify configure administration Mode
    // SWFW Show Version
    // SWFW Show User Local (All)
    // SWFW Add User
    // SWFW admin Password Change
    // CPFW Show Version
    // CPFW Set User Password
    // PAFW Show System Info
    // PAFW Set Mgt User Password
    // Apply configuration for UI configuration from server
    function ApplyConfigConf(){
        console.log($("#ScriptCommand-dropdown").val());
        $('#suserDiv').css("display", "none");
        $('#spwDiv').css("display", "none");
        $('#var1Div').css("display", "none");
        $('#var2Div').css("display", "none");
        $('#var3Div').css("display", "none");
        $('#var4Div').css("display", "none");
        $('#pw1Div').css("display", "none");
        $('#pw2Div').css("display", "none");
        $('#pw3Div').css("display", "none");
        $('#check1Div').css("display", "none");
        $('#Var1TextInput').val('');
        $('#Var2TextInput').val('');
        $('#Var3TextInput').val('');
        $('#Var4TextInput').val('');
        $('#PW1TextInput').val('');
        $('#PW2TextInput').val('');
        $('#PW3TextInput').val('');
        $('input[id=PW1TextInput]').prop('type', 'text')
        $('input[id=PW2TextInput]').prop('type', 'text')
        $('input[id=PW3TextInput]').prop('type', 'text')
        $("#PW1cb").prop('checked', false).change();
        $("#PW2cb").prop('checked', false).change();
        $("#PW3cb").prop('checked', false).change();
        $("#Check1").prop('checked', false).change();
        $('#drop1Div').css("display", "none");
        $('#Drop1').empty()
        $('#generalmsgDiv').css("display", "none");
        $('.generalmsg').html('');
        $('#check1MsgDiv').css("display", "none");
        $('.check1msg').html('');
        $('#NodeList-dropdown').prop('title', '');
        $('#ScriptCommand-dropdown').prop('title', '');
        $('#suserTextInput').prop('title', '');
        $('#spwTextInput').prop('title', '');
        $('#Var1TextInput').prop('title', '');
        $('#Var2TextInput').prop('title', '');
        $('#Var3TextInput').prop('title', '');
        $('#Var4TextInput').prop('title', '');
        $('#PW1TextInput').prop('title', '');
        $('#PW2TextInput').prop('title', '');
        $('#PW3TextInput').prop('title', '');
        $('#Drop1').prop('title', '');
        
        var arrayLength = ui_response.data.entry.length;
        for (var i = 0; i < arrayLength; i++) {
            if (ui_response.data.entry[i].name == $("#ScriptCommand-dropdown").val()) {
                
                if (ui_response.data.entry[i].content.ui_nodelist_title != undefined) {
                    $('#NodeList-dropdown').prop('title', ui_response.data.entry[i].content.ui_nodelist_title);
                }

                if (ui_response.data.entry[i].content.ui_cmdtype_title != undefined) {
                    $('#ScriptCommand-dropdown').prop('title', ui_response.data.entry[i].content.ui_cmdtype_title);
                }

                if (ui_response.data.entry[i].content.ui_suser_label != undefined) {
                    $('#suserDiv').css("display", "block");
                    $('#suserLabel').html(ui_response.data.entry[i].content.ui_suser_label);
                    $('#suserTextInput').removeAttr('placeholder');
                    $('#suserTextInput').attr('placeholder',ui_response.data.entry[i].content.ui_suser_placeholder);
                    $('#suserTextInput').prop('title', ui_response.data.entry[i].content.ui_suser_title);
                }
                if (ui_response.data.entry[i].content.ui_spw_label != undefined) {
                    $('#spwDiv').css("display", "block");
                    $('#spwLabel').html(ui_response.data.entry[i].content.ui_spw_label);
                    $('#spwTextInput').removeAttr('placeholder');
                    $('#spwTextInput').attr('placeholder',ui_response.data.entry[i].content.ui_spw_placeholder);
                    $('#spwTextInput').prop('title', ui_response.data.entry[i].content.ui_spw_title);
                }
                if (ui_response.data.entry[i].content.ui_general_msg != undefined) {
                    $('#generalmsgDiv').css("display", "block");
                    $('.generalmsg').html(ui_response.data.entry[i].content.ui_general_msg);
                }
                if (ui_response.data.entry[i].content.ui_var1_label != undefined) {
                    $('#var1Div').css("display", "block");
                    $('#Var1Label').html(ui_response.data.entry[i].content.ui_var1_label);
                    $('#Var1TextInput').removeAttr('placeholder');
                    $('#Var1TextInput').attr('placeholder',ui_response.data.entry[i].content.ui_var1_placeholder);
                    $('#Var1TextInput').prop('title', ui_response.data.entry[i].content.ui_var1_title);
                }
                if (ui_response.data.entry[i].content.ui_var2_label != undefined) {
                    $('#var2Div').css("display", "block");
                    $('#Var2Label').html(ui_response.data.entry[i].content.ui_var2_label);
                    $('#Var2TextInput').removeAttr('placeholder');
                    $('#Var2TextInput').attr('placeholder',ui_response.data.entry[i].content.ui_var2_placeholder);
                    $('#Var2TextInput').prop('title', ui_response.data.entry[i].content.ui_var2_title);
                }
                if (ui_response.data.entry[i].content.ui_var3_label != undefined) {
                    $('#var3Div').css("display", "block");
                    $('#Var3Label').html(ui_response.data.entry[i].content.ui_var3_label);
                    $('#Var3TextInput').removeAttr('placeholder');
                    $('#Var3TextInput').attr('placeholder',ui_response.data.entry[i].content.ui_var3_placeholder);
                    $('#Var3TextInput').prop('title', ui_response.data.entry[i].content.ui_var3_title);
                }
                if (ui_response.data.entry[i].content.ui_var4_label != undefined) {
                    $('#var4Div').css("display", "block");
                    $('#Var4Label').html(ui_response.data.entry[i].content.ui_var4_label);
                    $('#Var4TextInput').removeAttr('placeholder');
                    $('#Var4TextInput').attr('placeholder',ui_response.data.entry[i].content.ui_var4_placeholder);
                    $('#Var4TextInput').prop('title', ui_response.data.entry[i].content.ui_var4_title);
                }
                if (ui_response.data.entry[i].content.ui_pw1_label != undefined) {
                    $('#pw1Div').css("display", "block");
                    $('#PW1Label').html(ui_response.data.entry[i].content.ui_pw1_label);
                    $('#PW1TextInput').removeAttr('placeholder');
                    $('#PW1TextInput').attr('placeholder',ui_response.data.entry[i].content.ui_pw1_placeholder);
                    $('#PW1TextInput').prop('title', ui_response.data.entry[i].content.ui_pw1_title);
                }
                if (ui_response.data.entry[i].content.ui_pw2_label != undefined) {
                    $('#pw2Div').css("display", "block");
                    $('#PW2Label').html(ui_response.data.entry[i].content.ui_pw2_label);
                    $('#PW2TextInput').removeAttr('placeholder');
                    $('#PW2TextInput').attr('placeholder',ui_response.data.entry[i].content.ui_pw2_placeholder);
                    $('#PW2TextInput').prop('title', ui_response.data.entry[i].content.ui_pw2_title);
                }
                if (ui_response.data.entry[i].content.ui_pw3_label != undefined) {
                    $('#pw3Div').css("display", "block");
                    $('#PW3Label').html(ui_response.data.entry[i].content.ui_pw3_label);
                    $('#PW3TextInput').removeAttr('placeholder');
                    $('#PW3TextInput').attr('placeholder',ui_response.data.entry[i].content.ui_pw3_placeholder);
                    $('#PW3TextInput').prop('title', ui_response.data.entry[i].content.ui_pw3_title);
                }
                if (ui_response.data.entry[i].content.ui_check1_label != undefined) {
                    $('#check1Div').css("display", "block");
                    $('#Check1Label').html(ui_response.data.entry[i].content.ui_check1_label);
                }
                if (ui_response.data.entry[i].content.ui_check1_msg != undefined) {
                    $('#check1MsgDiv').css("display", "block");
                    $('.check1msg').html(ui_response.data.entry[i].content.ui_check1_msg);
                }
                if (ui_response.data.entry[i].content.ui_drop1_label != undefined) {
                    $('#drop1Div').css("display", "block");
                    $('#Drop1Label').html(ui_response.data.entry[i].content.ui_drop1_label);
                    $('#Drop1').prop('title', ui_response.data.entry[i].content.ui_drop1_title);
                    var drop1_options_array = ui_response.data.entry[i].content.ui_drop1_options.split(/,/);
                    var arrayLength_drop1 = drop1_options_array.length;
                    for (var i2 = 0; i2 < arrayLength_drop1; i2++) {
                        $("#Drop1").append('<option value="'+drop1_options_array[i2]+'">'+drop1_options_array[i2]+'</option>');
                    }
                break;
                    
                }

            }

        }

}

    // Run search to populate and call create table
    function populateTable() {
        // Initialize
        window.sessionStorage.setItem("formOpen", "false");
        var pidTableDiv = '#command-table';

        var search1 = new SearchManager({
                    "id": "search1",
                    "cancelOnUnload": true,
                    "status_buckets": 0,
                    "earliest_time": "-24h@h",
                    "latest_time": "now",
                    "sample_ratio": 1,
                    "search": searchQuery + NUM_JOBS,
                    "app": utils.getCurrentApp(),
                    "auto_cancel": 90,
                    "preview": true,
                    "tokenDependencies": {
                    },
                    "runWhenTimeIsUndefined": false
                }, {tokens: true, tokenNamespace: "submitted"});

        var mainSearch = splunkjs.mvc.Components.getInstance("search1");
        var myResults = mainSearch.data('results', { output_mode:'json', count:0 });
        //mainSearch.startSearch();

        mainSearch.on('search:progress', function(properties) {
            Messages.render("waiting", $(pidTableDiv));
        });

        mainSearch.on('search:done', function(properties) {
            document.getElementById("command-table").innerHTML = "";

            if(properties.content.resultCount == 0) {
                var noData = null;
                createTable(pidTableDiv, noData);
            }
        });

        myResults.on("data", function() {
            var data = myResults.data().results;
            createTable(pidTableDiv, data);
        });
    }

    // Run search to populate/update table
    function populateTableRefresh() {

        // Set the search parameters--specify a time range
        var searchParams = {
            earliest_time: "-24h@h",
            latest_time: "now"
        };

        var service = mvc.createService({ owner: "nobody" });
        // Run a oneshot search that returns the job's results
        service.oneshotSearch(
            searchQuery + NUM_JOBS,
            searchParams,
            function(err, results) {

                var data = results.rows;
                updateTable(data)
            }
        );
    }

    function updateTable(data) {
        var d = new Date();
        var n = d.getTime();
        var foundBusyStatus = false;
        var searchAllUrl = '';
        var searchAllatag = '';
        var searchSuccessatag = '';
        var JobSpanString = '';
        _.each(data, function(row, i) {
            searchAllUrl = '../../app/cliauto/search?q=search'
            + ' index="' + row[11] + '"'
            + ' source="' + row[12] + '"'
            + ' sourcetype="' + row[13] + '"'
            + ' jobid="' + row[0] + '"'
            + ' earliest=1 latest=now';
            searchAllatag = '<a class="action-link external" href="' + encodeURI(searchAllUrl) + '" target="_blank">All</a>';
            JobSpanString1 = row[0] + '<br>'+ searchAllatag
            JobSpanString2 = '<br>'
            if (row[14].toLowerCase() != 'cli_custom') {
                searchSuccessUrl = searchAllUrl + ' resultstatus="Success"';
                searchFailUrl = searchAllUrl + ' resultstatus="Fail"';
                searchSuccessCSVUrl = searchAllUrl + ' resultstatus="Success" | table host, ip_address | outputlookup success_' + row[1].slice(0, -4) + '_' + row[0].substring(row[0].length - 4) + '.csv';
                searchFailCSVUrl = searchAllUrl + ' resultstatus="Fail" | table host, ip_address | outputlookup fail_' + row[1].slice(0, -4) + '_' + row[0].substring(row[0].length - 4) + '.csv';
                searchSuccessUrl = encodeURI(searchSuccessUrl);
                searchFailUrl = encodeURI(searchFailUrl);
                searchSuccessCSVUrl = encodeURI(searchSuccessCSVUrl);
                searchFailCSVUrl = encodeURI(searchFailCSVUrl);
                searchSuccessatag = ' <a class="action-link external" href="' + searchSuccessUrl + '" target="_blank">Success</a>';
                searchFailatag = ' <a class="action-link external" href="' + searchFailUrl + '" target="_blank">Fail</a>';
                searchSuccesscsv = 'Create CSV: <a class="action-link external" href="' + searchSuccessCSVUrl + '" target="_blank">Success</a>';
                searchFailcsv = ' <a class="action-link external" href="' + searchFailCSVUrl + '" target="_blank">Fail</a>';
                JobSpanString1 = JobSpanString1 + searchSuccessatag;
                JobSpanString2 = JobSpanString2 + searchSuccesscsv;
                if (row[15].trim() != '') {
                    var CustomSumFields = row[15].split(',');
                    var arrayLength2 = CustomSumFields.length;
                    for (var i2 = 0; i2 < arrayLength2; i2++) {
                        searchCustomUrl = searchAllUrl + ' resultstatus="' + CustomSumFields[i2] + '"';
                        searchCustomCSVUrl = searchAllUrl + ' resultstatus="' + CustomSumFields[i2] + '" | table host, ip_address | outputlookup ' + CustomSumFields[i2].toLowerCase() + '_' + row[1].slice(0, -4) + '_' + row[0].substring(row[0].length - 4) + '.csv';
                        searchCustomUrl = encodeURI(searchCustomUrl);
                        searchCustomCSVUrl = encodeURI(searchCustomCSVUrl);
                        searchCustomatag = '<a class="action-link external" href="' + searchCustomUrl + '" target="_blank">' + CustomSumFields[i2] + '</a>';
                        searchCustomcsv = '<a class="action-link external" href="' + searchCustomCSVUrl + '" target="_blank">' + CustomSumFields[i2] + '</a>';
                        JobSpanString1 = JobSpanString1 + ' ' + searchCustomatag;
                        JobSpanString2 = JobSpanString2 + ' ' + searchCustomcsv;
                    }
                }
                JobSpanString1 = JobSpanString1 + searchFailatag;
                JobSpanString2 = JobSpanString2 + searchFailcsv;
            }
            JobSpanString = JobSpanString1 + JobSpanString2;

            $('.JobId'+ i).html(JobSpanString);
            $('.NodeList'+ i).html(row[1]);
            $('.Status'+ i).html(row[2]);
            $('.PID'+ i).html(row[3]);
            $('.Timestamp'+ i).html(row[4]);
            $('.Command'+ i).html(row[5]);
            $('.StartTime'+ i).html(row[6]);
            $('.EndTime'+ i).html(row[7]);
            $('.ScriptUser'+ i).html(row[8]);
            $('.SessionUser'+ i).html(row[9]);
            $('.HostCount'+ i).html(row[10]);

            if (row[2].substring(0,4) == "Busy") {
                foundBusyStatus = true;
                $('.Status'+ i).css( "background-color", "#65A637" )
            }
            else {
                $('.Status'+ i).css( "background-color", "" )
            }
        });
        if (foundBusyStatus == false){
            $('#command-progress-div').css("visibility", "hidden");
            $("#command-submit").prop("disabled",false);
            clearInterval(IntervalId);
        }

    }

    // Render credential table and wire up context menu
    function createTable(tableDiv, data) {
        var html = '<form id="scriptCredential"> \
                        <div class="form-row"> \
                            <div style = "padding-left: 5px;float:left;display: none" id="suserDiv" class="col"> \
                                <label for="suserTextInput" id="suserLabel"></label> \
                                <input type="ScriptUser" class="form-control" id="suserTextInput" title=""> \
                            </div> \
                            <div style = "padding-left: 5px;float:left;display: none" id="spwDiv" class="col"> \
                                <label for="spwTextInput" id="spwLabel" class="form-control"></label> \
                                <input type="password" class="form-control" id="spwTextInput" title=""> \
                            </div> \
                            <div style = "float:left" class="col"> \
                                <label for="NodeList-dropdown" id="NodeListLabel">Node List</label> \
                                <div id="NodeList-dropdown" title=""></div> \
                            </div> \
                            <div style = "float:left;padding-left: 5px" class="col"> \
                                <label for="ScriptCommand-dropdown" id="ScriptCommandDropdownLabel">Command Type</label> \
                                <select name="ScriptCommand-dropdown-name" id="ScriptCommand-dropdown" title=""> \
                                </select> \
                            </div> \
                            <div id="command-cli-submit" style = "float:left;padding-left: 5px"" class="col"> \
                                <button id="command-submit" class="btn btn-primary">Submit</button> \
                            </div> \
                            <div id="command-progress-div" style = "float:left;visibility: hidden" class="col"> \
                                <img src="/static/app/cliauto/img/spinning-loading-bar.gif?raw=true" alt="Alt text" style="width:75px;height:50px;"> \
                            </div> \
                        </div> \
                        </form> \
                        <br><br><br><br><br> \
                        <form id="scriptCmd"> \
                            <div class="form-row"> \
                            <div style = "padding-left: 5px;float:left;display: none" id="var1Div" class="col"> \
                                <label for="Var1Input" id="Var1Label"></label> \
                                <input type="text" class="form-control" id="Var1TextInput"> \
                            </div> \
                            <div style = "float:left;padding-left: 5px;display: none" id="var2Div" class="col"> \
                                <label for="Var2Input" id="Var2Label"></label> \
                                <input type="text" class="form-control" id="Var2TextInput"> \
                            </div> \
                            <div style = "float:left;padding-left: 5px;display: none" id="var3Div" class="col"> \
                                <label for="Var3Input" id="Var3Label"></label> \
                                <input type="text" class="form-control" id="Var3TextInput"> \
                            </div> \
                            <div style = "float:left;padding-left: 5px;display: none" id="var4Div" class="col"> \
                                <label for="Var4Input" id="Var4Label"></label> \
                                <input type="text" class="form-control" id="Var4TextInput"> \
                            </div> \
                            <div style = "float:left;padding-left: 5px;display: none" class="col" id="pw1Div"> \
                                <div class="row" style = "padding-left: 20px"> \
                                    <label for="PW1Input" id="PW1Label"></label> \
                                    <input type="password" class="form-control" id="PW1TextInput"> \
                                </div> \
                                <div class="row" style = "padding-left: 20px"> \
                                    <input type="checkbox" class="form-control" id="PW1cb">Show Password</input> \
                                </div> \
                            </div> \
                            <div style = "float:left;padding-left: 5px;display: none" class="col" id="pw2Div"> \
                                <div class="row" style = "padding-left: 20px"> \
                                    <label for="PW2Input" id="PW2Label"></label> \
                                    <input type="password" class="form-control" id="PW2TextInput"> \
                                </div> \
                                <div class="row" style = "padding-left: 20px"> \
                                    <input type="checkbox" class="form-control" id="PW2cb">Show Password</input> \
                                </div> \
                            </div> \
                            <div style = "float:left;padding-left: 5px;display: none" class="col" id="pw3Div"> \
                                <div class="row" style = "padding-left: 20px"> \
                                    <label for="PW3Input" id="PW3Label"></label> \
                                    <input type="password" class="form-control" id="PW3TextInput"> \
                                </div> \
                                <div class="row" style = "padding-left: 20px"> \
                                    <input type="checkbox" class="form-control" id="PW3cb">Show Password</input> \
                                </div> \
                            </div> \
                            <div style = "float:left;padding-left: 5px;display: none" id="drop1Div" class="col"> \
                                <label for="Drop1" id="Drop1Label">User Group</label> \
                                <select name="Drop1-name" id="Drop1"> \
                                </select> \
                            </div> \
                            <div style = "float:left;padding-left;display: none" id="generalmsgDiv" class="form-group"> \
                                <p><span class="generalmsg"></span></p> \
                            </div> \
                        </div> \
                        </form> \
                        <br><br><br><br> \
                        <form id="scriptCheck"> \
                        <div class="form-row"> \
                            <div style = "float:left;padding-left: 5px;display: none" id="check1Div" class="col"> \
                                <input type="checkbox" class="form-check-input" id="Check1"> \
                                <label for="Check1" id="Check1Label"></label> \
                            </div> \
                            <div style = "float:left;padding-left;display: none" id="check1MsgDiv" class="form-group"> \
                                <p><span style="color:red;" class="check1msg"></span></p> \
                            </div> \
                        </div> \
                    </form> \
                    <br><br> \
                    ';

        // <p style="color:red;"><br><b>&nbsp;&nbsp;&nbsp;Warning: This option will cause editing user(s) to lose pending configuration changes</b></p> \
        var tdHtml = "";
                             //class="table table-striped table-hover" 
        var header = '  <table id="rest-command-table" \
                             class="table table-striped table-condensed" \
                             data-toolbar="#toolbar" \
                             data-detail-view="true" \
                             data-sort-name="username" \
                             data-show-pagination-switch="true" \
                             data-id-field="id" \
                             data-pagination="true" \
                             data-sortable="true" \
                             data-page-size="10" \
                             data-page-list="[10,20,50,ALL]" \
                             data-id-field="id" \
                             data-toggle="table" \
                             data-smart-display="true" \
                             data-search="true" \
                             data-checkbox-header="true" \
                             data-show-footer="false" \
                             data-select-item-name="button-select" \
                             data-click-to-select="false"> \
                      <thead> \
                        <tr> \
                            <th style="font-size: 12px;" data-field="JobId" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_jobid_title + '"><div>Job Id - click to open in search</div></th> \
                            <th style="font-size: 12px;" data-field="NodeList" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_nodelist_title + '"><div>Node List</div></th> \
                            <th style="font-size: 12px;" data-field="Status" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_status_title + '"><div>Status</th> \
                            <th style="font-size: 12px;" data-field="PID" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_pid_title + '"><div>PID</th> \
                            <th style="font-size: 12px;" data-field="Timestamp" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_timestamp_title + '"><div>Timestamp</th> \
                            <th style="font-size: 12px;" data-field="Command" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_command_title + '"><div>Command</th> \
                            <th style="font-size: 12px;" data-field="StartTime" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_starttime_title + '"><div>StartTime</th> \
                            <th style="font-size: 12px;" data-field="EndTime" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_endtime_title + '"><div>EndTime</th> \
                            <th style="font-size: 12px;" data-field="ScriptUser" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_scriptuser_title + '"><div>Script User</th> \
                            <th style="font-size: 12px;" data-field="SessionUser" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_sessionuser_title + '"><div>Session User</th> \
                            <th style="font-size: 12px;" data-field="HostCount" data-sortable="true" data-align="center" title="' + app_response.data.entry[0].content.ui_hostcount_title + '"><div>Host Count</th> \
                        </tr> \
                      </thead> \
                      <tbody>';

        // NodeList, Status, PID, Timestamp, Command, StartTime, EndTime, ScriptUser, SessionUser, HostCount, index, source, sourcetype
        html += header;
        var pwtype = '';

        var numrows = 0;
        var searchUrl = '';
        var atag = '';
        var foundBusyStatus = false;

        _.each(data, function(row, i) {
            numrows = numrows + 1;
            searchAllUrl = '../../app/cliauto/search?q=search'
            + ' index="' + row.index + '"'
            + ' source="' + row.source + '"'
            + ' sourcetype="' + row.sourcetype + '"'
            + ' jobid="' + row.JobId + '"'
            + ' earliest=1 latest=now';
            searchAllatag = '<a class="action-link external" href="' + encodeURI(searchAllUrl) + '" target="_blank">All</a>';
            JobSpanString1 = row.JobId + '<br>'+ searchAllatag
            JobSpanString2 = '<br>'
            if (row.CommandType.toLowerCase() != 'cli_custom') {
                searchSuccessUrl = searchAllUrl + ' resultstatus="Success"';
                searchFailUrl = searchAllUrl + ' resultstatus="Fail"';
                searchSuccessCSVUrl = searchAllUrl + ' resultstatus="Success" | table host, ip_address | outputlookup success_' + row.NodeList.slice(0, -4) + '_' + row.JobId.substring(row.JobId.length - 4) + '.csv';
                searchFailCSVUrl = searchAllUrl + ' resultstatus="Fail" | table host, ip_address | outputlookup fail_' + row.NodeList.slice(0, -4) + '_' + row.JobId.substring(row.JobId.length - 4) + '.csv';
                searchSuccessUrl = encodeURI(searchSuccessUrl);
                searchFailUrl = encodeURI(searchFailUrl);
                searchSuccessCSVUrl = encodeURI(searchSuccessCSVUrl);
                searchFailCSVUrl = encodeURI(searchFailCSVUrl);
                searchSuccessatag = ' <a class="action-link external" href="' + searchSuccessUrl + '" target="_blank">Success</a>';
                searchFailatag = ' <a class="action-link external" href="' + searchFailUrl + '" target="_blank">Fail</a>';
                searchSuccesscsv = 'Create CSV: <a class="action-link external" href="' + searchSuccessCSVUrl + '" target="_blank">Success</a>';
                searchFailcsv = ' <a class="action-link external" href="' + searchFailCSVUrl + '" target="_blank">Fail</a>';
                JobSpanString1 = JobSpanString1 + searchSuccessatag;
                JobSpanString2 = JobSpanString2 + searchSuccesscsv;
                if (row.CustomSumFields.trim() != '') {
                    var CustomSumFields = row.CustomSumFields.split(',');
                    var arrayLength2 = CustomSumFields.length;
                    for (var i2 = 0; i2 < arrayLength2; i2++) {
                        searchCustomUrl = searchAllUrl + ' resultstatus="' + CustomSumFields[i2] + '"';
                        searchCustomCSVUrl = searchAllUrl + ' resultstatus="' + CustomSumFields[i2] + '" | table host, ip_address | outputlookup ' + CustomSumFields[i2].toLowerCase() + '_' + row.NodeList.slice(0, -4) + '_' + row.JobId.substring(row.JobId.length - 4) + '.csv';
                        searchCustomUrl = encodeURI(searchCustomUrl);
                        searchCustomCSVUrl = encodeURI(searchCustomCSVUrl);
                        searchCustomatag = '<a class="action-link external" href="' + searchCustomUrl + '" target="_blank">' + CustomSumFields[i2] + '</a>';
                        searchCustomcsv = '<a class="action-link external" href="' + searchCustomCSVUrl + '" target="_blank">' + CustomSumFields[i2] + '</a>';
                        JobSpanString1 = JobSpanString1 + ' ' + searchCustomatag;
                        JobSpanString2 = JobSpanString2 + ' ' + searchCustomcsv;
                    }
                }
                JobSpanString1 = JobSpanString1 + searchFailatag;
                JobSpanString2 = JobSpanString2 + searchFailcsv;
            }
            JobSpanString = JobSpanString1 + JobSpanString2;

            tdHtml += '<tr class="Row' + i +'">\
                         <td><span style="font-size: 10px;" class="JobId' + i +'">' + JobSpanString + '</span>\
                         <td><span style="font-size: 10px;" class="NodeList' + i +'">' + row.NodeList + '</span></td>\
                         <td><span style="font-size: 10px;" class="Status' + i +'">' + row.Status + '</span></td>\
                         <td><span style="font-size: 10px;" class="PID' + i +'">' + row.PID + '</span></td>\
                         <td><span style="font-size: 10px;" class="Timestamp' + i +'">' + row.Timestamp + '</span></td>\
                         <td><span style="font-size: 10px;" class="Command' + i +'">' + row.Command + '</span></td>\
                         <td><span style="font-size: 10px;" class="StartTime' + i +'">' + row.StartTime + '</span></td>\
                         <td><span style="font-size: 10px;" class="EndTime' + i +'">' + row.EndTime + '</span></td>\
                         <td><span style="font-size: 10px;" class="ScriptUser' + i +'">' + row.ScriptUser + '</span></td>\
                         <td><span style="font-size: 10px;" class="SessionUser' + i +'">' + row.SessionUser + '</span></td>\
                         <td><span style="font-size: 10px;" class="HostCount' + i +'">' + row.HostCount + '</span></td>\
                         </tr>';
            if (row.Status.substring(0,4) == "Busy") {
                foundBusyStatus = true;
            }
        });
        
        for (i = numrows; i < NUM_JOBS; i++) {
            tdHtml += '<tr class="Row' + i +'">\
                         <td><span style="font-size: 10px;" class="JobId' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="NodeList' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="Status' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="PID' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="Timestamp' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="Command' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="StartTime' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="EndTime' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="ScriptUser' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="SessionUser' + i +'"></span></td>\
                         <td><span style="font-size: 10px;" class="HostCount' + i +'"></span></td>\
                       </tr>';
        };

        tdHtml += "</tbody></table></div>";
        html += tdHtml;
        
        // Render table
        $(tableDiv).append(html);

        // Render the user form
        renderCommandForm();

        // Populate cmdtpyes for UI configuration from server
        PopulateCmdTypes();

        // Apply configuration for UI configuration from server
        ApplyConfigConf()

        // Check for job in progress
        if (foundBusyStatus){
            $('#command-progress-div').css("visibility", "visible");
            $("#command-submit").prop("disabled",true);
            updateJobStatusAtServer();
        }

        // Current row index in table
        var curIndex = null;

    }

     /**
         * SplunkJS Input object and methods
         * @param {object}      config      Config object holding component specific definitions
         */
    function splunkJSInput(config) {
        var config = this.config = config;

        // Save context 
        var that = this;

        // Remove component and add div back
        this.remove = function() {
            var el = "#" + this.config.parentEl;
            var splunkJsComponent = mvc.Components.get(this.config.id);

            if(splunkJsComponent) {
                splunkJsComponent.remove();
                $(el).append('<div id="' + this.config.el + '"></div>');    
            }
        }

        // Remove component from inline update form. Don't add the div back since it's dynamic
        this.updateRemove = function() {
            var el = "#" + this.config.parentEl;
            var splunkJsComponent = mvc.Components.get(this.config.id);
            
            if(splunkJsComponent) {
                splunkJsComponent.remove();
            }
        }

        // Render the component in the form
        this.renderComponent = function () {
            // Remove component if it exists
            that.remove();

            var el = "#" + this.config.el;

            // Get search manager
            var splunkJsComponentSearch = mvc.Components.get(this.config.id + "-search");

            // Check to make sure div is there before rendering
            if ($(el).length) {
                var choices = _.has(this.config, "choices") ? this.config.choices:[];    
    
                // Create search manager if it doesn't exist
                if(!splunkJsComponentSearch) {
                    this.config.searchInstance = new SearchManager({
                        id: this.config.id + "-search",
                        app: utils.getCurrentApp(),
                        search: this.config.searchString
                    });
                }

                if(this.config.type == "dropdown") {
                    this.config.instance = new DropdownView({
                        id: this.config.id,
                        managerid: _.isUndefined(this.config.searchString) ? null:this.config.id + "-search",
                        app: utils.getCurrentApp(),
                        choices: choices,
                        labelField: "label",
                        valueField: "value",
                        default: _.has(this.config, "default") ? this.config.default:null,
                        el: $(el)
                    }).render();                       
                } else {
                    this.config.instance = new MultiDropdownView({
                        id: this.config.id,
                        choices: choices,
                        managerid: _.isUndefined(this.config.searchString) ? null:this.config.id + "-search",
                        app: utils.getCurrentApp(),
                        labelField: "label",
                        valueField: "value",
                        width: 350,
                        default: _.has(this.config, "default") ? this.config.default:null,
                        el: $(el)
                    }).render();         
                }
            } else {
                setTimeout(function() {
                    that.renderComponent();
                }, 100);
            }
        }
        
        // Get values from bootstrap table
        this.getVals = function() {
            return this.config.instance.val();
        }
    }

    // Used to render create form
    function renderCommandForm() {
        var submitCommand = function submitCommand() {

            var nlData = {};
            _.each(arguments[0], function(component, i) {
                var nlKey = component.config.nlKey;
                nlData[nlKey] = _.isArray(component.getVals()) ? component.getVals().join():component.getVals();
                console.log(nlData[nlKey]);
            });

            // Verify ssh Port Open
            // Custom
            // SWFW Delete User
            // SWFW Verify configure administration Mode
            // SWFW Show Version
            // SWFW Show User Local (All)
            // SWFW Add User
            // SWFW admin Password Change
            // CPFW Show Version
            // CPFW Set User Password
            // PAFW Show System Info
            // PAFW Set Mgt User Password
            var cmdtype = '';
            var ScriptNodeList = nlData.NodeList;
            var ScriptUser = '';
            var SPassword = '';
            var Var1 = $('input[id=Var1TextInput]').val();
            var Var2 = $('input[id=Var2TextInput]').val();
            var Var3 = $('input[id=Var3TextInput]').val();
            var Var4 = $('input[id=Var4TextInput]').val();
            var PW1 = '';
            var PW2 = '';
            var PW3 = '';
            var Check1 = '';
            if ($("#Check1").prop('checked') == true) {
                Check1 = 'override';
            }
            var Drop1 = $("#Drop1").val();

            var arrayLength = ui_response.data.entry.length;
            for (var i = 0; i < arrayLength; i++) {
                if (ui_response.data.entry[i].name == $("#ScriptCommand-dropdown").val()) {
                    cmdtype = ui_response.data.entry[i].name;

                    // Validate Input
                    if(ScriptNodeList == "") {
                        return renderModal("missing-nodelist",
                                            "Missing NodeList",
                                            "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Please select a nodelist</div>",
                                            "Close")
                    }

                    if (ui_response.data.entry[i].content.ui_suser_label != undefined) {
                        ScriptUser = $('input[id=suserTextInput]').val();
                        SPassword = $('input[id=spwTextInput]').val();
                        if(ScriptUser == "") {
                            return renderModal("missing-username",
                                                "Missing Username",
                                                "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Please enter a script username</div>",
                                                "Close")
                        }
            
                    }
                    if (ui_response.data.entry[i].content.ui_spw_label != undefined) {
                        SPassword = $('input[id=spwTextInput]').val();
                        if(SPassword == ""){
                            return renderModal("missing-password",
                                                "Missing Password",
                                                "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Please enter a script password</div>",
                                                "Close")
                        }

                    }
                    if (ui_response.data.entry[i].content.ui_pw1_label != undefined) {
                        PW1 = $('input[id=PW1TextInput]').val();
                    }
                    if (ui_response.data.entry[i].content.ui_pw2_label != undefined) {
                        PW2 = $('input[id=PW2TextInput]').val();
                    }
                    if (ui_response.data.entry[i].content.ui_pw3_label != undefined) {
                        PW3 = $('input[id=PW3TextInput]').val();
                    }

                    if ((IsNotUTF8(ScriptUser)) | (IsNotUTF8(SPassword)) | (IsNotUTF8(Var1)) | (IsNotUTF8(Var2)) | (IsNotUTF8(Var3)) | (IsNotUTF8(Var4)) | (IsNotUTF8(PW1)) | (IsNotUTF8(PW2)) | (IsNotUTF8(PW3))) {
                        return renderModal("invalid-character",
                                                "Invalid Character",
                                                "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Only printable UTF8 (ASCII) characters are supported</div>",
                                                "Close")
                    }
                    if (ui_response.data.entry[i].content.ui_drop1_not_empty == '1') {
                        if (Drop1 == ""){
                            return renderModal("drop1-is-empty",
                                               "Field empty",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_drop1_not_empty_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var1_length_min != undefined) {
                        if (Var1.length < parseInt(ui_response.data.entry[i].content.ui_var1_length_min, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var1_length_min_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var2_length_min != undefined) {
                        if (Var2.length < parseInt(ui_response.data.entry[i].content.ui_var2_length_min, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var2_length_min_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var3_length_min != undefined) {
                        if (Var3.length < parseInt(ui_response.data.entry[i].content.ui_var3_length_min, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var3_length_min_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var4_length_min != undefined) {
                        if (Var4.length < parseInt(ui_response.data.entry[i].content.ui_var4_length_min, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var4_length_min_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var1_length_max != undefined) {
                        if (Var1.length > parseInt(ui_response.data.entry[i].content.ui_var1_length_max, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var1_length_max_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var2_length_max != undefined) {
                        if (Var2.length > parseInt(ui_response.data.entry[i].content.ui_var2_length_max, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var2_length_max_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var3_length_max != undefined) {
                        if (Var3.length > parseInt(ui_response.data.entry[i].content.ui_var3_length_max, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var3_length_max_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var4_length_max != undefined) {
                        if (Var4.length > parseInt(ui_response.data.entry[i].content.ui_var4_length_max, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var4_length_max_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw1_length_min != undefined) {
                        if (PW1.length < parseInt(ui_response.data.entry[i].content.ui_pw1_length_min, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw1_length_min_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw2_length_min != undefined) {
                        if (PW2.length < parseInt(ui_response.data.entry[i].content.ui_pw2_length_min, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw2_length_min_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw3_length_min != undefined) {
                        if (PW3.length < parseInt(ui_response.data.entry[i].content.ui_pw3_length_min, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw3_length_min_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw1_length_max != undefined) {
                        if (PW1.length > parseInt(ui_response.data.entry[i].content.ui_pw1_length_max, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw1_length_max_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw2_length_max != undefined) {
                        if (PW2.length > parseInt(ui_response.data.entry[i].content.ui_pw2_length_max, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw2_length_max_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw3_length_max != undefined) {
                        if (PW3.length > parseInt(ui_response.data.entry[i].content.ui_pw3_length_max, 10)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw3_length_max_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var1_invalid_characters != undefined) {
                        if (containsInvalidChars(Var1, ui_response.data.entry[i].content.ui_var1_invalid_characters)) {
                            return renderModal("invalid-character",
                                                    "Invalid Character",
                                                    "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var1_invalid_characters_msg + "</div>",
                                                    "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var2_invalid_characters != undefined) {
                        if (containsInvalidChars(Var2, ui_response.data.entry[i].content.ui_var2_invalid_characters)) {
                            return renderModal("invalid-character",
                                                    "Invalid Character",
                                                    "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var2_invalid_characters_msg + "</div>",
                                                    "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var3_invalid_characters != undefined) {
                        if (containsInvalidChars(Var3, ui_response.data.entry[i].content.ui_var3_invalid_characters)) {
                            return renderModal("invalid-character",
                                                    "Invalid Character",
                                                    "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var3_invalid_characters_msg + "</div>",
                                                    "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_var4_invalid_characters != undefined) {
                        if (containsInvalidChars(Var4, ui_response.data.entry[i].content.ui_var4_invalid_characters)) {
                            return renderModal("invalid-character",
                                                    "Invalid Character",
                                                    "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_var4_invalid_characters_msg + "</div>",
                                                    "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw1_invalid_characters != undefined) {
                        if (containsInvalidChars(PW1, ui_response.data.entry[i].content.ui_pw1_invalid_characters)) {
                            return renderModal("invalid-character",
                                                    "Invalid Character",
                                                    "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw1_invalid_characters_msg + "</div>",
                                                    "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw2_invalid_characters != undefined) {
                        if (containsInvalidChars(PW2, ui_response.data.entry[i].content.ui_pw2_invalid_characters)) {
                            return renderModal("invalid-character",
                                                    "Invalid Character",
                                                    "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw2_invalid_characters_msg + "</div>",
                                                    "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw3_invalid_characters != undefined) {
                        if (containsInvalidChars(PW3, ui_response.data.entry[i].content.ui_pw3_invalid_characters)) {
                            return renderModal("invalid-character",
                                                    "Invalid Character",
                                                    "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw3_invalid_characters_msg + "</div>",
                                                    "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw1_match_string != undefined) {
                        if (ui_response.data.entry[i].content.ui_pw1_match_string.includes(PW1)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw1_match_string_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw2_match_string != undefined) {
                        if (ui_response.data.entry[i].content.ui_pw2_match_string.includes(PW2)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw2_match_string_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_pw3_match_string != undefined) {
                        if (ui_response.data.entry[i].content.ui_pw3_match_string.includes(PW3)){
                            return renderModal("invalid-input",
                                               "Invalid Input",
                                               "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_response.data.entry[i].content.ui_pw3_match_string_msg + "</div>",
                                               "Close")
                        }
                    }
                    if (ui_response.data.entry[i].content.ui_val_equal != undefined) {
                        var val_array = ui_response.data.entry[i].content.ui_val_equal.split(/,/);
                        var arrayLength_val = val_array.length;
                        var ui_val_equal = '';
                        for (var i2 = 0; i2 < arrayLength_val; i2++) {
                            ui_val_equal = val_array[i2].split('|');

                            if (ui_val_equal[0] == 'var1=var2'){
                                if (Var1 != Var2) {
                                    return renderModal("field-equality",
                                                       "Field equality",
                                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_val_equal[1] + "</div>",
                                                       "Close")
                                }
                            }
                            if (ui_val_equal[0] == 'var1=var3'){
                                if (Var1 != Var3) {
                                    return renderModal("field-equality",
                                                       "Field equality",
                                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_val_equal[1] + "</div>",
                                                       "Close")
                                }
                            }
                            if (ui_val_equal[0] == 'var1=var4'){
                                if (Var1 != Var4) {
                                    return renderModal("field-equality",
                                                       "Field equality",
                                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_val_equal[1] + "</div>",
                                                       "Close")
                                }
                            }
                            if (ui_val_equal[0] == 'var2=var3'){
                                if (Var2 != Var3) {
                                    return renderModal("field-equality",
                                                       "Field equality",
                                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_val_equal[1] + "</div>",
                                                       "Close")
                                }
                            }
                            if (ui_val_equal[0] == 'var2=var4'){
                                if (Var2 != Var4) {
                                    return renderModal("field-equality",
                                                       "Field equality",
                                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_val_equal[1] + "</div>",
                                                       "Close")
                                }
                            }
                            if (ui_val_equal[0] == 'var3=var4'){
                                if (Var3 != Var4) {
                                    return renderModal("field-equality",
                                                       "Field equality",
                                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_val_equal[1] + "</div>",
                                                       "Close")
                                }
                            }
                            if (ui_val_equal[0] == 'pw1=pw2'){
                                if (PW1 != PW2) {
                                    return renderModal("field-equality",
                                                       "Field equality",
                                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_val_equal[1] + "</div>",
                                                       "Close")
                                }
                            }
                            if (ui_val_equal[0] == 'pw1=pw3'){
                                if (PW1 != PW3) {
                                    return renderModal("field-equality",
                                                       "Field equality",
                                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_val_equal[1] + "</div>",
                                                       "Close")
                                }
                            }
                            if (ui_val_equal[0] == 'pw2=pw3'){
                                if (PW2 != PW3) {
                                    return renderModal("field-equality",
                                                       "Field equality",
                                                       "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>" + ui_val_equal[1] + "</div>",
                                                       "Close")
                                }
                            }
                        }
                    }

                    break;
                }
            }


            if(cmdtype == "") {
                return renderModal("missing-cmdtype",
                                    "Error getting cmdtype",
                                    "<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Error getting cmdtype. Try refreshing the page.</div>",
                                    "Close")
            }

            else {

                // Display prompt for user to confirm and submit job
                if (confirmSubmit() == false) {
                    return false;
                };
    
                $('#command-progress-div').css("visibility", "visible");
                $("#command-submit").prop("disabled",true);

                // Create object to POST for command
                var ScommandData = {"cmdtype": cmdtype,
                              "var1": Var1,
                              "var2": Var2,
                              "var3": Var3,
                              "var4": Var4,
                              "pw1": PW1,
                              "pw2": PW2,
                              "pw3": PW3,
                              "check1": Check1,
                              "drop1": Drop1,
                              "suser": ScriptUser,
                              "spw": SPassword,
                              "nodelist": ScriptNodeList};

                var currentUser = Splunk.util.getConfigValue("USERNAME");
                var commandSUrl = "../../splunkd/__raw/services/cliauto";

                // Success message for final modal display
                var message = [];

                $.ajax({
                    type: "POST",
                    url: commandSUrl,
                    data: ScommandData,
                    success: function(data, textStatus, xhr) {
                        message.push("<div><i class=\"icon-check-circle\"></i> Successfully submitted command <b>" + currentUser + "</b></div>");
                    },
                    error: function(xhr, textStatus, error) {
                        message.push("<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Failed to submit command for user - <b>" + currentUser + "</b> - " + xhr.responseText + "</div>");
                    }
                })
                .done(function () {
                    
                    // Set interval to update the job status
                    populateTableRefresh();
                    IntervalId = setInterval(function () {
                        populateTableRefresh();
                    }, 5000);

                })
                .fail(function() {
                    renderModal("submit-fail",
                                "Submit Command Failed",
                                message.join('\n'),
                                "Close",
                                $('#command-progress-div').css("visibility", "hidden"),
                                $("#command-submit").prop("disabled",false)
                                )
                });
            }
        }

        var inputs = [new splunkJSInput({"id": "NodeList-dropdown",
                        "searchString": "| rest /servicesNS/-/" + utils.getCurrentApp() + "/data/lookup-table-files \
                        | search eai:appName=" + utils.getCurrentApp() + " \
                        | eval label = title, value = title | table label, value",
                        "app": utils.getCurrentApp(),
                        "el": "NodeList-dropdown",
                        "type": "dropdown",
                        "nlKey": "NodeList",
                        "default": "",
                        "parentEl": "NodeList"})
                    ];

        // Render components
        _.each(inputs, function(input, i) {
            input.renderComponent();
        });

        // Register submitCommand callback for button
        clearOnClickAndRegister('#command-submit', submitCommand, [inputs]);

        $('input[id=PW1cb]').change(
            function(){
                if ($('input[id=PW1TextInput]').prop('type') == 'password') {
                    $('input[id=PW1TextInput]').prop('type', 'text');
                }
                else {
                    $('input[id=PW1TextInput]').prop('type', 'password');
                }
        });
        $('input[id=PW2cb]').change(
            function(){
                if ($('input[id=PW2TextInput]').prop('type') == 'password') {
                    $('input[id=PW2TextInput]').prop('type', 'text');
                }
                else {
                    $('input[id=PW2TextInput]').prop('type', 'password');
                }
        });
        $('input[id=PW3cb]').change(
            function(){
                if ($('input[id=PW3TextInput]').prop('type') == 'password') {
                    $('input[id=PW3TextInput]').prop('type', 'text');
                }
                else {
                    $('input[id=PW3TextInput]').prop('type', 'password');
                }
        });

        // Verify ssh Port Open
        // Custom
        // SWFW Delete User
        // SWFW Verify configure administration Mode
        // SWFW Show Version
        // SWFW Show User Local (All)
        // SWFW Add User
        // SWFW admin Password Change
        // CPFW Show Version
        // CPFW Set User Password
        // PAFW Show System Info
        // PAFW Set Mgt User Password
        $("#ScriptCommand-dropdown").change(
            function(){
                ApplyConfigConf();
        });


    }

    // Used to update job status at server
    function updateJobStatusAtServer() {

        // Create object to POST for command
        var ScommandData = {"cmdtype": "STATUS"};

        var currentUser = Splunk.util.getConfigValue("USERNAME");
        var commandSUrl = "../../splunkd/__raw/services/cliauto";

        // Success message for final modal display
        var message = [];

        $.ajax({
            type: "POST",
            url: commandSUrl,
            data: ScommandData,
            success: function(data, textStatus, xhr) {
                message.push("<div><i class=\"icon-check-circle\"></i> Successfully submitted command <b>" + currentUser + "</b></div>");
            },
            error: function(xhr, textStatus, error) {
                message.push("<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Failed to update job status for user - <b>" + currentUser + "</b> - " + xhr.responseText + "</div>");
            }
        })
        .done(function () {
                    
            // Set interval to update the job status
            populateTableRefresh();
            IntervalId = setInterval(function () {
                populateTableRefresh();
            }, 5000);

                })
        .fail(function() {
            renderModal("update-job-status-fail",
                "Update Job Status Failed",
                message.join('\n'),
                "Close")
        });
    }

 // Kick it all off
    GetConfigCmdsConf();

});

//# sourceURL=cliauto-crud.js
