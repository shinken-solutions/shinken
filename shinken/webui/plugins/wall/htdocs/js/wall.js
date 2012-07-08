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


function translate_problem(){
    var to_slide = $('.sliding');
    to_slide.each(function(idx){
	var pos = $(this).position();
	var new_pos = pos.left - 400;

	$(this).animate({'left':new_pos});

    });

}


function translate_impact(to_right){
    var to_slide = $('.sliding-impacts');
    //alert('Nb elements'+to_slide.length);
    to_slide.each(function(idx){
	//alert('Element'+$(this));
	var pos = $(this).position();
	var new_pos = pos;
	if(to_right){
   	    new_pos = pos.left - 400;
   	}else{
   	    new_pos = pos.left + 400;
   	}

	$(this).animate({'left':new_pos});

    });

}


function go_right(){
   translate_impact(true);
}

function go_left(){
   translate_impact(false);
}

/* And we will initialise the slide of our problems too*/
$(document).ready(function(){
    var nb_elements = $('.sliding').length;
    // If there is not enough elements, don't even slide
    // So we print in each page 9 elements. No need to slide if lower
    if(nb_elements > 9){
	var nb_slides = nb_elements / 9;
	var slide_interval = 60/nb_slides;

	slide_interval = Math.max(slide_interval, 10000);
	setInterval( translate_problem, slide_interval);//10000);
    }

});


/* And we will initialise the slide of our problems too*/
$(document).ready(function(){
    var nb_elements = $('.sliding-impacts').length;
    // If there is not enough elements, don't even slide
    // So we print in each page 6 elements. No need to slide if lower
    if(nb_elements > 6){
	var nb_slides = nb_elements / 6;
	var slide_interval = 60/nb_slides;

	slide_interval = Math.max(slide_interval, 10000);
	setInterval( go_right, slide_interval);
    }

});
