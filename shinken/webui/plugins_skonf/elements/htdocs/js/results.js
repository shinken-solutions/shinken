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



function delete_discovery_host(name) {
    var f = document.forms['form-'+name];
    $.ajax({
	url: '/newhosts/delete/'+name,
	success: function(data) {
	    console.log('Got result for'+name);
	    var r = $('#push-result-'+name);
	    r.show();
	    r.addClass('alert-success');
	    r.html('Host '+name+' was deleted');
	    $('#form-'+name).hide();
	    $('#btn-validate-'+name).hide();
	},
	error: function(data, txt) {
            console.log('Got bad result for'+name);
            var r = $('#push-result-'+name);
	    r.show();
            r.addClass('alert-error');
            r.html('Error for '+name+' :' +txt);
        },
    });
}


function delete_forever_discovery_host(name) {
    var f = document.forms['form-'+name];
    $.ajax({
	url: '/newhosts/tagunmanaged/'+name,
	success: function(data) {
	    console.log('Got result for'+name);
	    var r = $('#push-result-'+name);
	    r.show();
	    r.addClass('alert-success');
	    r.html('Host '+name+' was deleted');
	    $('#form-'+name).hide();
	    $('#btn-validate-'+name).hide();
	},
	error: function(data, txt) {
            console.log('Got bad result for'+name);
            var r = $('#push-result-'+name);
	    r.show();
            r.addClass('alert-error');
            r.html('Error for '+name+' :' +txt);
        },
    });
}



function validatehostform(name) {
    //var form = document.forms[name];//.submit();

    //alert("submit" + name);
    /**
     * This empties the log and shows the spinning indicator
     */
    var f = document.forms['form-'+name];

    var data = {'_id' : f._id.value, 'host_name' : f.host_name.value, 'use' : get_use_values(name)};
    console.log('Data?'+dump(data));

    $('#loading-'+name).show();
    $.ajax({
	url: '/newhosts/validatehost',
	type : 'POST',
	data : data,
	success: function(data) {
	    console.log('Got result for'+name);
	    var r = $('#push-result-'+name);
	    r.show();
	    r.addClass('alert-success');
	    r.html('Host '+name+' was added succesfully');
	    $('#loading-'+name).hide();
	    $('#form-'+name).hide();
	    $('#show_form-'+name).show();
	    $('#btn-validate-'+name).css({opacity : 0.5});	    
	},
	error: function(data, txt) {
            console.log('Got bad result for'+name);
            var r = $('#push-result-'+name);
	    r.show();
            r.addClass('alert-error');
            r.html('Error for '+name+' :' +txt);
	    $('#loading-'+name).hide();
        },

    });
}




/* We Hide all results and loading divs */
$(document).ready(function(){
    $('.ajax-loading').hide();
    $('.show_form').hide();
    $('.push-result').hide();
});


// We should get back our form :p
function show_form(name){
    $('#form-'+name).show();
    $('#show_form-'+name).hide();
    $('#btn-validate-'+name).css({opacity : 1});
}


function get_use_values(name){
    v = $('.use-value-input-'+name);
    r = [];
    $.each(v, function(idx, name){
        console.log('use-value?'+$(this).html()+' '+idx+' '+name);
	r.push($(this).html());
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
