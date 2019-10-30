'use strict';

// Configuration variable
app_version_data = new Object();

require(['jquery',
        'underscore',
        '/static/app/cliauto/Modal.js',
        'splunkjs/mvc/simplexml/ready!'],

    function ($,
          _,
          Modal) {

    function anonCallback(callback=function(){}, callbackArgs=null) {
        // debugger;
        if(callbackArgs) {
            callback.apply(this, callbackArgs);
        } else {
            callback();
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

    // Render credential table and wire up context menu
    function createTable() {

        // Initialize
        var pidTableDiv = '#command-table';

        var html = '';
        html += '<p>CLIAuto version: ' + String(app_version_data.cliauto_version) + '</p>';
        html += '<p>Splunk Python version: ' + String(app_version_data.python_version) + '</p>';
        html += '<p>Splunk Python SDK version: ' + String(app_version_data.splunklib_python_version) + '</p>';
        html += '<p>pexpect version: ' + String(app_version_data.pexpect_version) + '</p>';
        html += '<p>ptyprocess version: ' + String(app_version_data.ptyprocess_version) + '</p>';
        html += '<p>Openssh client version: ' + String(app_version_data.openssh_version) + '</p>';
        html += '<p>Openssh client supported ciphers: ' + String(app_version_data.openssh_ciphers) + '</p>';
        html += '<p>CLIAuto conf ciphers (cliauto.conf->main->cipher): ' + String(app_version_data.cliauto_ciphers) + '</p>';

        // Render table
        $(pidTableDiv).append(html);



    }


    // Get version from server
    function getVersionInfo() {

        window.sessionStorage.setItem("formOpen", "false");
        document.getElementById("command-table").innerHTML = "";

        // Create object to POST for command
        var ScommandData = {"cmdtype": "get_version"};

        var currentUser = Splunk.util.getConfigValue("USERNAME");
        var commandSUrl = "../../splunkd/__raw/services/cliauto";

        // Success message for final modal display
        var message = [];

        $.ajax({
            type: "POST",
            url: commandSUrl,
            data: ScommandData,
            success: function(data, textStatus, xhr) {
                message.push("<div><i class=\"icon-check-circle\"></i> Successfully got version info <b>" + currentUser + "</b> responseText=" + xhr.responseText + "</div>");
            },
            error: function(xhr, textStatus, error) {
                message.push("<div class=\"alert alert-error\"><i class=\"icon-alert\"></i>Failed to get version info for user - <b>" + currentUser + "</b> - " + xhr.responseText + "</div>");
            }
        })
        .done(function (data, textStatus, xhr) {

            // Set interval to update the job status
            //populateTableRefresh();
            app_version_data = data
            createTable();

                })
        .fail(function() {
            renderModal("get-version-info-fail",
                "Get Version Info Failed",
                message.join('\n'),
                "Close")
        });
    }

 // Kick it all off
    //debugger;
    getVersionInfo();
});

//# sourceURL=cliauto-crud.js
