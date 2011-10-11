			window.addEvent('domready', function() {
				
				//slider variables for making things easier below
				var itemsHolder = $('dash_container');
				var myItems = $$(itemsHolder.getElements('.item'));
				
				
				//create instance of the slider, and start it up		
				var mySlider = new SL_Slider({
					slideTimer: 10000,
					orientation: 'none',      //vertical, horizontal, or none: None will create a fading in/out transition.
					fade: true,                    //if true will fade the outgoing slide - only used if orientation is != None
					isPaused: false,
					container: itemsHolder,
					items: myItems
				});
				mySlider.start();
				
							 
			});