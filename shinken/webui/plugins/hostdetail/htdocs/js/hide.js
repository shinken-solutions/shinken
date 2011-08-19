/* We delare the sliding actions for the advanced ones*/

window.addEvent('domready', function(){
	var adv_actions_slide = new Fx.Slide('advanced_actions');
	adv_actions_slide.hide();
	
	$('toggle_advanced_actions').addEvent('click', function(e){
		e = new Event(e);
		adv_actions_slide.toggle();
		e.stop();
	    });
    });
