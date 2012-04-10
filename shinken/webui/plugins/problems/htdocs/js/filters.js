


function save_hg_filter(){
    var f = document.forms['hgfilter'];
    var hg = f.hg.value;
    console.log('Trying to save preference :' + hg);
    $.post("/user/save_pref", { 'key' : 'filter_hg', 'value' : hg});
}

function clean_new_search(){
    new_filters = [];
    refresh_new_search_div();
}

function refresh_new_search_div(){
    if(new_filters.length == 0){
	$('#new_search').html('<h4>No filter selected</h4>');
	return;
    }
    
    s = '<h4>New filters</h4><ul>';
    
    $.each(new_filters, function(idx, e){
	console.log('Trying to refresh the div with'+idx+'and'+f);
	s+= '<li>'+f.long_type+': '+f.search+'</li>';
    });

    s += '</ul>';
    $('#new_search').html(s);
    
}


function add_hg_filter(name){
    f = {};
    f.type = 'hg';
    f.long_type = 'Group';
    f.search = name;
    new_filters.push(f);
    refresh_new_search_div();
}

function add_hst_srv_filter(name){
    f = {};
    f.type = 'hst_srv';
    f.long_type = 'Name';
    f.search = name;
    new_filters.push(f);
    refresh_new_search_div();
}

