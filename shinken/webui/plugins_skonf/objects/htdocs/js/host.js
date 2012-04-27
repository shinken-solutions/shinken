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
