
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
	imgLink.src = img_src+'reduce.png';
    } else {
	toc.style.display = 'none';
	imgLink.src = img_src+'expand.png';
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
