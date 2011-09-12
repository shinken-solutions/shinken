

/* By default, we set the page to reload each 60s*/
var refresh_timeout = 60;

/* Each second, we check for timeout and restart page */
function check_refresh(){
    if(refresh_timeout < 0){
	location.assign(location.href);
    }
    refresh_timeout = refresh_timeout - 1;    
}


/* Someone ask us to reinit the refresh so the user will have time to
   do some thigns like ask actions or something like that */
function reinit_refresh(){
    refresh_timeout = 60;
}

/* We will check timeout each 1s*/
window.addEvent('domready', function(){
	setInterval("check_refresh();", 1000); 
    });

