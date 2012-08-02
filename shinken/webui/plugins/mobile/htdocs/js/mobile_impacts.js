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


    var first_right = $('#impact-1');
    if(first_right != null){
	first_right.css('opacity', '0.7');
    }

    // And make others nearly disapears
    for(var j=0;j<nb_impacts;j++){
	var impact = $('#impact-'+j);
	old_pos = impact.css('left').substring(0, impact.css('left').length-2);
	new_pos = 0;
	if(j == idx){
	    impact.css('opacity', '1');
	    new_pos = offset;
	}else if(j == idx-1 || j == idx+1){
	    impact.css('opacity', '0.7');
	    new_pos = ((j-idx)*250+offset);
	}else{
	    impact.css('opacity', '0.1');
	    new_pos = ((j-idx)*250+offset);
	}
	impact.animate({'left' : new_pos});
	/*var move = new Fx.Tween(impact, {property: 'left', duration : 200});
	move.start(old_pos, new_pos); // and by moving now*/

    }

}

function go_to_pos_x(pos_x){
    pos_x = -pos_x;
    var idx=3;
    alert(pos_x);
    n = (pos_x - Math.floor(pos_x)%250)/250;
    n = Math.ceil(n);
    n = Math.abs(n);
    alert('N'+n);
    focus_on(n);
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

function limit_it(v){
    v = Math.min(v, 250*nb_impacts);
    v = Math.max(v, 0);
    return v;
}

$(document).ready(function(){

    // First we make opacity low for distant
    var all_impacts = $('.impact');
    nb_impacts = all_impacts.length;

    focus_on(0);
    var currentX = 0;
    var startX = 0;
    var touchMoved = false;
    var lastMoveTime = 0;

    window.addEventListener("touchstart", function (event){
	startX = event.touches[0].pageX - currentX;
	touchMoved = false;

	event.preventDefault();
    }, false);

    window.addEventListener("touchmove", function (e){
	touchMoved = true;
	lastX = currentX;
	lastMoveTime = new Date();
	currentX = event.touches[0].pageX - startX;
	currentX = limit_it(currentX);
	e.preventDefault();
    }, false);

    window.addEventListener('touchend', function (e){
	if (touchMoved)
	{
            /* Approximate some inertia -- the transition function takes care of the decay over 0.4s for us, but we need to amplify the last movement */
            var delta = currentX - lastX;
            var dt = (new Date()) - lastMoveTime + 1;
            /* dx * 400 / dt */
	    alert('delta'+delta+'dt'+dt);
            currentX = currentX + delta * 200 / dt;
	    currentX = limit_it(currentX);
	    go_to_pos_x(currentX);
            //this.delegate.updateTouchEnd(this);
	    //alert(currentX);


	}
	else
	{
            //this.delegate.clicked(this.currentX);
	}
	alert('CurrentX'+currentx);
	e.preventDefault();
    }, false);


});
