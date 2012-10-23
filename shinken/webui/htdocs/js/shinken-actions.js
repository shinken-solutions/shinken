/*Copyright (C) 2009-2012 :
     Gabes Jean, naparuba@gmail.com
     Gerhard Lausser, Gerhard.Lausser@consol.de
     Gregory Starck, g.starck@gmail.com
     Hartmut Goebel, h.goebel@goebel-consult.de
     Andreas Karfusehr, andreas@karfusehr.de

 This file is part of Shinken.

 Shinken is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Shinken is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with Shinken.  If not, see <http://www.gnu.org/licenses/>.
*/



/* ************************************* Message raise part ******************* */
function raise_message_ok(text){
    $.meow({
	message: text,
	icon: '/static/images/ok_medium.png'
    });
}


function raise_message_error(text){
    $.meow({
        message: text,
        icon: '/static/images/down_medium.png'
    });
}


/* React to an action return of the /action page. Look at status
 to see if it's ok or not */
function react(response){
    //alert('In react'+ response+response.status);
    //alert(response.status == 200);
    if(response.status == 200){
	raise_message_ok(response.text);
    }else{
	raise_message_error(response.text);
    }
}

function manage_error(response){
    //alert('In manage_error'+response);
    //alert(response.status);
    //alert(response.responseText);
    raise_message_error(response.responseText);
}

/* ************************************* Launch the request ******************* */
function launch(url){
    // this code will send a data object via a GET request and alert the retrieved data.
    //alert('Try to get' + url+'?callback=?');
    $.jsonp({
	"url": url+'?callback=?',
	"success": react,
	"error": manage_error
    });

}


/* ************************************* Commands ******************* */

function get_elements(name){
    var elts = name.split('/');
    var elt = {type : 'UNKNOWN',
	   namevalue : 'NOVALUE'
    };
    /* 1 element mean HOST*/
    if (elts.length == 1){
	elt.type = 'HOST';
	elt.type_long = 'HOST';
	elt.namevalue = elts[0];
	elt.nameslash = elts[0];
    }else{ // 2 means Service
	elt.type = 'SVC';
	elt.type_long = 'SERVICE';
	elt.namevalue = elts[0]+';'+elts[1];
	elt.nameslash = elts[0]+'/'+elts[1];
    }
    return elt

}

/* The command that will launch an event handler */
function try_to_fix(name) {
    var elts = get_elements(name);
    var url = '/action/LAUNCH_'+elts.type+'_EVENT_HANDLER/'+elts.namevalue;
    // We can launch it :)
    launch(url);

}




function do_acknowledge(name, text, user){
    var elts = get_elements(name);
    var url = '/action/ACKNOWLEDGE_'+elts.type+'_PROBLEM/'+elts.nameslash+'/1/0/1/'+user+'/'+text;
    launch(url);
}


function do_remove(name, text, user){
    var elts = get_elements(name);
    
    /* A Remove is in fact some several commands :
       DISABLE_SVC_CHECK
       DISABLE_PASSIVE_SVC_CHECKS
       DISABLE_SVC_NOTIFICATIONS
       DISABLE_SVC_EVENT_HANDLER
       PROCESS_SERVICE_CHECK_RESULT
     */

    disable_notifications(elts);
    disable_event_handlers(elts);
    submit_check(name, 0, text);
    // WARNING : Disable checks AFTER send the OK check, but wait for
    // the check to be consume, so wait 1s
    setTimeout(function(){disable_checks(elts);}, 5000);
}



//# SCHEDULE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
function do_schedule_downtime(name, start_time, end_time, user, comment){
    var elts = get_elements(name);
    var url = '/action/SCHEDULE_'+elts.type+'_DOWNTIME/'+elts.nameslash+'/'+start_time+'/'+end_time+'/1/0/0/'+user+'/'+comment;
    launch(url);
}

function submit_check(name, return_code, output){
    var elts = get_elements(name);
    var url = '/action/PROCESS_'+elts.type_long+'_CHECK_RESULT/'+elts.nameslash+'/'+return_code+'/'+output;
    //alert('Try to submit check' + url);
    // We can launch it :)
    launch(url);
}




/* The command that will launch an event handler */
function recheck_now(name) {
    var elts = get_elements(name);
    //alert('Try to fix' + hname);
    var now = '$NOW$';
    var url = '/action/SCHEDULE_'+elts.type+'_CHECK/'+elts.nameslash+'/'+now;
    // We can launch it :)
    launch(url);
}


