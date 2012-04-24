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




function validatehostform(name) {
    //var form = document.forms[name];//.submit();

    var form = $("form-"+name);
    //alert("submit" + name);
    /**
     * This empties the log and shows the spinning indicator
     */
    var log = $("res-"+name).empty().addClass('ajax-loading');

    new Request({
        method: form.method,
        url: form.action+"toto",
        onSuccess: function(responseText, responseXML) {
            log.removeClass('ajax-loading');
            log.set('text', 'text goes here');
	    div_res = $("good-result-"+name);
	    new Fx.Slide(div_res).show();
	    div_res.highlight('#ddf');
        },
	onFailure: function(responseText, responseXML) {
            log.removeClass('ajax-loading');
            log.set('text', 'ajax finished');
	    div_res = $("bad-result-"+name);
	    new Fx.Slide(div_res).show();
	    div_res.highlight('#ddf');
        }

    }).send(form.toQueryString());
}




/* We Hide all results divs */
$(document).ready(function(){
    $('.div-result').hide();
});





function get_use_values(name){
    v = $('.use-value-input-'+name);
    r = [];
    $.each(v, function(idx, name){
        console.log('use-value?'+$(this).html()+' '+idx+' '+name);
	r.push($(this).html());
    });
    //console.log('Got the good values at last!'+r.length);
    console.log(dump(r));
    return r;
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
