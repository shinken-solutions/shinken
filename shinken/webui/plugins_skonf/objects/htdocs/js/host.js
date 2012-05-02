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


function get_use_values(name){
    v = $('.use-value-'+name);
    r = [];
    $.each(v, function(idx, name){
        console.log('use-value?'+$(this).html()+' '+idx+' '+name);
	var t = $(this).html();
	r.push(t);
    });
    //console.log(dump(r));
    console.log('Inline?'+r.join(','));
    return r.join(',')
}



// Go autofill tags
$(document).ready(function(){
    $(".to_use_complete").each(function(idx, elt){
        var raw_use = $(this).attr('data-use').split(',');
        var pop = [];
        $.each(raw_use, function(idx, v){pop.push({id:v, name : v})});
	

	/*
	  Ok, go for the huge part. We want a auto loading of the elements from /lookup/tag,
	  as a POST (query = value), we don't want duplicate objects (stupid for tag),
	  and the formater will put a good class to we can get the data back, and put a
	  picture from the sets. If not available, hide the picture :p.
	  The ref_id is an hack from original code so in the tokenFormatter we know 
	  what we are refering from...

	  ... yes, I said huge :)
	 */
	$(this).tokenInput("/lookup/tag",
			   {'theme' : 'facebook',
			    prePopulate: pop, 
			    method : 'POST', queryParam:'value', 
			    preventDuplicates: true,
			    tokenFormatter: function(item) { return "<li><img class='imgsize1' onerror=\"$(this).hide()\" src=\"/static/images/sets/"+item[this.propertyToSearch]+"/tag.png\" /> <p class='use-value-"+this.ref_id+"'>"+item[this.propertyToSearch] + "</p></li>" },ref_id : $(this).attr('id')
			    
			   });
    });
});


/* 
  Thanks to jquery UI make a sortable is just easy.
*/
$(function() {
    $( ".token-input-list-facebook" ).sortable();
    $( ".token-input-list-facebook" ).disableSelection();
});
