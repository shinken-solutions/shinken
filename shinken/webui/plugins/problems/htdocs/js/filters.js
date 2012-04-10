


function save_hg_filter(){
    var f = document.forms['hgfilter'];
    var hg = f.hg.value;
    console.log('Trying to save preference :' + hg);
    $.post("/user/save_pref", { 'key' : 'filter_hg', 'value' : hg});
}

