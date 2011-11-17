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


/* We want to be able to add image hovering in perfdata
   so we need the position of the mouse and make apears a div with
   the image in it */

var mouse_abs_x = 0;
var mouse_abs_y = 0;

var mouse_rel_x = 0;
var mouse_rel_y = 0;

function create_img(src, alt){
    var img = document.createElement("img");

    // If we got problem with the image, bail out the
    // print/ WARNING : BEFORE set src!
    img.onerror = function() {
	img.hide()
    };
    img.src = src;
    img.alt = alt;

    return img;
}

// First we look for the img_hover div and we add it
// the image, and we set it in the good place
function display_hover_img(src, alt){
    var img = create_img(src, alt);
    var div = $('img_hover');

    var pagesize = document.documentElement.clientWidth;
    var pagehigth = document.documentElement.clientHeight;

    // We remove the previous image in it
    div.innerHTML = '';

    // If we are too much on the left, put the image a bit
    // before so we are sure it fill on the page without
    // slide. same for hight
    var pos_x = mouse_abs_x;
    if(pagesize - pos_x < 600){
	pos_x = pagesize - 600;
    }

    // By default we are a bit lower than the mouse
    var pos_y = mouse_abs_y + 20;

    // If too low, go higher. We use the relative y position here
    if(pagehigth - mouse_rel_y < 200){
        pos_y = pos_y - 300;
    }

    // Ok, let apply our positions!
    div.style.left = pos_x +'px';
    div.style.top = pos_y +'px';
    
    // And add our image, then make the div appears
    // magically
    div.appendChild(img);
    div.fade('in');
}

// when we go out the hover item, we must hide the
// img div, and remove the image in it
function hide_hover_img(){
    var div = $('img_hover');
    div.fade('out');
}

// When we move, we save our mouse position, both
// absolute and relative
window.addEvent('domready', function(){
    document.onmousemove = function(e){
	mouse_abs_x = e.pageX;
	mouse_abs_y = e.pageY;
	
	mouse_rel_x = e.clientX;
	mouse_rel_y = e.clientY;

    };
});
