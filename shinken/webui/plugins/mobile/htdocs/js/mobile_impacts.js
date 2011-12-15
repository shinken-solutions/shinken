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


var offset = 100;

var nb_impacts = 0;
var current_idx = 0;


function focus_on(idx){
    

    var first_right = $('impact-1');
    if(first_right != null){
	first_right.style.opacity = '0.7';
    }

    // And make others nearly disapears
    for(var j=0;j<nb_impacts;j++){
	var impact = $('impact-'+j);
	old_pos = impact.style.left.substring(0, impact.style.left.length-2);
	new_pos = 0;
	if(j == idx){
	    impact.style.opacity = '1';
	    new_pos = offset;
	}else if(j == idx-1 || j == idx+1){
	    impact.style.opacity = '0.7';
	    new_pos = ((j-idx)*250+offset);
	}else{
	    impact.style.opacity = '0.1';
	    new_pos = ((j-idx)*250+offset);
	}
	var move = new Fx.Tween(impact, {property: 'left', duration : 200});
	move.start(old_pos, new_pos); // and by moving now

    }
    
}


function go_left(){
    if(current_idx > 0){
	current_idx -= 1;
	focus_on(current_idx);
    }
}

function go_right(){
    if(current_idx < nb_impacts-1){
	current_idx += 1;
	focus_on(current_idx);
    }
}


window.addEvent('domready', function(){

    // First we make opacity low for distant
    var all_impacts = $$('.impact');
    nb_impacts = all_impacts.length;

    focus_on(0);
});