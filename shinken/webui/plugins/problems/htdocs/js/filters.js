
function save_name_filter(){
    var f = document.forms['namefilter'];
    var name = f.name.value;
    add_hst_srv_filter(name);
    //$.post("/user/save_pref", { 'key' : 'filter_hg', 'value' : hg});
}


function save_hg_filter(){
    var f = document.forms['hgfilter'];
    var hg = f.hg.value;
    add_hg_filter(hg);
    //$.post("/user/save_pref", { 'key' : 'filter_hg', 'value' : hg});
}

function save_realm_filter(){
    var f = document.forms['realmfilter'];
    var r = f.realm.value;
    add_realm_filter(r);
    //$.post("/user/save_pref", { 'key' : 'filter_hg', 'value' : hg});
}


function clean_new_search(){
    console.log('Cleaning new search');
    new_filters = [];
    refresh_new_search_div();
}

function refresh_new_search_div(){
    if(new_filters.length == 0){
	$('#new_search').html('<h4>No filter selected</h4>');
	// Actions buttons are now useless...
	$('#remove_all_filters').animate({'opacity': 0.3});
	$('#launch_the_search').animate({'opacity': 0.3});
	return;
    }
    
    // The actions buttons are now important :)
    $('#remove_all_filters').animate({'opacity': 1});
    $('#launch_the_search').animate({'opacity': 1});
    
    s = '<h4>New filters</h4><ul>';
    
    $.each(new_filters, function(idx, f){
	console.log('Trying to refresh the div with'+idx+'and'+f);
	t = '<span>'+f.long_type+': '+f.search+'</span>';
	fun = "remove_new_filter('"+f.type+"', '"+f.search+"');";
	c = '<span class="filter_delete"><a href="javascript:'+fun+'" class="close">&times;</a></span>';
	s+= '<li>'+t+c+'</li>';
    });

    s += '</ul>';
    $('#new_search').html(s);
    console.log('We got up to'+new_filters.length);
}

function already_got_filter(type, name){
    r = false;
    $.each(new_filters, function(idx, f){
	if (f.type == type && f.search == name){
	    r = true;
	}
    });
    return r;
}

// We remove from new_filters the filter of type with name
function remove_new_filter(type, name){
    new_new_filters = [];
    $.each(new_filters, function(idx, f){
	console.log('Check for removing'+f.type+'and'+type);
	console.log('And name'+f.search+'and'+name);
	if (!(f.type == type && f.search == name)){
	    new_new_filters.push(f);
	}
    });
    console.log('New size'+new_new_filters.length);
    new_filters =  new_new_filters;
    refresh_new_search_div();
}


// Now the active version
function remove_current_filter(type, name, page){
    new_current_filters = [];
    $.each(current_filters, function(idx, f){
	console.log('Check for removing '+f.type+' and '+type);
	console.log('And name '+f.search+' and '+name);
	if (!(f.type == type && f.search == name)){
	    new_current_filters.push(f);
	}
    });
    console.log('New size'+new_current_filters.length);
    current_filters =  new_current_filters;
    //console.log('And now go to the page '+page);
    // And we directly go in the new page so
    launch_current_search(page);
}

// We kill all current filter, and go in our new page
function remove_all_current_filter(page){
    current_filters = [];
    launch_current_search(page);
}

// The _active_ versions of the add_ are for the elements
// that are ALREADY filtered in the page.
function add_active_hg_filter(name){
    f = {};
    f.type = 'hg';
    f.long_type = 'Group';
    f.search = name;
    current_filters.push(f);
    add_hg_filter(name);
}


function add_hg_filter(name){
    if(already_got_filter('hg', name)){return;}
    f = {};
    f.type = 'hg';
    f.long_type = 'Group';
    f.search = name;
    new_filters.push(f);
    refresh_new_search_div();
}


function add_active_realm_filter(name){
    f = {};
    f.type = 'realm';
    f.long_type = 'Realm';
    f.search = name;
    current_filters.push(f);
    add_realm_filter(name);
}

function add_realm_filter(name){
    if(already_got_filter('realm', name)){return;}
    f = {};
    f.type = 'realm';
    f.long_type = 'Realm';
    f.search = name;
    new_filters.push(f);
    refresh_new_search_div();
}


// The _active_ versions of the add_ are for the elements
// that are ALREADY filtered in the page.
function add_active_hst_srv_filter(name){
    f = {};
    f.type = 'hst_srv';
    f.long_type = 'Name';
    f.search = name;
    current_filters.push(f);
    // And add in the panel side
    add_hst_srv_filter(name);
}

function add_hst_srv_filter(name){
    if(already_got_filter('hst_srv', name)){return;}
    f = {};
    f.type = 'hst_srv';
    f.long_type = 'Name';
    f.search = name;
    new_filters.push(f);
    refresh_new_search_div();
}



function launch_new_search(page){
    var uri = page+'?';
    v = []
    $.each(new_filters, function(idx, f){
	if(f.type == 'hst_srv'){
	    v.push('search=' + f.search);
	}else{
	    v.push('search=' + f.type+':'+f.search);
	}
    });
    uri += v.join('&');
    console.log('Go the the new URI: '+uri);
    document.location.href = uri;
}


function get_current_search(page){
    var uri = page+'?';
    v = []
    $.each(current_filters, function(idx, f){
	if(f.type == 'hst_srv'){
	    v.push('search=' + f.search);
	}else{
	    v.push('search=' + f.type+':'+f.search);
	}
    });
    uri += v.join('&');
    return uri;
}


function launch_current_search(page){
    var uri = get_current_search(page);
    console.log('Go the the new URI: '+uri);
    document.location.href = uri;
}


