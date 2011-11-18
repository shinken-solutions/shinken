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


/* We will initialize the WALL panel with our data*/
window.addEvent('domready', function(){
    options = {'autoslide' : true};
    snowstack_init(images, options);
});


function translate_problem(){
    var to_slide = $$('.sliding');
    to_slide.each(function(el){
	var pos = el.getPosition();
	var new_pos = pos.x - 400;
	
	var myeffect  = new Fx.Elements(el);//$$('a'));

	myeffect.start({
	    '0': {
		'left': [pos.x,new_pos]
	    }
	});
	
    });

}

/* And we will initialise the slide of our problems too*/
window.addEvent('domready', function(){
    var nb_elements = $$('.sliding').length;
    // If there is not enough elements, don't even slide
    // So we print in each page 9 elements. No need to slide if lower
    if(nb_elements > 9){
	var nb_slides = nb_elements / 9;
	var slide_interval = 60/nb_slides;
	//alert('interval'+slide_interval);

	slide_interval = Math.max(slide_interval, 10000);
	setInterval( translate_problem, slide_interval);//10000);
    }

});
