
/* We Hide all detail elements */
window.addEvent('domready', function(){
	 var details = $$('.detail');
	 details.each(function(el){
		  new Fx.Slide(el).hide();
		      });
		});

/* And if the user lick on the good image, we untoggle them. */
function show_detail(name){
    var myFx = new Fx.Slide(name).toggle();
}


/* We keep an array of all selected elements */
var selected_elements = [];


function add_remove_elements(name){
    if( selected_elements.contains(name)){
	remove_element(name);
    }else{
	add_element(name);
    }
}
	

/* function when we add an element*/
function add_element(name){
    selected_elements.push(name);
    var selector = $('selector-'+name);
    selector.src = '/static/images/tick.png';
    $('actions').fade('in');
    /* The user will ask something, so it's good to reinit
     the refresh time so he got time to launch its action,
    see reload.js for this function */
    reinit_refresh();
}

/* And or course when we remove it... */
function remove_element(name){
    selected_elements.erase(name);
    if(selected_elements.length == 0){
	$('actions').fade('out');
    }
    var selector = $('selector-'+name);
    selector.src = '/static/images/untick.png';
}


/* Flush selected elements, so clean the list
but also untick thems in the UI */
function flush_selected_elements(){
    /* We must copy the lsit so we can parse it in a clean way 
     without fearing some bugs */
    var cpy = Array.clone(selected_elements);
    cpy.each(function(name){
		 remove_element(name);
	     });
}


/* Now actions buttons : */
function recheck_now_all(){
    selected_elements.each(function(name){
			       recheck_now(name);
			   });
    flush_selected_elements();
}


/* Now actions buttons : */
function try_to_fix_all(){
    selected_elements.each(function(name){
                               try_to_fix(name);
                           });
    flush_selected_elements();
}


function acknoledge_all(){
    selected_elements.each(function(name){
			       ackno_element = name;
			       do_acknoledge('Acknoledge from WebUI.');
			   });
    flush_selected_elements();
}