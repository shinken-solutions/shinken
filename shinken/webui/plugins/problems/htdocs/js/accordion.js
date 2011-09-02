
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
	var selector = $('selector-'+name);
	selector.src = '/static/images/untick.png';
	if(selected_elements.length == 0){
	    $('actions').fade('out');
	}
    }else{
	add_element(name);
	var selector = $('selector-'+name);
	selector.src = '/static/images/tick.png';
	$('actions').fade('in');
    }
}
	

/* function when we add an element*/
function add_element(name){
    selected_elements.push(name);
}

/* And or course when we remove it... */
function remove_element(name){
    selected_elements.erase(name);
}



/* Now actions buttons : */
function recheck_now_all(){
    selected_elements.each(function(name){
			       recheck_now(name);
			   });
}


/* Now actions buttons : */
function try_to_fix_all(){
    selected_elements.each(function(name){
                               try_to_fix(name);
                           });
}


function acknoledge_all(){
    selected_elements.each(function(name){
			       ackno_element = name;
			       do_acknoledge('Acknoledge from WebUI.');
			   });
}