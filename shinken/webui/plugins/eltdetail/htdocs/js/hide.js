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

window.addEvent('domready', function(){
    
    /* We must avoid $$() call for IE, so call a standad way*/
    var switches = $(document.body).getElement('.switches');
    var host_services = $(document.body).getElement('.host-services');

    // We set display actions on hover
    switches.addEvent('mouseenter', function(){
	    new Fx.Tween(switches, {property: 'opacity'}).start(1);
    });

    // And on leaving, hide them with opacity -> 0
    switches.addEvent('mouseleave', function(){
	    new Fx.Tween(switches, {property: 'opacity'}).start(0.5);
    });

    // Now All Services
    // We set display actions on hover, but only if they are present
    if(host_services != null){
	host_services.addEvent('mouseenter', function(){
		new Fx.Tween(host_services, {property: 'opacity'}).start(1);
	    });

	// And on leaving, hide them with opacity -> 0
	host_services.addEvent('mouseleave', function(){
		new Fx.Tween(host_services, {property: 'opacity'}).start(0.3);
	    });
    }

});





/* The business rules toggle buttons*/
function toggleBusinessElt(e) {
    //alert('Toggle'+e);
    var toc = document.getElementById('business-parents-'+e);
    var imgLink = document.getElementById('business-parents-img-'+e);
    
    img_src = '/static/images/';

    if (toc && toc.style.display == 'none') {
	toc.style.display = 'block';
	if (imgLink != null){
	    imgLink.src = img_src+'reduce.png';
	}
    } else {
	toc.style.display = 'none';
	if (imgLink != null){
	    imgLink.src = img_src+'expand.png';
	}
    }
}



/* Important_impact_div */
window.addEvent('domready', function(){
	
	var important_banner = $('important_banner');
	if (important_banner != null){

	    var fx = new Fx.Tween(important_banner, {property: 'opacity'});
	    fx.start(0).chain(
			      //Notice that "this" refers to the calling object (in this case, the myFx object).
			      function(){ fx.start(1); },
			      function(){ fx.start(0); },
			      function(){ fx.start(1); },
			      function(){ fx.start(0); },
			      function(){ fx.start(1); },
			      function(){ fx.start(0); },
			      function(){ fx.start(1); }
			      ); //Will fade the Element out and in twice.
	}
    });




/* When he user ask for show all impacts ro services, we display them */
function show_hidden_impacts_or_services() {

    var imp_srv_s = $$('.hidden_impacts_services');
    
    imp_srv_s.each(function(el) {
	    el.style.display = 'block';
	    var fx = new Fx.Tween(el, {property: 'opacity'});
	    fx.start(1);
	});

    /* An we can delete the button that toggle us */
    var button = $('hidden_impacts_or_services_button');
    button.style.display = 'none';
}
