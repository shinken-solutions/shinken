 // +------------------------------------------------------------------+
// |             ____ _               _        __  __ _  __           |
// |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
// |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
// |           | |___| | | |  __/ (__|   <    | |  | | . \            |
// |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
// |                                                                  |
// | Copyright Mathias Kettner 2010             mk@mathias-kettner.de |
// +------------------------------------------------------------------+
//
// This file is part of Check_MK.
// The official homepage is at http://mathias-kettner.de/check_mk.
//
// check_mk is free software;  you can redistribute it and/or modify it
// under the  terms of the  GNU General Public License  as published by
// the Free Software Foundation in version 2.  check_mk is  distributed
// in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
// out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
// PARTICULAR PURPOSE. See the  GNU General Public License for more de-
// ails.  You should have  received  a copy of the  GNU  General Public
// License along with GNU Make; see the file  COPYING.  If  not,  write
// to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
// Boston, MA 02110-1301 USA.






/* Add for > icons a toggle root problem panel of this impact
   and hide all previously open ones 
*/
window.addEvent('domready', function(){
    
	/* Keep a pointer to the currently open problem*/
	var old_problem = null;
	/* Keep the currently click impact */
	var old_impact = null;
	/* Keep a trace of the click show problem div*/
	var old_show_pb = null;
	/* And the id of the problem */
	var current_id = 0;
  
	/* We must avoid $$() call for IE, so call a standad way*/
	var impacts = $(document.body).getElements('.impact');

	/* We must avoid $$() call for IE, so call a standad way*/
	var problems = $(document.body).getElements('.problems-panel');
  
    
	/* Activate all problems, but in invisible from now*/
	problems.setStyle('opacity', 0);


	/* Register the toggle function for all problem links*/
	var clicks = $(document.body).getElements('.pblink');
	/* And we register our toggle function */
	clicks.addEvent('click', function(){
		var pb_nb = this.get('id');
		toggleBox(pb_nb);

	    });

	function get_impact(impacts, id){
	    for(var i = 0; i< impacts.length; i++) {
		var impact = impacts[i];
		/*alert("Look for impact"+i+impact+"\n");*/
		if (impact.get('id') == id){
		    return impact;
		}
	    }
	    return none;
	}


	/* Our main toggle function */
	function toggleBox(pb_nb){
	    // Get our current impact click element
	    impact = get_impact(impacts, pb_nb);

	    // And fidn the panel we will slide
	    el = document.getElementById("problems-"+pb_nb);
	
	    if (old_show_pb != null) {
		new Fx.Tween(old_show_pb, {property: 'opacity'}).start(0);
		old_show_pb = null;
	    }
      
	    var click_same_problem = false;
	    if (old_problem == el ) {
		click_same_problem = true;
	    }

	    var toggleEffect = new Fx.Tween(el, {
		    property : 'opacity',
		    duration :500/*'short'*/
		});

	    // If we got an open problem, close it
	    if (old_problem != null && old_problem != el){
		old_problem.setStyle('left', -450);
		old_problem.setStyle('opacity', 0);
		old_problem.setStyle('display','none');
		// And clean the active impact class too
		old_impact.removeClass("impact-active");
	    }

	    old_problem = el;
	    old_impact = impact;
	    

	    /* If it was hide, it was on the left, go right and show up
	       and reverse the >> right image */
	    if(el.getStyle('opacity') == 0){
		current_id = pb_nb;
		el.setStyle('display','block');
		toggleEffect.start(0, 1); // go show by in opacity
		new Fx.Tween(el, {property: 'left', transition: 'circ:in:out'}).start(5); // and by moving right

		// Add the active class on the current impact
		impact.addClass("impact-active");
		

		/* else it was show, go left and hide :)*/
	    } else {
		current_id = 0;
		toggleEffect.start(1, 0); // go hide by opacity
		new Fx.Tween(el, {property: 'left', transition: 'circ:in:out'}).start(-450); // go left
		
		// Add the active class on the current impact
		impact.removeClass("impact-active");

	    }
	
	}
    
    
    });




/* Now a function for managingthe hovering of the problems. Will make
   appears the actiosn buttons with a smoot way (opacity)*/

window.addEvent('domready', function(){
    
    /* We must avoid $$() call for IE, so call a standad way*/
    var problems = $(document.body).getElements('.problem');
    

    // We set display actions on hover
    problems.addEvent('mouseenter', function(){
	var pb_nb = this.get('id');
	el = document.getElementById("actions-" + pb_nb);
	new Fx.Tween(el, {property: 'opacity'}).start(1);
	
    });
    // And on leaving, hide them with opacity -> 0
    problems.addEvent('mouseleave', function(){
        var pb_nb = this.get('id');
        el = document.getElementById("actions-" + pb_nb);
	new Fx.Tween(el, {property: 'opacity'}).start(0.4);
    });


});



/* Now register for images FIXIT a fitit call*/
window.addEvent('domready', function(){
    
    /* We must avoid $$() call for IE, so call a standad way*/
    var actions_fixit = $(document.body).getElements('.action-fixit');
    

    // We set display actions on hover
    actions_fixit.addEvent('click', function(){
	var args = this.get('id');
	var reg = new RegExp("[/]+", "g");
	var tab = args.split(reg);
	var action = tab[0];
	var site = tab[1];
	var host = tab[2];
	var desc = '';
	var type = 'host' ;
	// If got 4 part, it's a service
	if (tab.length == 4){
	    desc = tab[3];
	    type = 'service';
	}
	
	//alert('got tab'+tab);
	performAction(this, action, type, site, host, desc);
    });
});


/* Now register for images an ACKNO call*/
window.addEvent('domready', function(){
    
    /* We must avoid $$() call for IE, so call a standad way*/
    var actions_ack = $(document.body).getElements('.action-ack');

    // We set display actions on hover
    actions_ack.addEvent('click', function(){
	var args = this.get('id');
	var reg = new RegExp("[/]+", "g");
	var tab = args.split(reg);
	var action = tab[0];
	var site = tab[1];
	var host = tab[2];
	var desc = '';
	var type = 'host' ;
	// If got 4 part, it's a service
	if (tab.length == 4){
	    desc = tab[3];
	    type = 'service';
	}
	
	//alert('got tab'+tab);
	performAction(this, action, type, site, host, desc);

    });
});




