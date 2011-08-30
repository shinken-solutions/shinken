
window.addEvent('domready', function(){
	var toggles = $$('.toggler');
	var content = $$('.element');
 
	var AccordionObject = new Accordion(toggles, content, {
		//opacity: 0,
		alwaysHide : true
		/*onActive: function(toggler) { toggler.setStyle('color', '#f30'); },
		  onBackground: function(toggler) { toggler.setStyle('color', '#000'); }*/
	    });
	
    });
