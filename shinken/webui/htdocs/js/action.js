

/* ************************************* Message raise part ******************* */
function raise_message_ok(text){
    // Simplest way to use the class...
    new Message({
	    iconPath : '/static/images/',
		icon: "okMedium.png",
		title: "Success!",
		message: text
		}).say();
}


function raise_message_error(text){
    // Simplest way to use the class...
    new Message({
            iconPath : '/static/images/',
                icon: "errorMedium.png",
                title: "Error!",
                message: text
                }).tell();
}


/* React to an action return of the /action page. Look at status
 to see if it's ok or not */
function react(response){
    //alert('In react'+ response);
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
    var jsonRequest = new Request.JSON(
                                       {url: url,
                                        onSuccess: react,
                                        onFailure : manage_error,
                                       }).get();

}


/* ************************************* Commands ******************* */

/* The command that will launch an event handler */
function try_to_fix(hname) {
    
    //alert('Try to fix' + hname);
    var url = '/action/LAUNCH_HOST_EVENT_HANDLER/'+hname;
    // We can launch it :)
    launch(url);
}



/* For acknoledge, we can ask for a message first */
var ackno_element = null;
function acknoledge(hname){
    ackno_element = hname;
    var obj = new Element('div', {
	    'id': 'dummydummy',
	    'events': {
		'click': function(){
		    sendComment();
		    this.destroy();
		}
	    }
	});
    new Message({
	    icon: "questionMedium.png",
		iconPath: "/static/images/",
		width: 300,
		fontSize: 14,
		/*passEvent: e,*/
		autoDismiss: false,
		title: 'Have a Comment?' ,
		message: '<textarea id="commentText" cols="3" rows="5" class="msgEditable">Acknoledged.</textarea>',
		callback: do_acknoledge
		}).say();
}
 
function do_acknoledge(text){
    /*alert('acknoledge'+ackno_element+text);*/
    var url = '/action/ACKNOWLEDGE_HOST_PROBLEM/'+ackno_element+'/1/0/1/webui/'+text;
    launch(url);
}




/* The command that will launch an event handler */
function recheck_now(hname) {
    
    //alert('Try to fix' + hname);
    var now = Math.round(new Date().getTime()/1000.0);
    var url = '/action/SCHEDULE_HOST_CHECK/'+hname+'/'+now;
    // We can launch it :)
    launch(url);
}


/* For some commands, it's a toggle/un-toggle way */

/* We to the active AND passive in the same way, and the services
in the same time */
function toggle_checks(hname, b){
    //alert('toggle_active_checks::'+hname+b);
    // Inverse the active check or not for the element
    if(b == 'True'){ // go disable
	var url = '/action/DISABLE_HOST_CHECK/'+hname;
	launch(url);
	var url = '/action/DISABLE_PASSIVE_HOST_CHECKS/'+hname;
	launch(url);
	var url = '/action/DISABLE_HOST_SVC_CHECKS/'+hname;
	launch(url);
    }else{ // Go enable
	var url = '/action/ENABLE_HOST_CHECK/'+hname;
	launch(url);
	var url = '/action/ENABLE_PASSIVE_HOST_CHECKS/'+hname;
	launch(url);
	var url = '/action/ENABLE_HOST_SVC_CHECKS/'+hname;
	launch(url);
    }
}


function toggle_notifications(hname, b){
    //alert('toggle_active_checks::'+hname+b);
    // Inverse the active check or not for the element
    if(b == 'True'){ // go disable
        var url = '/action/DISABLE_HOST_NOTIFICATIONS/'+hname;
        launch(url);
    }else{ // Go enable
        var url = '/action/ENABLE_HOST_NOTIFICATIONS/'+hname;
        launch(url);
    }
}


function toggle_event_handlers(hname, b){
    //alert('toggle_active_checks::'+hname+b);
    // Inverse the active check or not for the element
    if(b == 'True'){ // go disable
        var url = '/action/DISABLE_HOST_EVENT_HANDLER/'+hname;
        launch(url);
    }else{ // Go enable
        var url = '/action/ENABLE_HOST_EVENT_HANDLER/'+hname;
        launch(url);
    }
}


function toggle_flap_detection(hname, b){
    //alert('toggle_active_checks::'+hname+b);
    // Inverse the active check or not for the element
    if(b == 'True'){ // go disable
        var url = '/action/DISABLE_HOST_FLAP_DETECTION/'+hname;
        launch(url);
    }else{ // Go enable
        var url = '/action/ENABLE_HOST_FLAP_DETECTION/'+hname;
        launch(url);
    }
}
