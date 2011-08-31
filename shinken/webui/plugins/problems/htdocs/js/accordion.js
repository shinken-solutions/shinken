
window.addEvent('domready', function(){
	var toggles = $$('.toggler');
	var content = $$('.element');
 
	var AccordionObject = new Accordion(toggles, content, {
		// By default we wqant no item displayed
		display : -1,
		// And user can choose to hide all elements
		alwaysHide : true
	    });
	
    });
