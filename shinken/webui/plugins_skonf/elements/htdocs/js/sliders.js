/*Copyright (C) 2009-2012 :
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

function enable_slider(name){
    var s = $('#slider_'+name);
    var l = $('#slider_log_'+name);
    var b = $('#btn-slider_'+name);
    s.attr('data-active', 1);
    s.animate({'opacity' : 1});
    l.animate({'opacity' : 1});
    b.html('Unset');
}

function disable_slider(name){
    var s = $('#slider_'+name);
    var l = $('#slider_log_'+name);
    var b = $('#btn-slider_'+name);
    s.attr('data-active', 0);
    s.animate({'opacity' : 0.4});
    l.animate({'opacity' : 0.4});
    b.html('Set');

}


/* We will enable/disable a slider by playing with opacity*/
function toggle_slider(name){
    var s = $('#slider_'+name);
    var b = $('#btn-slider_'+name);
    console.log("Founded?"+s.length+''+s.attr('data-active'));
    
    if(s.attr('data-active') == 0){
	console.log('Enable slide');
	enable_slider(name);
    }else{
	console.log('Disable slider');
	disable_slider(name);
    }
}


$(function(){
});



$(function() {
    // Create the sliders objects
    $( ".slider" ).slider({
       value:$(this).attr('data-value'),
       min: $(this).attr('data-min'),
       max: $(this).attr('data-max'),
       step: 1,
       slide: function( event, ui ) {
           $(''+$(this).attr('data-log')).html( ui.value+$(this).attr('data-unit'));
           $(this).attr('data-value', ui.value);
	   enable_slider($(this).attr('data-prop'));
       }
    });


    // And place opacity as it should be
    $('.slider').each(function(){
	if($(this).attr('data-active') == 0){
	    disable_slider($(this).attr('data-prop'));
	}else{
	    enable_slider($(this).attr('data-prop'));	    
	}
    });


});
