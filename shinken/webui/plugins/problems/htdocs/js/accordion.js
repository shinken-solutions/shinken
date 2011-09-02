
window.addEvent('domready', function(){
	var toggles = $$('.toggler');
	var content = $$('.element');
	/*
	var AccordionObject = new Accordion(toggles, content, {
		// By default we wqant no item displayed
		display : -1,
		// And user can choose to hide all elements
		alwaysHide : true
		});*/
	
    });


/* We Hide all detail elements */
window.addEvent('domready', function(){
	 var details = $$('.detail');
	 details.each(function(el){
		  new Fx.Slide(el).hide();
		      });
		});
//var mySlide = new Fx.Slide('container').hide()

function show_detail(name){
    var myFx = new Fx.Slide(name).toggle();
}