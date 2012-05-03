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



function disable_host(name){
    $.ajax({
	url: '/element/q/hosts/disable/'+name,
	success: function(data) {
	    $('#btn-enabled-'+name).hide();
	    $('#btn-disabled-'+name).show();
	    
	},
	error: function(data, txt) {
            console.log('Got bad result for'+name);
        },
    });

}

function enable_host(name){
    $.ajax({
	url: '/element/q/hosts/enable/'+name,
	success: function(data) {
	    $('#btn-disabled-'+name).hide();
	    $('#btn-enabled-'+name).show();
	    
	},
	error: function(data, txt) {
            console.log('Got bad result for'+name);
        },
    });

}