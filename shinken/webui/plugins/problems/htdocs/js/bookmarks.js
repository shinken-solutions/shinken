function add_new_bookmark(page){
    console.log('We will try to save the user bookmark');
    var f = document.forms['bookmark_save'];
    var name = f.bookmark_name.value;
    if (name==''){return;}

    console.log('Saving a bookmark with'+name);

    var uri = get_current_search(page);
    console.log('With the URI'+uri);

    var b = {'name' : name, 'uri' : uri};
// Do not save the bm if there is already one with this name
    var names =new Array();
    $.each(bookmarks, function(idx, bm){
        names.push(bm.name);
        });
    if (names.indexOf(name)==-1) {
    // Ok we can save bookmarks in our preferences
        bookmarks.push(b);
        save_bookmarks();
    }
    else { alert('This bookmark name already exists !');}

}

function save_bookmarks(){
    console.log('Need to save bookmarks list'+JSON.stringify(bookmarks));
    $.post("/user/save_pref", { 'key' : 'bookmarks', 'value' : JSON.stringify(bookmarks)});

    // And refresh it
    refresh_bookmarks();
}

function save_bookmarksro(){
    console.log('Need to save common bookmarks list'+JSON.stringify(bookmarks));
    $.post("/user/save_common_pref", { 'key' : 'bookmarks', 'value' : JSON.stringify(bookmarksro)});

    // And refresh it
    refresh_bookmarksro();
}

function push_to_common_bookmarks(name,uri) {
    console.log('Pushing a bookmark to common ones');
    var b = {'name' : name, 'uri' : uri};
// Do not save the bm if there is already one with this name
    var names =new Array();
    $.each(bookmarksro, function(idx, bm){
        names.push(bm.name);
        });
    if (names.indexOf(name)==-1) {
    // Ok we can save bookmarks in our preferences
        bookmarksro.push(b);
        save_bookmarksro();
    }
    else { alert('This Common bookmark name already exists !');}

}


function declare_bookmark(name, uri){
    console.log('declaring bookmark '+name+' at uri '+uri);
    var b = {'name' : name, 'uri' : uri};
    bookmarks.push(b);
}

function declare_bookmarksro(name, uri){
    console.log('declaring Common bookmark '+name+' at uri '+uri);
    var b = {'name' : name, 'uri' : uri};
    bookmarksro.push(b);
}

function refresh_bookmarks(){
    if(bookmarks.length == 0){
        $('#bookmarks').html('<h4>No bookmarks</h4>')
        return;
    }

    s = '<h3>Your bookmarks</h3> <ul class="unstyled">'
    $.each(bookmarks, function(idx, b){
        l = '<span><a href="'+b.uri+'"><i class="icon-tag"></i> '+b.name+'</a></span>';
        fun = "delete_bookmark('"+b.name+"');";
        c = '<span><a href="javascript:'+fun+'" class="close">&times;</a></span>';
        if (advfct == 1) {
                fun2 = "push_to_common_bookmarks('"+b.name+"','"+b.uri+"');";
                c2 = '<span><a href="javascript:'+fun2+'" class="close">&plus;</a></span>';
        }
        else { c2 =""; }

        s+= '<li>'+l+c+c2+'</li>';
    });
    $('#bookmarks').html(s);
}

function refresh_bookmarksro(){

    if(bookmarksro.length == 0){
        $('#bookmarksro').html('<h4>No common bookmarks</h4>')
        return;
    }

    sro = '<h3>Common bookmarks</h3> <ul class="unstyled">'
    $.each(bookmarksro, function(idx, b){
        l = '<span><a href="'+b.uri+'"><i class="icon-tag"></i> '+b.name+'</a></span>';
        if (advfct == 1) {
                fun = "delete_bookmarkro('"+b.name+"');";
                c = '<span><a href="javascript:'+fun+'" class="close">&times;</a></span>';
        }
        else { c =""; }
        sro+= '<li>'+l+c+'</li>';

    });
    $('#bookmarksro').html(sro);

}




// We want to delete one specific bookmark by it's name
function delete_bookmark(name){
    new_bookmarks = [];
    $.each(bookmarks, function(idx, b){
	if(b.name != name){
	    new_bookmarks.push(b);
	}
    });
    bookmarks = new_bookmarks;
    save_bookmarks();
}

function delete_bookmarkro(name){
    new_bookmarksro = [];
    $.each(bookmarksro, function(idx, b){
        if(b.name != name){
            new_bookmarksro.push(b);
        }
    });
    bookmarksro = new_bookmarksro;
    save_bookmarksro();
}


