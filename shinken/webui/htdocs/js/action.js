
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

/* The command that will launch an event handler */
function try_to_fix(hname) {
    
    //alert('Try to fix' + hname);
    var url = '/action/LAUNCH_HOST_EVENT_HANDLER/'+hname;
    
    // this code will send a data object via a GET request and alert the retrieved data.
    var jsonRequest = new Request.JSON(
				       {url: url,
					onSuccess: react,
					onFailure : manage_error,
				       }).get();    
}