/* For some commands, it's a toggle/un-toggle way */

/* We to the active AND passive in the same way, and the services
in the same time */
function toggle_checks(name, b){
    //alert('toggle_active_checks::'+hname+b);
    var elts = get_elements(name);
    // Inverse the active check or not for the element
    if(b){ // go disable
	disable_checks(elts);
    }else{ // Go enable
	enable_checks(elts);
    }
}


function enable_checks(elts){
    var url = '/action/ENABLE_'+elts.type+'_CHECK/'+elts.nameslash;
    launch(url);
    var url = '/action/ENABLE_PASSIVE_'+elts.type+'_CHECKS/'+elts.nameslash;
    launch(url);
    // Disable host services only if it's an host ;)
    if(elts.type == 'HOST'){
	var url = '/action/ENABLE_HOST_SVC_CHECKS/'+elts.nameslash;
	launch(url);
    }
}


function disable_checks(elts){
    var url = '/action/DISABLE_'+elts.type+'_CHECK/'+elts.nameslash;
    launch(url);
    var url = '/action/DISABLE_PASSIVE_'+elts.type+'_CHECKS/'+elts.nameslash;
    launch(url);
    // Disable host services only if it's an host ;)
    if(elts.type == 'HOST'){
	var url = '/action/DISABLE_HOST_SVC_CHECKS/'+elts.nameslash;
	launch(url);
    }
}



function toggle_notifications(name, b){
    var elts = get_elements(name);
    //alert('toggle_active_checks::'+hname+b);
    // Inverse the active check or not for the element
    if(b){ // go disable
	disable_notifications(elts);
    }else{ // Go enable
	enable_notifications(elts);
    }
}

function disable_notifications(elts){
    var url = '/action/DISABLE_'+elts.type+'_NOTIFICATIONS/'+elts.nameslash;
    launch(url);
}

function enable_notifications(elts){
    var url = '/action/ENABLE_'+elts.type+'_NOTIFICATIONS/'+elts.nameslash;
    launch(url);
}



function toggle_event_handlers(name, b){
    var elts = get_elements(name);
    //alert('toggle_active_checks::'+hname+b);
    // Inverse the active check or not for the element
    if(b){ // go disable
	disable_event_handlers(elts);
    }else{ // Go enable
	enable_event_handlers(elts);
    }
}

function enable_event_handlers(elts){
    var url = '/action/ENABLE_'+elts.type+'_EVENT_HANDLER/'+elts.nameslash;
    launch(url);
}

function disable_event_handlers(elts){
    var url = '/action/DISABLE_'+elts.type+'_EVENT_HANDLER/'+elts.nameslash;
    launch(url);
}

function toggle_flap_detection(name, b){
    var elts = get_elements(name);
    //alert('toggle_flap::'+name+b);
    // Inverse the active check or not for the element
    if(b){ //go disable
        var url = '/action/DISABLE_'+elts.type+'_FLAP_DETECTION/'+elts.nameslash;
        launch(url);
    }else{ // Go enable
        var url = '/action/ENABLE_'+elts.type+'_FLAP_DETECTION/'+elts.nameslash;
        launch(url);
    }
}



//ADD_SVC_COMMENT;<host_name>;<service_description>;<persistent>;<author>;<comment>
// We add a persistent comment
function add_comment(name, user, comment){
    var elts = get_elements(name);
    var url = '/action/ADD_'+elts.type+'_COMMENT/'+elts.nameslash+'/1/'+user+'/'+comment;
    // We can launch it :)
    launch(url);
}


/* The command that will launch an event handler */
function delete_comment(name, i) {
    var elts = get_elements(name);
    var url = '/action/DEL_'+elts.type+'_COMMENT/'+i;
    // We can launch it :)
    launch(url);
}


/* The command that will launch an event handler */
function delete_all_comments(name) {
    var elts = get_elements(name);
    var url = '/action/DEL_ALL_'+elts.type+'_COMMENTS/'+elts.nameslash;
    // We can launch it :)
    launch(url);
}


/* The command that will launch an event handler */
function delete_downtime(name, i) {
    var elts = get_elements(name);
    var url = '/action/DEL_'+elts.type+'_DOWNTIME/'+i;
    // We can launch it :)
    launch(url);
}


/* The command that will launch an event handler */
function delete_all_downtimes(name) {
    var elts = get_elements(name);
    var url = '/action/DEL_ALL_'+elts.type+'_DOWNTIMES/'+elts.nameslash;
    // We can launch it :)
    launch(url);
}
