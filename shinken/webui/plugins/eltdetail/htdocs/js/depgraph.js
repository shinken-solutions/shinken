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


// when we show the depgraph tab, we lazy load the depgraph :p
$(window).ready(function(){
    $('#tab_to_depgraph').on('shown', function (e) {
	console.log('Show must go on!');
	// First we get the full nmae of the object from div data
	var n = $('#inner_depgraph').attr('data-elt-name');
	// Then we load the inner depgraph page. Easy isn't it? :)
	$('#inner_depgraph').load('/inner/depgraph/'+n);
    })
});
