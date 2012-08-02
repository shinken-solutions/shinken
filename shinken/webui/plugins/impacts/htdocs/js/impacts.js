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

/* Add for > icons a toggle root problem panel of this impact
   and hide all previously open ones
*/
$(document).ready(
    function(){

	/* Keep a pointer to the currently open problem*/
	var old_problem = null;
	/* Keep the currently click impact */
	var old_impact = null;
	/* Keep a trace of the click show problem div*/
	var old_show_pb = null;
	/* And the id of the problem */
	var current_id = 0;

	/* We must avoid $$() call for IE, so call a standad way*/
	var impacts = $('.impact');

	/* We must avoid $$() call for IE, so call a standad way*/
	var problems = $('.problems-panel');


	/* Activate all problems, but in invisible from now*/
	problems.css('opacity', 0);
	problems.css('visibility', '');


	/* Register the toggle function for all problem links*/
	var clicks = $('.pblink');

	/* And we register our toggle function */
	clicks.click(function(){
	    var pb_nb = $(this).attr('id');
	    toggleBox(pb_nb);

	});

	function get_impact(impacts, id){
	    for(var i = 0; i< impacts.length; i++) {
		var impact = impacts.eq(i);
		if (impact.attr('id') == id){
		    return impact;
		}
	    }
	    return null;
	}


	/* Our main toggle function */
	function toggleBox(pb_nb){
	    //alert('toggle'+pb_nb);
	    // Get our current impact click element
	    impact = get_impact(impacts, pb_nb);

	    // And fidn the panel we will slide
	    el = $('#problems-'+pb_nb);//document.getElementById("problems-"+pb_nb);

	    if (old_show_pb != null) {
		new Fx.Tween(old_show_pb, {property: 'opacity'}).start(0);
		old_show_pb = null;
	    }

	    var click_same_problem = false;
	    if (old_problem == el ) {
		click_same_problem = true;
	    }


	    // If we got an open problem, close it
	    if (old_problem != null && old_problem.attr('id') != el.attr('id')){
		old_problem.css('left', -450);
		old_problem.css('opacity', 0);
		old_problem.css('display','none');
		// And clean the active impact class too
		old_impact.removeClass("impact-active");
	    }

	    old_problem = el;
	    old_impact = impact;


	    /* If it was hide, it was on the left, go right and show up
	       and reverse the >> right image */
	    if(el.css('opacity') == 0){
		//alert("go show"+pb_nb);
		current_id = pb_nb;
		el.css('display','block');
		el.animate({opacity:1, left : '0'});

		// Add the active class on the current impact
		impact.addClass("impact-active");


		/* else it was show, go left and hide :)*/
	    } else {
		//alert("go hide"+pb_nb);
		current_id = 0;

		el.animate({left : -450, opacity:0});

		// Add the active class on the current impact
		impact.removeClass("impact-active");

	    }

	}


	// This values is filled by teh /impact page. By default ti's -1
	// and so it do not ask for a default expand. But it will ask for the first value if
	// it's an bad state
	if(impact_to_expand != -1){
	    toggleBox(impact_to_expand);
	}

    });

