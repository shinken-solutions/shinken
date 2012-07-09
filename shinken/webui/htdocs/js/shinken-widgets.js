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

// We are adding a typeahead on the input
function link_elt_typeahead(id){
    $(document).ready(function(){
	$('#'+id).typeahead({
	    source: function (typeahead, query) {
		$.ajax({url: "/lookup/"+query,
	                success: function (data){
	                    typeahead.process(data)}
	               });
	    },
	    onselect: function(obj) {
	        $("ul.typeahead.dropdown-menu").find('li.active').data(obj);
	    }
	});
    });
}
