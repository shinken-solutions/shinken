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

function go_to(url){
    window.location = url;
}

/* We want to slide all elements (in fact the div that got all elements
   , make it opacity in 0.5 s and then go to the new page.
*/
function slide_and_go(url){
    /* We must avoid $$() call for IE, so call a standad way*/
    var a = $(document.body).getElement('#all');
    
    var toggleEffect = new Fx.Tween(a, {
	property : 'opacity',
	duration : 500/*'short'*/
    });

    toggleEffect.start(1, 0); // go show by in opacity
    var move = new Fx.Tween(a, {property: 'left', duration : 500});
    move.start(0, 200); // and by moving right
    setTimeout("go_to('"+url+"')", 500);
}    
