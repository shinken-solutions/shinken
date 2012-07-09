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

/* Now a function for managingthe hovering of the problems. Will make
   appears the actiosn buttons with a smoot way (opacity)*/

$(document).ready(function(){

    /* We must avoid $$() call for IE, so call a standad way*/
    var switches = $('.switches');
    var host_services = $('.host-services');

    // We set display actions on hover
    switches.mouseenter(function(){
	$(this).animate({'opacity' : 1});
    });

    // And on leaving, hide them with opacity -> 0
    switches.mouseleave(function(){
	$(this).animate({'opacity' : 0.7});
    });

    // Now All Services
    // We set display actions on hover, but only if they are present
    if(host_services != null){
	host_services.mouseenter(function(){
	    $(this).animate({'opacity' : 1});
	});

	// And on leaving, hide them with opacity -> 0
	host_services.mouseleave(function(){
	    $(this).animate({'opacity' : 0.3});
	});
    }

});


/* When he user ask for show all impacts ro services, we display them */
function show_hidden_impacts_or_services() {

    var imp_srv_s = $('.hidden_impacts_services');

    imp_srv_s.css('display','block');
    imp_srv_s.animate({'opacity' : 1});

    /* An we can delete the button that toggle us */
    var button = $('#hidden_impacts_or_services_button');
    button.css('display', 'none');
}


/* When he user ask for show all impacts ro services, we display them */
function show_hidden_info() {

    var info_s = $('.hidden_infos');
    info_s.css('display', 'block');
    info_s.animate({'opacity' : 1});

    /* An we can delete the button that toggle us */
    var button = $('#hidden_info_button');
    button.css('display', 'none');
}




