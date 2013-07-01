/*Copyright (C) 2009-2011 :
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


/* By default, we set the page to reload each 60s*/
var refresh_timeout = 60;
var nb_refresh_try = 0;


function postpone_refresh(){
    // If we are not in our first try, warn the user
    if (nb_refresh_try > 0){
	$.meow({
            message: 'The UI backend is not available.',
            icon: '/static/images/errorMedium.png'
	});
    }
    nb_refresh_try += 1;
    /* Ok, we are now for a new loop of 60s before retrying... */
    reinit_refresh();
}


/* React to an action return of the /action page. Look at status
 to see if it's ok or not */
function check_gotfirstdata_result(response){
    //alert('In gotfirstdata_result'+ response+response.status);
    //alert(response.status == 200);
    if(response.status == 200 && response.text == '1'){
	// Go Refresh
        location.assign(location.href);
	reinit_refresh();
    }else{
	postpone_refresh();
    }
}


/* We will try to see if the UI is not in restating mode, and so
   don't have enough data to refresh the page as it should. (force login) */
function check_for_data(){
    // this code will send a data object via a GET request and alert the retrieved data.
    //alert('Try to get' + url+'?callback=?');
    $.jsonp({
	"url": '/gotfirstdata?callback=?',
	"success": check_gotfirstdata_result,
	"error": postpone_refresh
    });

}



/* Each second, we check for timeout and restart page */
function check_refresh(){
    if(refresh_timeout < 0){
        // We will first check ifthe backend is available or not. It's useless to refresh
	// if the backend is reloading, because it will prompt for login, when wait a little bit
	// will make the data available.
	check_for_data();
    }
    refresh_timeout = refresh_timeout - 1;
}


/* Someone ask us to reinit the refresh so the user will have time to
   do some thigns like ask actions or something like that */
function reinit_refresh(){
    refresh_timeout = 60;
    console.log('Reinitialize refresh');
}

/* We will check timeout each 1s*/
$(document).ready(function(){
    setInterval("check_refresh();", 1000);
});

