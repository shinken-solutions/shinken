			window.addEvents({
				'load': function(){

					/* info rotator example */
					new SlideItMoo({overallContainer: 'fullscreen_info_outer',
									elementScrolled: 'fullscreen_info_inner',
									thumbsContainer: 'fullscreen_info_items',
									itemsVisible:1,
									itemsSelector: '.info_item',
									itemWidth:'100%',
									showControls:0,
									autoSlide: 5000,
									transition: Fx.Transitions.Sine.easeIn,
									duration: 1800,
									direction:1});
				}
			});