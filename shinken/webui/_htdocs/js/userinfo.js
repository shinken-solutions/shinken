window.addEvent('domready', function(){
    
	$('userinfo').setStyle('height','auto');
	var mySlide = new Fx.Slide('userinfo').hide();

	$('toggleUserinfo').addEvent('click', function(e){
		e = new Event(e);
		mySlide.toggle();
		e.stop();
	    });

	$('closeUserinfo').addEvent('click', function(e){
		e = new Event(e);
		mySlide.slideOut();
		e.stop();
	    });

    });