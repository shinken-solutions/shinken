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


var _already_load = {};

// when we show a custom view tab, we lazy load it :D
function show_custom_view(p){
    var hname = p.attr('data-elt-name');
    var cvname = p.attr('data-cv-name');

    if(cvname in _already_load){
	console.log('Panel already load');
	return;
    }

    var _t = new Date().getTime();
    console.log('GOGOGO'+hname);
    $('#cv'+cvname).load('/cv/'+cvname+'/'+hname+"?_="+_t);
    _already_load[cvname] = true;
    console.log("Already load?");
    console.log(_already_load);
}

// when we show the depgraph tab, we lazy load the depgraph :p
$(window).ready(function(){
    $('.cv_pane').on('shown', function (e) {
	console.log('Show must go on!');
	show_custom_view($(this));
    })

    // And for each already active on boot, show them directly!
    $('.cv_pane.active').each(function(index, elt ) {
	show_custom_view($(elt));
    });

});
