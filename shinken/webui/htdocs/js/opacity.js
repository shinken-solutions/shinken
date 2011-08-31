/* Now a function for managingthe hovering of the problems. Will make
   appears the actiosn buttons with a smoot way (opacity)*/

window.addEvent('domready', function(){

        $$('.opacity_hover').each(function(el){
		
		el.setStyle('opacity', 0.5);

                // We set display actions on hover
                el.addEvent('mouseenter', function(){
                        new Fx.Tween(el, {property: 'opacity'}).start(1);
                    });

                // And on leaving, hide them with opacity -> 0
                el.addEvent('mouseleave', function(){
                        new Fx.Tween(el, {property: 'opacity'}).start(0.5);
                    });
            });
    });
